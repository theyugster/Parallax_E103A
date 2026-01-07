# backend/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Any
from enum import Enum

class UserRole(str, Enum):
    TEACHER = "teacher"
    STUDENT = "student"

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class UserBase(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    role: str = UserRole.STUDENT.value

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Classroom Schemas
class ClassroomBase(BaseModel):
    name: str
    description: Optional[str] = None

class ClassroomCreate(ClassroomBase):
    pass

class Classroom(ClassroomBase):
    id: int
    teacher_id: int
    students: List[User] = []
    model_config = ConfigDict(from_attributes=True)

# Document Schemas
class DocumentResponse(BaseModel):
    id: int
    filename: str
    classroom_id: int
    model_config = ConfigDict(from_attributes=True)

class VectorResponse(BaseModel):
    id: int
    vector: List[float]