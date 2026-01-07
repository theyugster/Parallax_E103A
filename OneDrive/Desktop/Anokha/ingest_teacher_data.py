import os
import json
import csv
import time
import re
import ast
from dotenv import load_dotenv

# Document Loading & Splitting
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings 

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("API_KEY") 

if not GOOGLE_API_KEY:
    raise ValueError("Please set your API_KEY in the .env file")

# --- DATABASE HELPERS (CSV) ---
def init_csv():
    # Check if file exists, if not create with headers
    if not os.path.exists('question_bank.csv'):
        with open('question_bank.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['book_name', 'difficulty', 'question', 'opt_a', 'opt_b', 'opt_c', 'opt_d', 'answer'])

def save_batch_to_csv(questions, book_name):
    # Determine if we need to write headers (in case file was deleted)
    file_exists = os.path.exists('question_bank.csv')
    
    with open('question_bank.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # If file didn't exist, we just created it in append mode, but it might be empty if we didn't use init_csv properly before.
        # However, init_csv is called at startup. If deleted mid-run, this handles it partially, but let's rely on init_csv.
        if not file_exists:
            writer.writerow(['book_name', 'difficulty', 'question', 'opt_a', 'opt_b', 'opt_c', 'opt_d', 'answer'])
            
        count = 0
        for q in questions:
            if 'question' in q and 'answer' in q:
                writer.writerow([
                    book_name, 
                    q.get('difficulty', 'Medium'), 
                    q['question'], 
                    q.get('opt_a', ''), 
                    q.get('opt_b', ''), 
                    q.get('opt_c', ''), 
                    q.get('opt_d', ''), 
                    q['answer']
                ])
                count += 1
    print(f"      ✅ Saved {count} questions to CSV.")

def safe_parse_json(text):
    """Robust JSON parser that handles markdown and sloppy AI output."""
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r'\[.*\]', text, re.DOTALL) # Find list block
    if match: text = match.group(0)
    try: return json.loads(text)
    except: 
        try: return ast.literal_eval(text) # Fallback for single quotes
        except: return None

# Initialize CSV
init_csv()

# 1. Load the PDF
pdf_path = "textbook.pdf" 
book_name = "textbook_v1"

if not os.path.exists(pdf_path):
    raise FileNotFoundError(f"❌ Error: Could not find '{pdf_path}'")

print(f"Loading {pdf_path}...")
loader = PyPDFLoader(pdf_path)
documents = loader.load()

# --- PART A: GENERATE SYLLABUS ---
print("Generating Syllabus...")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", 
    google_api_key=GOOGLE_API_KEY,
    temperature=0
)

# Send first 10 pages for Syllabus
toc_content = ""
for doc in documents[:10]:
    toc_content += doc.page_content + "\n"

syllabus_prompt = PromptTemplate.from_template(
    """
    You are an educational assistant. Read the textbook introduction below and extract the main chapters/topics.
    Return ONLY a valid JSON list of strings. Do not add markdown formatting.
    Example: ["Chapter 1: Force", "Chapter 2: Gravity"]
    
    TEXTBOOK CONTENT:
    {content}
    """
)

chain = syllabus_prompt | llm
try:
    syllabus_response = chain.invoke({"content": toc_content})
    syllabus_text = syllabus_response.content.strip()
    # Basic cleaning
    if "```" in syllabus_text:
        syllabus_text = syllabus_text.replace("```json", "").replace("```", "")
    
    with open("syllabus.json", "w") as f:
        f.write(syllabus_text)
    print(f"Syllabus Generated: {syllabus_text[:100]}...")
except Exception as e:
    print(f"⚠️ Syllabus generation failed ({e}). using fallback.")
    with open("syllabus.json", "w") as f: json.dump(["Chapters 1-5"], f)


# --- PART B: CREATE VECTOR DATABASE (Using Local Embeddings) ---
print("Creating Vector Database (Locally)...")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)

print("Downloading embedding model (this happens only once)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Clear old DB if exists to prevent duplicates
if os.path.exists("./chroma_db"):
    import shutil
    try: shutil.rmtree("./chroma_db") 
    except: pass 

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

print("✅ Success! Database created locally.")

# --- PART C: GENERATE QUESTIONS (Sliding Window Strategy) ---
print("\n🚀 Starting Full-Book Question Generation (Target: 50 Questions)...")
print("   (Using Sliding Window to cover all chapters)")

full_text = " ".join([d.page_content for d in documents])
total_chars = len(full_text)
segment_size = total_chars // 5 # Divide book into 5 parts

# We will generate 5 batches of 10 questions each
for i in range(5):
    # 1. Select text segment
    start = i * segment_size
    end = start + segment_size
    segment_text = full_text[start : end + 1000] # +1000 buffer
    
    # 2. Determine Difficulty Mix
    if i == 0: diff_desc = "mostly Easy"
    elif i == 4: diff_desc = "mostly Hard"
    else: diff_desc = "Medium difficulty"
    
    print(f"\n   -> Processing Part {i+1}/5 ({diff_desc})...")
    
    prompt = f"""
    Generate 10 Multiple Choice Questions based on this specific part of the book.
    DIFFICULTY FOCUS: {diff_desc}
    
    CRITICAL: Return ONLY a raw JSON list. No Markdown.
    Format:
    [
      {{
        "question": "...", 
        "opt_a": "...", "opt_b": "...", "opt_c": "...", "opt_d": "...", 
        "answer": "A", 
        "difficulty": "Medium"
      }}
    ]
    
    TEXT: {segment_text[:15000]}... (truncated)
    """
    
    try:
        response = llm.invoke(prompt).content
        data = safe_parse_json(response)
        
        if data:
            save_batch_to_csv(data, book_name)
        else:
            print("      ⚠️ AI output format error (skipping this batch).")
            
    except Exception as e:
        print(f"      ❌ API Error: {e}")
        
    # 3. Rate Limit Pause
    print("      ⏳ Cooling down (10s)...")
    time.sleep(10)

print("\n✅ Ingestion Complete! Questions ready in 'question_bank.csv'.")