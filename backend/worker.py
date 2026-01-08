# backend/worker.py
import os
import sys
import shutil
import asyncio
import traceback
import psutil
from rq import SimpleWorker, get_current_job
from redis import Redis
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Import your MinIO client
from minio_client import minio_client, BUCKET_NAME

# Load Env
load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)

# --- YOUR CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY") # Ensure this matches your .env key name
if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in env.")

client = genai.Client(api_key=API_KEY)

def kill_child_processes(parent_pid):
    """Kills any subprocesses (like Manim/Latex) started by this worker."""
    try:
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            child.kill()
    except:
        pass

def convert_doc_to_latex(doc_content: str) -> str:
    """
    Step 1: Converts raw text/document content into a clean LaTeX equation file.
    """
    print("🔄 Converting document content to LaTeX...")
    prompt = """
    You are a LaTeX expert.
    Read the following educational content.
    Extract the SINGLE MAIN mathematical equation or concept.
    Output ONLY the raw LaTeX code for that equation/concept.
    Do not add markdown, do not add explanations.
    Just the LaTeX.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite", # Fast model for conversion
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"CONTENT:\n{doc_content}"),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
        )
        return response.text.strip()
    except Exception as e:
        print(f"❌ LaTeX Conversion Failed: {e}")
        raise e

def generate_manim_code(latex_content: str) -> str:
    """
    Step 2: Your specific 'Hardened Prompt' logic to generate Manim code.
    """
    print("🎨 Generating Manim code from LaTeX...")
    
    base_prompt = r"""
    YOU ARE AN EXPERT MANIM ANIMATOR.
    Your task is to generate a short educational animation that visually explains the MAIN equation from the LaTeX code I provide.
    
    OUTPUT RULES (ABSOLUTE)
    • Output ONLY raw Python code.
    • Do NOT include markdown.
    • Do NOT include explanations.
    • The code must be COMPLETE and RUNNABLE.

    CODE RULES
    • Must use Manim.
    • Must define exactly: class MathScene(Scene):
    • Must import everything needed.
    • Must use MathTex for all equations.
    • Must use RAW LaTeX strings.

    ANIMATION RULES
    • Total duration about 8-10 seconds.
    • Center the main equation.
    • Make text large, clean, and readable.
    • Use smooth animations (Write, FadeIn, Transform, Indicate).
    • Visually highlight important parts.

    CRITICAL STABILITY RULES
    • NEVER use Tex for math expressions.
    • NEVER put math like f_\theta inside Tex.
    • DO NOT use substrings_to_isolate.
    • NEVER access MathTex using numeric indices or slices.
    • NEVER highlight MathTex using indices.
    """

    for attempt in range(4): # Retry loop
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite", # Or gemma-3-27b-it
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=f"LATEX SOURCE:\n{latex_content}"),
                            types.Part.from_text(text=base_prompt)
                        ]
                    )
                ]
            )

            code = response.text.replace("```python", "").replace("```", "").strip()
            if "from manim import *" not in code:
                code = "from manim import *\n" + code
            
            # Basic validation
            if "substrings_to_isolate" in code or "equation[" in code:
                print(f"⚠️ Attempt {attempt}: Unsafe code detected, retrying...")
                continue
                
            return code
        except Exception as e:
            print(f"⚠️ Error in generation attempt {attempt}: {e}")
            
    raise Exception("Failed to generate safe Manim code after retries.")

def render_scene(job_id: str, code: str, output_dir: str):
    """
    Step 3: Renders the code using system Manim.
    """
    script_path = os.path.join(output_dir, "scene.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    print(f"🎬 Rendering Job {job_id}...")
    
    # Run Manim command
    # -pql = Preview quality (Low) - Change to -pqh for High quality
    # --media_dir = Explicit output path
    cmd = f'manim -ql --media_dir "{output_dir}" "{script_path}" MathScene'
    
    exit_code = os.system(cmd)
    
    if exit_code != 0:
        raise Exception("Manim render command failed.")

    # Locate the video file
    video_dir = os.path.join(output_dir, "videos", "scene", "480p15") # Depends on quality flags
    
    # Find the mp4 file
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".mp4"):
                return os.path.join(root, file)
                
    raise Exception("Video file not found after render.")

def process_doc_to_video_task(content: str, job_id: str):
    """
    The Main Worker Task called by the API.
    """
    print(f"🚀 Processing Job {job_id}")
    job = get_current_job()
    work_dir = f"temp_{job_id}"
    os.makedirs(work_dir, exist_ok=True)
    
    try:
        # 1. Convert Doc -> LaTeX
        latex = convert_doc_to_latex(content)
        print(f"📝 Extracted LaTeX: {latex[:50]}...")
        
        # 2. Generate Code
        code = generate_manim_code(latex)
        
        # 3. Render
        video_local_path = render_scene(job_id, code, work_dir)
        
        # 4. Upload
        minio_path = f"generated_videos/{job_id}.mp4"
        minio_client.fput_object(BUCKET_NAME, minio_path, video_local_path)
        
        print(f"✅ Job {job_id} Completed: {minio_path}")
        return {"status": "success", "minio_path": minio_path}

    except Exception as e:
        print(f"❌ Job {job_id} Failed: {e}")
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}
        
    finally:
        kill_child_processes(os.getpid())
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)

if __name__ == "__main__":
    print("👷 Manim Worker Started...")
    worker = SimpleWorker(["default"], connection=redis_conn)
    worker.work()