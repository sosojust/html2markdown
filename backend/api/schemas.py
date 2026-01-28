from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    tier: str
    created_at: datetime

    class Config:
        from_attributes = True

class ApiKeyCreate(BaseModel):
    name: Optional[str] = None

class ApiKeyRead(BaseModel):
    id: UUID
    prefix: str
    name: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class ApiKeyShow(ApiKeyRead):
    key: str # Only shown once on creation

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
