from pymongo import MongoClient, ASCENDING
from src.config import settings
from datetime import datetime

client = MongoClient(settings.MONGO_URI)

db = client[settings.MONGO_DB]

# Collections
users = db["users"]
chats = db["chats"]
messages = db["messages"]

# Indexes
users.create_index([("email", ASCENDING)], unique=True)
chats.create_index([("user_id", ASCENDING)])
messages.create_index([("chat_id", ASCENDING), ("created_at", ASCENDING)])

def create_user(email: str, password_hash: str):
    users.insert_one({
        "email": email.lower(),
        "password_hash": password_hash,
        "created_at": datetime.utcnow()
    })

def get_user(email: str):
    return users.find_one({"email": email.lower()})

def create_chat(user_id: str, title: str):
    chat = {"user_id": user_id, "title": title, "created_at": datetime.utcnow()}
    res = chats.insert_one(chat)
    return str(res.inserted_id)

def append_message(chat_id: str, role: str, content: str, sources=None):
    messages.insert_one({
        "chat_id": chat_id, "role": role, "content": content,
        "sources": sources or [], "created_at": datetime.utcnow()
    })

def get_chat_history(chat_id: str, limit: int = 50):
    return list(messages.find({"chat_id": chat_id}).sort("created_at", ASCENDING).limit(limit))


# src/db/mongo.py (add helpers)
def list_chats_for_user(user_id: str, limit: int = 50):
    return list(chats.find({"user_id": user_id}).sort("created_at", ASCENDING).limit(limit))

def get_chat(chat_id: str):
    return chats.find_one({"_id": chat_id})

def rename_chat(chat_id: str, title: str):
    from bson import ObjectId
    chats.update_one({"_id": ObjectId(chat_id)}, {"$set": {"title": title}})