# src/data/loaders.py
from pathlib import Path
from typing import Tuple
import mimetypes

def load_txt(path: str) -> Tuple[str, str]:
    return Path(path).read_text(encoding="utf-8"), "text/plain"

def load_pdf(path: str) -> Tuple[str, str]:
    from pypdf import PdfReader
    reader = PdfReader(path)
    text = "\n".join([p.extract_text() or "" for p in reader.pages])
    return text, "application/pdf"

def load_docx(path: str) -> Tuple[str, str]:
    import docx
    doc = docx.Document(path)
    text = "\n".join([p.text for p in doc.paragraphs])
    return text, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

def load_any(path: str) -> Tuple[str, str]:
    mime, _ = mimetypes.guess_type(path)
    suffix = Path(path).suffix.lower()
    if suffix == ".txt":
        return load_txt(path)
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix in [".docx"]:
        return load_docx(path)
    raise ValueError(f"Unsupported file type: {suffix}")