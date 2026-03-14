import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "ai_assistant")
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_EXPIRES_MIN = int(os.getenv("JWT_EXPIRES_MIN", "1440"))
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "knowledge_base")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

settings = Settings()