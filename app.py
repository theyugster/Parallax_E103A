import streamlit as st
import os
import json
from dotenv import load_dotenv

# --- UPDATED IMPORTS (Fixes the error) ---
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
# New Core Paths:
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# --- CONFIGURATION ---
load_dotenv()
GOOGLE_API_KEY = os.getenv("API_KEY") 

# Setup Page
st.set_page_config(page_title="AI Tutor", layout="wide")
st.title("🎓 Learning-Aware AI Tutor")

# --- 1. LOAD DATA (The Brain & Roadmap) ---

@st.cache_resource
def load_vector_store():
    # MUST match the model used in ingest_teacher_data.py
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    # Load the existing DB
    if not os.path.exists("./chroma_db"):
        st.error("Database not found! Please run 'ingest_teacher_data.py' first.")
        return None
        
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    return vector_store

@st.cache_data
def load_syllabus():
    if os.path.exists("syllabus.json"):
        with open("syllabus.json", "r") as f:
            return json.load(f)
    return ["General Learning"]

# Load everything
vector_store = load_vector_store()

if vector_store:
    retriever = vector_store.as_retriever(search_kwargs={"k": 3}) # Retrieve top 3 relevant chunks
else:
    retriever = None

syllabus = load_syllabus()

# --- 2. SIDEBAR (Student Profile) ---
with st.sidebar:
    st.header("👤 Student Profile")
    student_name = st.text_input("Name", "Rohan")
    student_grade = st.selectbox("Grade Level", ["5th Grade", "8th Grade", "High School", "College"])
    student_interest = st.text_input("My Interest (e.g., Football, Minecraft)", "Football")
    
    st.divider()
    st.header("🗺️ Learning Roadmap")
    # Handle case where syllabus might be empty or malformed
    if isinstance(syllabus, list) and len(syllabus) > 0:
        selected_topic = st.radio("Current Topic:", syllabus)
    else:
        st.error("Syllabus file is empty. Run ingestion script first.")
        selected_topic = "General"

# --- 3. THE CHAT LOGIC ---

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

def generate_response(question, topic):
    if not retriever:
        return "Error: Database not loaded."

    # The "Personalization" Prompt
    template = """
    You are an expert tutor.
    
    CONTEXT (FACTS FROM TEXTBOOK): 
    {context}
    
    STUDENT PROFILE:
    - Name: {name}
    - Interest: {interest}
    - Grade: {grade}
    
    INSTRUCTION: 
    Explain the concept of '{topic}' based on the student's question.
    Use analogies related to **{interest}** to make it easier.
    Keep the language suitable for **{grade}**.
    Strictly use the facts from the CONTEXT.
    
    QUESTION: {question}
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # We still use Gemini for WRITING the answer
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=GOOGLE_API_KEY, temperature=0.3)
    
    chain = (
        {"context": retriever, "question": RunnablePassthrough(), "name": lambda x: student_name, "interest": lambda x: student_interest, "grade": lambda x: student_grade, "topic": lambda x: selected_topic}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain.invoke(question)

# --- 4. USER INPUT ---
user_input = st.chat_input(f"Ask about {selected_topic}...")

if user_input:
    # Show User Message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate AI Message
    with st.chat_message("assistant"):
        with st.spinner(f"Connecting {selected_topic} to {student_interest}..."):
            response = generate_response(user_input, selected_topic)
            st.markdown(response)
            
    # Save AI Message
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- 5. START LESSON BUTTON ---
if len(st.session_state.messages) == 0:
    if st.button(f"🚀 Start Lesson on {selected_topic}"):
        initial_prompt = f"Explain the main concept of {selected_topic} to me."
        st.session_state.messages.append({"role": "user", "content": initial_prompt})
        
        with st.chat_message("assistant"): 
             with st.spinner("Preparing lesson..."):
                response = generate_response(initial_prompt, selected_topic)
                st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()