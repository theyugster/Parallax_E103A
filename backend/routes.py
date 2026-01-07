# backend/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session  
from database import get_db         
import models
# Import updated schemas
from schemas import Token, User, UserCreate, ClassroomCreate, Classroom, DocumentResponse, VectorResponse
from auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
import random # For mock embedding generation

router = APIRouter()

# --- Auth Routes ---

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
    
    # Save role from input
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

# --- Classroom Routes ---

@router.post("/classrooms/", response_model=Classroom)
async def create_classroom(
    classroom: ClassroomCreate, 
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Only Teachers can create classrooms
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

    # Add student to classroom (Association)
    classroom.students.append(current_user)
    db.commit()
    db.refresh(classroom)
    return classroom

# --- Document & Vector Routes ---

def mock_generate_embedding(text: str) -> list[float]:
    """
    Placeholder for actual embedding logic (e.g., OpenAI, HuggingFace).
    Returns a random vector of dimension 5 for demonstration.
    """
    return [random.random() for _ in range(5)]

@router.post("/classrooms/{classroom_id}/documents", response_model=DocumentResponse)
async def upload_document_and_vectorize(
    classroom_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can upload documents")
    
    # Check if classroom exists and user owns it
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom or classroom.teacher_id != current_user.id:
        raise HTTPException(status_code=404, detail="Classroom not found or unauthorized")

    # Read and Process File
    content_bytes = await file.read()
    try:
        text_content = content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        # Fallback or error handling for non-text files
        text_content = "Binary content placeholder"

    # Generate Vector
    vector = mock_generate_embedding(text_content)

    new_doc = models.Document(
        filename=file.filename,
        content=text_content,
        embedding=vector,
        classroom_id=classroom_id
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return new_doc

@router.get("/documents/{document_id}/vector", response_model=VectorResponse)
async def get_document_vector(
    document_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Retrieve document
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {"id": document.id, "vector": document.embedding}