import re

def split_by_sentences(text: str, max_chars: int = 800) -> list[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks, buf = [], ""
    for s in sentences:
        if len(buf) + len(s) + 1 <= max_chars:
            buf = f"{buf} {s}".strip()
        else:
            if buf: chunks.append(buf)
            buf = s
    if buf: chunks.append(buf)
    return chunks