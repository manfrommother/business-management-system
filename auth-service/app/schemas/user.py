from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, validator, constr
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    name: str
    company_id: Optional[int] = None
    access_level: str = 'user'

class UserCreate(UserBase):
    password: constr(min_length=8)
    password_confirm: str

    @validator('password_confirm')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Пароль не верный')
        return v
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    company_id: Optional[int] = None
    access_level: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class User(UserInDBBase):
    pass 

class UserWithAccessLevels(UserInDBBase):
    access_level: List[str] = []

class UserInDB(UserInDBBase):
    password_hash: str

class AccessLevelBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None

class AccessLevelCreate(AccessLevelBase):
    pass 

class AccessLEvelUpdate(BaseModel):
    description: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None

class AccessLevelInDBBAse(AccessLevelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class AccessLevel(AccessLevelInDBBAse):
    pass 

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    expires_at: datetime

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None

class RefreshToken(BaseModel):
    refreesh_token: str

class PasswordReset(BaseModel):
    token: str
    new_password: constr(min_length=8)
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Пароли не совпадают')
        return v
    
class RequestPasswordReset(BaseModel):
    email: EmailStr

class CompleteAccountRecovery(BaseModel):
    token: str
