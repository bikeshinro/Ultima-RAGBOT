from typing import List
from pydantic import BaseModel

class AnswerDTO(BaseModel):
    answer: str
    contexts: List[dict]  # retrieved chunks with text, source, score

class LoginResponseDTO(BaseModel):
    token: str
    email: str

class SignupResponseDTO(BaseModel):
    success: bool
    message: str