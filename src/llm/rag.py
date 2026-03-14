from typing import List, Dict
from src.db.qdrant import search
from src.llm.embeddings import get_embeddings
from src.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from src.config import settings

def retrieve(question: str, embeddings, user_id: str | None = None, k: int = 3, threshold: float = 0.75):
    q_vec = embeddings.embed_texts([question])[0]
    filters = {"user_id": user_id} if user_id else None
    hits = search(collection=settings.QDRANT_COLLECTION, vector=q_vec, limit=k, filters=filters)

    contexts = []
    for h in hits:
        if h.score >= threshold:  # only accept confident matches
            payload = h.payload or {}
            contexts.append({
                "text": payload.get("text", ""),
                "source": payload.get("source", "unknown"),
                "score": h.score
            })
    return contexts

def answer(question: str, llm_provider, llm_model: str, embeddings, user_id: str | None = None, top_k: int = 3, threshold: float = 0.75, temperature: float = 0.2):
    contexts = retrieve(question, embeddings, user_id=user_id, k=top_k, threshold=threshold)
    if not contexts:
        return {"answer": "I could not find reliable information in the knowledge base for this query.", "contexts": []}

    #user_prompt = build_user_prompt(question, contexts)
    user_prompt = f"""
    Use the following context to answer the question.
    Format your response using this template:

    ### Problem Statement
    ### Possible Causes
    ### Recommended Actions
    ### Safety Notes
    ### Sources

    Question: {question}
    Context: {contexts}
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    content = llm_provider.chat(messages=messages, model=llm_model, temperature=temperature)
    return {"answer": content, "contexts": contexts}


