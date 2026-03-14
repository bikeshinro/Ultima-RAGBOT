import os
from pathlib import Path
from src.data.ingest import ingest_file
from src.config import settings

DEMO_DIR = Path("demo_docs")

def main():
    if not DEMO_DIR.exists():
        print("No demo_docs directory found, skipping seeding.")
        return

    for f in DEMO_DIR.glob("*.*"):
        try:
            count = ingest_file(str(f), user_id="demo", source_name=f.name)
            print(f"Seeded {count} chunks from {f.name}")
        except Exception as e:
            print(f"Failed to ingest {f.name}: {e}")

if __name__ == "__main__":
    main()