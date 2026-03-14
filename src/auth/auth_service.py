import time, jwt
from src.db.mongo import create_user, get_user
from src.auth.password import hash_password, verify_password
from src.config import settings

def signup(email: str, password: str):
    if get_user(email):
        raise ValueError("Email already exists")
    create_user(email, hash_password(password))

def login(email: str, password: str) -> str:
    user = get_user(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid credentials")
    payload = {"sub": str(user["_id"]), "email": user["email"], "exp": int(time.time()) + 60*settings.JWT_EXPIRES_MIN}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    return token