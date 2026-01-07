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

class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id"))

    teacher = relationship("User", back_populates="classrooms_teaching")
    students = relationship("User", secondary=classroom_students, back_populates="classrooms_enrolled")
    documents = relationship("Document", back_populates="classroom")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    content = Column(String) # Store text content
    # Store embeddings as an Array of Floats (Postgres specific)
    embedding = Column(ARRAY(Float)) 
    classroom_id = Column(Integer, ForeignKey("classrooms.id"))

    classroom = relationship("Classroom", back_populates="documents")