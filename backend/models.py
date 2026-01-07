# backend/models.py
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Table, Float, ARRAY
from sqlalchemy.orm import relationship
from database import Base
import enum

# Define Enum for Roles
class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"

# Association Table: Students <-> Classrooms
classroom_students = Table(
    'classroom_students',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('classroom_id', Integer, ForeignKey('classrooms.id'))
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    # New Role Column
    role = Column(String, default=UserRole.STUDENT.value)

    # Relationships
    classrooms_teaching = relationship("Classroom", back_populates="teacher")
    classrooms_enrolled = relationship("Classroom", secondary=classroom_students, back_populates="students")
    generated_lessons = relationship("GeneratedLesson", back_populates="student")
class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))

    teacher = relationship("User", back_populates="classrooms_teaching")
    students = relationship("User", secondary=classroom_students, back_populates="classrooms_enrolled")
    documents = relationship(
    "Document",
    back_populates="classroom",
    cascade="all, delete-orphan"
)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # File info
    filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)

    # MinIO storage info
    bucket_name = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    # example: classroom_3/documents/document_12/original.pdf

    # Ownership
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Processing status
    is_processed = Column(Boolean, default=False)

    classroom = relationship("Classroom", back_populates="documents")
class GeneratedLesson(Base):
    __tablename__ = "generated_lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    content = Column(String) 
    student_id = Column(Integer, ForeignKey("users.id"))
    
    student = relationship("User", back_populates="generated_lessons")