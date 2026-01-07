import streamlit as st
import os
import json
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# --- PAGE SETUP ---
st.set_page_config(page_title="Offline Search", layout="wide")
st.title("📂 Offline Semantic Search (No Internet Required)")
st.caption("This mode finds relevant textbook paragraphs using purely local embeddings.")

# --- 1. LOAD LOCAL DATABASE ---
@st.cache_resource
def load_vector_store():
    # This runs 100% on your laptop CPU
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    if not os.path.exists("./chroma_db"):
        st.error("❌ Database not found! You must run 'ingest_teacher_data.py' first.")
        return None
        
    # Load the database from the folder
    vector_store = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    return vector_store

vector_store = load_vector_store()

# --- 2. THE SEARCH LOGIC ---
st.divider()

# Simple Search Bar
query = st.text_input("Search the textbook:", placeholder="e.g., What is Newton's Second Law?")

if query and vector_store:
    with st.spinner("Scanning database locally..."):
        # This finds the top 4 matching chunks based on meaning, not just keywords
        # k=4 means "Give me the best 4 paragraphs"
        results = vector_store.similarity_search(query, k=4)
        
    st.success(f"Found {len(results)} relevant sections:")
    
    # Display Results
    for i, doc in enumerate(results):
        with st.expander(f"📄 Result {i+1} (Source Page: {doc.metadata.get('page', 'Unknown')})", expanded=True):
            st.markdown(f"**Content:**")
            st.info(doc.page_content)
            st.caption("--- End of Section ---")

elif not vector_store:
    st.warning("Please ingest a PDF first.")