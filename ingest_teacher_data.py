import os
import json
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
# NEW IMPORT: Local Embeddings
from langchain_huggingface import HuggingFaceEmbeddings 

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("API_KEY") 

if not GOOGLE_API_KEY:
    raise ValueError("Please set your API_KEY in the .env file")

# 1. Load the PDF
pdf_path = "textbook.pdf" 
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
syllabus_response = chain.invoke({"content": toc_content})
syllabus_text = syllabus_response.content.strip()

if "```" in syllabus_text:
    syllabus_text = syllabus_text.replace("```json", "").replace("```", "")

with open("syllabus.json", "w") as f:
    f.write(syllabus_text)

print(f"Syllabus Generated: {syllabus_text}")

# --- PART B: CREATE VECTOR DATABASE (Using Local Embeddings) ---
print("Creating Vector Database (Locally)...")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)

# --- THE FIX: Use Local Embeddings instead of Google API ---
print("Downloading embedding model (this happens only once)...")
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

print("✅ Success! Database created locally.")