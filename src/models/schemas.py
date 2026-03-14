from typing import List, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

# --- User ---
class User(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime

# --- Chat session ---
class Chat(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: datetime

# --- Message ---
class Message(BaseModel):
    id: str
    chat_id: str
    role: str  # "user" or "assistant"
    content: str
    sources: Optional[List[str]] = []
    created_at: datetime

# --- Document metadata ---
class Document(BaseModel):
    doc_id: str
    user_id: Optional[str] = None
    source: str
    mime_type: str
    created_at: datetime
    updated_at: datetime