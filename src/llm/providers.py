# src/llm/providers.py
import os
from src.config import settings

class LLMProvider:
    def chat(self, messages: list[dict], model: str, temperature: float = 0.2) -> str:
        raise NotImplementedError

class OpenAIProvider(LLMProvider):
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI()
    def chat(self, messages, model, temperature=0.2) -> str:
        resp = self._client.chat.completions.create(model=model, messages=messages, temperature=temperature)
        return resp.choices[0].message.content

class OllamaProvider(LLMProvider):
    def __init__(self, base_url="http://localhost:11434"):
        import requests
        self._http = requests
        self.base_url = base_url
    def chat(self, messages, model, temperature=0.2) -> str:
        # Simple single-turn prompt concat
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
        r = self._http.post(f"{self.base_url}/api/generate", json={"model": model, "prompt": prompt, "options": {"temperature": temperature}})
        r.raise_for_status()
        # Stream may be returned, but we aggregate for simplicity
        text = ""
        for line in r.text.splitlines():
            try:
                import json
                obj = json.loads(line)
                text += obj.get("response", "")
            except Exception:
                pass
        return text

def get_llm_provider(name: str) -> LLMProvider:
    if name == "openai":
        return OpenAIProvider()
    if name == "ollama":
        return OllamaProvider()
    raise ValueError(f"Unknown LLM provider: {name}")