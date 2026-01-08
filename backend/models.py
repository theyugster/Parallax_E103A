from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, Float, JSON, DateTime
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

# Define Enum for Roles
class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"

# Association Table: Students <-> Classrooms
classroom_students = Table(
    'classroom_students',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('classroom_id', Integer, ForeignKey('classrooms.id')),
    extend_existing=True  # Prevents the MetaData re-definition error
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    role = Column(String, default=UserRole.STUDENT.value)

    # Relationships
    classrooms_teaching = relationship("Classroom", back_populates="teacher")
    classrooms_enrolled = relationship("Classroom", secondary=classroom_students, back_populates="students")
    generated_lessons = relationship("GeneratedLesson", back_populates="student")
    test_results = relationship("TestResult", back_populates="student")

class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))

    teacher = relationship("User", back_populates="classrooms_teaching")
    students = relationship("User", secondary=classroom_students, back_populates="classrooms_enrolled")
    documents = relationship("Document", back_populates="classroom", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    bucket_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_processed = Column(Boolean, default=False)

    classroom = relationship("Classroom", back_populates="documents")

class GeneratedLesson(Base):
    __tablename__ = "generated_lessons"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    content = Column(String) 
    student_id = Column(Integer, ForeignKey("users.id"))
    
    student = relationship("User", back_populates="generated_lessons")

class Test(Base):
    __tablename__ = "tests"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    document_id = Column(Integer, ForeignKey("documents.id"))
    classroom_id = Column(Integer, ForeignKey("classrooms.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    questions = relationship("TestQuestion", back_populates="test", cascade="all, delete-orphan")
    results = relationship("TestResult", back_populates="test")

class TestQuestion(Base):
    __tablename__ = "test_questions"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    question_text = Column(String)
    options = Column(JSON)  # ["Option A", "Option B", ...]
    correct_answer = Column(String) # "A", "B", "C", or "D"
    difficulty = Column(String)
    points = Column(Integer)
    
    test = relationship("Test", back_populates="questions")

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Integer)
    total_questions = Column(Integer)
    percentage = Column(Float)
    predicted_level = Column(String)  # Beginner, Intermediate, Advanced
    created_at = Column(DateTime, default=datetime.utcnow)

    test = relationship("Test", back_populates="results")
    student = relationship("User", back_populates="test_results")