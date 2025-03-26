from typing import Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr, validator


class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_strenght(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать не менее 8 символов')
        return v
    
class UserUpdate(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None

    @validator('password')
    def password_strenght(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Пароль должен содержать не менее 8 символов')
        return v
    
class UserInDB(UserBase):
    id: uuid.UUID
    is_active: bool
    is_deleted: bool
    email_verified: bool
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class User(UserInDB):
    pass 

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str
    role: str
    email_verified: bool
    created_at: datetime

    class Config:
        orm_mode = True