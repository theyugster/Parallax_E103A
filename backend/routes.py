import shutil
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session  
from database import get_db         
import models
from schemas import Token, User, UserCreate, ClassroomCreate, Classroom, DocumentResponse, VectorResponse
from auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

# --- NEW IMPORTS FOR EMBEDDINGS ---
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

router = APIRouter()

# --- 1. Setup Vector Store (Matches your script) ---
# Load the model once (this downloads 'all-MiniLM-L6-v2' locally)
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize ChromaDB
vector_store = Chroma(
    collection_name="classroom_docs",
    embedding_function=embedding_model,
    persist_directory="./chroma_db"  # Saves to the same folder structure
)

# --- Auth Routes (Same as before) ---

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or Password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    user_check = db.query(models.User).filter(models.User.username == user_data.username).first()
    if user_check:
        raise HTTPException(status_code=400, detail="Username already Registered")
    
    hashed_pw = get_password_hash(user_data.password)
    new_user_entry = models.User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_pw,
        role=user_data.role, 
        disabled=False
    )
    db.add(new_user_entry)
    db.commit()
    db.refresh(new_user_entry)
    return new_user_entry

@router.get("/users/me/", response_model=User)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user    

# --- Classroom Routes (Same as before) ---

@router.post("/classrooms/", response_model=Classroom)
async def create_classroom(
    classroom: ClassroomCreate, 
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create classrooms")

    new_classroom = models.Classroom(
        name=classroom.name,
        description=classroom.description,
        teacher_id=current_user.id
    )
    db.add(new_classroom)
    db.commit()
    db.refresh(new_classroom)
    return new_classroom

@router.post("/classrooms/{classroom_id}/join", response_model=Classroom)
async def join_classroom(
    classroom_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Only students can join classrooms")
        
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    classroom.students.append(current_user)
    db.commit()
    db.refresh(classroom)
    return classroom

# --- Document & Vector Routes (UPDATED) ---

@router.post("/classrooms/{classroom_id}/documents", response_model=DocumentResponse)
async def upload_document_and_vectorize(
    classroom_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Uploads a file, splits it into chunks (like the script), 
    generates embeddings using HuggingFace, and stores them in ChromaDB.
    """
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can upload documents")
    
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom or classroom.teacher_id != current_user.id:
        raise HTTPException(status_code=404, detail="Classroom not found or unauthorized")

    # 1. Save File Temporarily (LangChain loaders need a file path)
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. Load the Document
        documents = []
        if temp_filename.endswith(".pdf"):
            loader = PyPDFLoader(temp_filename)
            documents = loader.load()
        else:
            # Simple text loader fallback
            loader = TextLoader(temp_filename, encoding='utf-8')
            documents = loader.load()

        # 3. Create Database Record (Postgres)
        # We store a short snippet or just a placeholder in Postgres
        new_doc = models.Document(
            filename=file.filename,
            content=f"Processed {len(documents)} pages.", 
            classroom_id=classroom_id
        )
        db.add(new_doc)
        db.commit()
        db.refresh(new_doc)

        # 4. Split Text (Chunks)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)

        # 5. Add Metadata to Chunks (Link to Postgres ID)
        for chunk in chunks:
            chunk.metadata["document_id"] = new_doc.id
            chunk.metadata["classroom_id"] = classroom_id
            chunk.metadata["filename"] = file.filename

        # 6. Store in ChromaDB
        # This uses the 'all-MiniLM-L6-v2' model defined globally
        vector_store.add_documents(chunks)
        
        return new_doc

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        # 7. Cleanup Temp File
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@router.get("/documents/{document_id}/vector")
async def get_document_vectors_status(
    document_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Since a document is now split into multiple chunks, we can't return 
    a single vector. Instead, we query Chroma to confirm chunks exist.
    """
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Query Chroma for chunks belonging to this document_id
    # Note: Chroma query syntax depends on the version, but using 'where' metadata filter is standard
    results = vector_store.get(where={"document_id": document_id})
    
    count = len(results['ids'])
    
    return {
        "document_id": document.id,
        "chunk_count": count,
        "message": "Vectors are stored in ChromaDB and ready for RAG retrieval."
    }