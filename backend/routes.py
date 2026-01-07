import shutil
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session  
from database import get_db         
import models
from schemas import Token, User, UserCreate, ClassroomCreate, Classroom, DocumentResponse, VectorResponse
from schemas import PersonalizeRequest
from auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user, 
    get_password_hash, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from minio_client import minio_client, BUCKET_NAME
from typing import List

# --- NEW IMPORTS FOR EMBEDDINGS ---
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from schemas import ChatRequest, GeneratedLessonResponse
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
def upload_document_and_vectorize(
    classroom_id: int,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1️⃣ Authorization
    if current_user.role != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can upload")

    classroom = db.query(models.Classroom).filter_by(
        id=classroom_id,
        teacher_id=current_user.id
    ).first()

    if not classroom:
        raise HTTPException(status_code=404, detail="Unauthorized")

    # 2️⃣ Create DB record FIRST
    doc = models.Document(
        filename=file.filename,
        mime_type=file.content_type,
        file_size=0,
        bucket_name=BUCKET_NAME,
        storage_path="",  # fill later
        classroom_id=classroom_id,
        uploaded_by=current_user.id
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 3️⃣ Upload file to MinIO
    object_path = (
        f"classroom_{classroom_id}/documents/"
        f"document_{doc.id}/original_{file.filename}"
    )

    minio_client.put_object(
        bucket_name=BUCKET_NAME,
        object_name=object_path,
        data=file.file,
        length=-1,
        part_size=10 * 1024 * 1024
    )

    # 4️⃣ Save MinIO path in DB
    doc.storage_path = object_path
    db.commit()

    # 5️⃣ Download from MinIO temporarily for embedding
    temp_filename = f"temp_{doc.id}_{file.filename}"

    with open(temp_filename, "wb") as temp_file:
        response = minio_client.get_object(BUCKET_NAME, object_path)
        for chunk in response.stream(32 * 1024):
            temp_file.write(chunk)

    try:
        # 6️⃣ Load document
        if file.filename.endswith(".pdf"):
            loader = PyPDFLoader(temp_filename)
        else:
            loader = TextLoader(temp_filename, encoding="utf-8")

        documents = loader.load()

        # 7️⃣ Split into chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(documents)

        # 8️⃣ Add metadata
        for chunk in chunks:
            chunk.metadata = {
                "document_id": doc.id,
                "classroom_id": classroom_id,
                "filename": file.filename
            }

        # 9️⃣ Store in ChromaDB
        vector_store.add_documents(chunks)

        doc.is_processed = True
        db.commit()

        return doc

    finally:
        # 🔟 Cleanup temp file
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
@router.post("/chat/generate_lesson", response_model=GeneratedLessonResponse)
async def generate_and_store_lesson(
    request: ChatRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # ... (API Key check and LLM setup remain the same) ...
    google_api_key = os.getenv("AI_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=google_api_key,
        temperature=0.4
    )

    # --- THE FIX: ADD SEARCH KWARGS WITH FILTER ---
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 4,
            "filter": {"classroom_id": request.classroom_id}  # <--- This enforces the scope
        }
    )
    
    # ... (The rest of the Prompt and Chain code remains exactly the same) ...
    
    template = """
    You are an expert teacher creating a personalized lesson plan.
    
    Student Details:
    - Name: {name}
    - Grade Level: {grade}
    - Personal Interest/Hobby: {interest}
    
    The Lesson Topic is: {topic}
    
    Use the following educational content (Context) to answer the student's question. 
    Explain the concept using analogies related to their interest ({interest}) to make it engaging.
    
    Context:
    {context}
    
    Student's Question:
    {question}
    
    Answer:
    """
    
    prompt = ChatPromptTemplate.from_template(template)

    # The rest of your chain code is correct:
    chain = (
        {
            "context": retriever, 
            "question": RunnablePassthrough(), 
            "name": lambda x: request.student_name, 
            "interest": lambda x: request.student_interest, 
            "grade": lambda x: request.student_grade, 
            "topic": lambda x: request.topic
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    try:
        # Check if the user is actually IN this classroom (Security Check)
        # (Optional but recommended)
        student_in_class = db.query(models.classroom_students).filter_by(
            user_id=current_user.id, 
            classroom_id=request.classroom_id
        ).first()
        
        if not student_in_class:
             raise HTTPException(status_code=403, detail="You are not enrolled in this classroom.")

        generated_content = chain.invoke(request.question)
        
        new_lesson = models.GeneratedLesson(
            topic=request.topic,
            content=generated_content,
            student_id=current_user.id
        )
        
        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)
        
        return new_lesson

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
@router.get("/chat/lessons", response_model=List[GeneratedLessonResponse])
async def get_student_lessons(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve history of generated lessons for the current user."""
    return db.query(models.GeneratedLesson).filter(
        models.GeneratedLesson.student_id == current_user.id
    ).all()

@router.get("/chat/lessons/{lesson_id}", response_model=GeneratedLessonResponse)
async def get_lesson_detail(
    lesson_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Retrieve a specific lesson."""
    lesson = db.query(models.GeneratedLesson).filter(
        models.GeneratedLesson.id == lesson_id,
        models.GeneratedLesson.student_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

# ==========================================
#      DOCUMENT DOWNLOAD ROUTES
# ==========================================

@router.get("/documents/{document_id}/download")
async def download_original_document(
    document_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Downloads the original file from MinIO.
    """
    # 1. Get Document Info
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Check Permissions (Optional: Check if user is in the classroom)
    # For now, we assume if they are logged in, they can access (expand logic as needed)
    
    # 3. Stream from MinIO
    try:
        response = minio_client.get_object(document.bucket_name, document.storage_path)
        
        return StreamingResponse(
            response.stream(32 * 1024),
            media_type=document.mime_type or "application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{document.filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File retrieval error: {str(e)}")
@router.post("/documents/{document_id}/personalize", response_model=GeneratedLessonResponse)
async def personalize_entire_document(
    document_id: int,
    request: PersonalizeRequest,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1. Verify Document Access
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # (Optional: Check if student is in the classroom of this doc)
    # ...

    # 2. Retrieve ALL chunks for this document from Chroma
    # We filter by metadata "document_id" which we saved during upload
    results = vector_store.get(
        where={"document_id": document_id},
        include=["documents"]  # We only need the text content
    )

    doc_texts = results.get("documents", [])
    
    if not doc_texts:
        raise HTTPException(status_code=404, detail="No processed text found for this document")

    # 3. Combine chunks into one large string
    # Note: Depending on doc size, this might be large. 
    # Gemini 1.5/2.5 Flash has a huge context window, so this usually works fine for standard chapters/PDFs.
    full_text = "\n\n".join(doc_texts)

    # 4. Setup LLM
    google_api_key = os.getenv("AI_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite", # Ensure you use a model with large context
        google_api_key=google_api_key,
        temperature=0.5
    )

    # 5. Create the "Rewrite" Prompt
    template = """
    You are an expert educational content creator.
    
    Goal: Rewrite the following entire educational text to make it personalized for a student.
    
    Student Profile:
    - Name: {name}
    - Grade: {grade}
    - Interest: {interest}
    
    Instructions:
    1. Read the provided text below.
    2. Rewrite the content to match the student's reading level ({grade}).
    3. Explain the core concepts using analogies, metaphors, and examples related to their interest: "{interest}".
    4. Maintain the original educational facts but change the tone and delivery style.
    
    Original Text:
    {full_text}
    
    Personalized Version:
    """

    prompt = ChatPromptTemplate.from_template(template)

    # 6. Execute Chain
    chain = prompt | llm | StrOutputParser()

    try:
        generated_content = chain.invoke({
            "name": request.student_name,
            "grade": request.student_grade,
            "interest": request.student_interest,
            "full_text": full_text
        })

        # 7. Save and Return
        new_lesson = models.GeneratedLesson(
            topic=f"Full Rewrite: {doc.filename}",
            content=generated_content,
            student_id=current_user.id
        )
        
        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)
        
        return new_lesson

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Personalization failed: {str(e)}")
@router.get("/classrooms/me", response_model=List[Classroom])
async def get_my_classrooms(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Fetch all classrooms where the current user is the teacher
    classrooms = db.query(models.Classroom).filter(
        models.Classroom.teacher_id == current_user.id
    ).all()
    return classrooms
@router.get("/classrooms/enrolled", response_model=List[Classroom])
async def get_enrolled_classrooms(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # SQLAlchemy magic: fetch classrooms linked to this student
    return current_user.classrooms_enrolled

@router.get("/classrooms/{classroom_id}/documents", response_model=List[DocumentResponse])
async def get_classroom_documents(
    classroom_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # 1. Check if classroom exists
    classroom = db.query(models.Classroom).filter(models.Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
        
    # 2. Security: Ensure student is actually in this class (or is the teacher)
    if current_user not in classroom.students and current_user.id != classroom.teacher_id:
        raise HTTPException(status_code=403, detail="Not a member of this classroom")
        
    return classroom.documents
@router.get("/classrooms/available", response_model=List[Classroom])
async def get_available_classrooms(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Fetch all classrooms
    all_classrooms = db.query(models.Classroom).all()
    
    # Filter out classrooms the user is already enrolled in
    # (using the classrooms_enrolled relationship from models.py)
    enrolled_ids = {c.id for c in current_user.classrooms_enrolled}
    
    return [c for c in all_classrooms if c.id not in enrolled_ids]