import os
import sys
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# --- CONFIGURATION ---
load_dotenv()
api_key = os.getenv("AI_API_KEY")

if not api_key:
    raise ValueError("Missing API_KEY in .env file")

client = genai.Client(api_key=api_key)

# --- FILE PATH ---
tex_filename = "method.tex"
script_dir = os.path.dirname(os.path.abspath(__file__))
tex_path = os.path.join(script_dir, tex_filename)

if not os.path.exists(tex_path):
    print(f"❌ Error: Could not find '{tex_filename}' in {script_dir}")
    sys.exit(1)

# --- HELPER: RENDER MANIM ---
def render_manim_code(code_str):
    filename = "ai_scene.py"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code_str)

    print("   💾 Python script saved as ai_scene.py")
    print("   🎬 Rendering video...")

    command = f'"{sys.executable}" -m manim -pql ai_scene.py MathScene'
    exit_code = os.system(command)

    if exit_code == 0:
        video_path = os.path.join("media", "videos", "ai_scene", "480p15", "MathScene.mp4")
        print("\n✅ SUCCESS! Video rendered.")

        try:
            if os.path.exists(video_path):
                os.startfile(os.path.abspath(video_path))
        except:
            pass
    else:
        print("\n❌ Manim render failed. Check LaTeX or Manim output.")

# --- READ LATEX ---
print(f"🚀 Reading LaTeX file: {tex_filename}")

with open(tex_path, "r", encoding="utf-8") as f:
    latex_content = f.read()

# --- FINAL HARDENED PROMPT ---
base_prompt = r"""
YOU ARE AN EXPERT MANIM ANIMATOR.

Your task is to generate a short educational animation that visually explains the MAIN equation from the LaTeX code I provide.

Follow every rule exactly.

━━━━━━━━━━━━━━━━━━━━

TASK

1. Read the LaTeX.
2. Extract the single most important equation.
3. Create a visual Manim animation that explains that equation.

━━━━━━━━━━━━━━━━━━━━

OUTPUT RULES (ABSOLUTE)

• Output ONLY raw Python code.
• Do NOT include markdown.
• Do NOT include explanations.
• The code must be COMPLETE and RUNNABLE.

━━━━━━━━━━━━━━━━━━━━

CODE RULES

• Must use Manim.
• Must define exactly:

class MathScene(Scene):

• Must import everything needed.
• Must use MathTex for all equations.
• Must use RAW LaTeX strings.

━━━━━━━━━━━━━━━━━━━━

ANIMATION RULES

• Total duration about 8–10 seconds.
• Center the main equation.
• Make text large, clean, and readable.
• Use smooth animations (Write, FadeIn, Transform, Indicate).
• Visually highlight important parts.
• End with the full equation clearly shown.

━━━━━━━━━━━━━━━━━━━━

CRITICAL STABILITY RULES

• NEVER use Tex for math expressions.
• NEVER put math like f_\theta inside Tex.
• DO NOT use substrings_to_isolate.
• NEVER access MathTex using numeric indices or slices.
• NEVER highlight MathTex using indices.
• Highlight ONLY using tex_to_color_map or separate MathTex objects.
• If coloring symbols, ONLY use tex_to_color_map.

━━━━━━━━━━━━━━━━━━━━

FINAL RULE

If your output contains anything except valid Python code, it is WRONG.
If you use equation[...] anywhere, it is WRONG.
"""

# --- CALL MODEL WITH SELF-CORRECTION ---
print("🤖 Requesting animation code from model...")

max_retries = 6
last_code = ""

for attempt in range(max_retries):
    try:
        feedback = ""
        if attempt > 0:
            feedback = "\n\nPREVIOUS OUTPUT WAS INVALID. Fix ALL rule violations."

        response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"LATEX SOURCE:\n{latex_content}"),
                        types.Part.from_text(text=base_prompt + feedback)
                    ]
                )
            ]
        )

        code = response.text.replace("```python", "").replace("```", "").strip()
        last_code = code

        if "from manim import *" not in code:
            code = "from manim import *\n" + code

        # --- AUTO SAFETY FILTER ---
        forbidden = [
            "equation[",
            "substrings_to_isolate",
            "Tex(r\"f_",
            "Tex(r'f_",
            "Tex(\"f_",
            "Tex('f_"
        ]

        # if any(bad in code for bad in forbidden):
        #     print("⚠️ Unsafe Manim code detected. Regenerating...\n")
        #     print("------ MODEL OUTPUT PREVIEW ------")
        #     print(code[:1200])
        #     print("------ END PREVIEW ------\n")
        #     time.sleep(2)
        #     continue

        print("   📝 Safe code generated. Rendering...")
        render_manim_code(code)
        break

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(2)

else:
    print("❌ Model failed to produce safe Manim code.")
    print("👉 Last attempt saved to unsafe_ai_scene.py")

    with open("unsafe_ai_scene.py", "w", encoding="utf-8") as f:
        f.write(last_code)