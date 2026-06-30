import json, requests, sys
from pathlib import Path
import chromadb

BASE_DIR = Path(__file__).resolve().parents[1]
CHROMA_ROOT = BASE_DIR / "embeddings" / "chroma_db"
client = chromadb.PersistentClient(path=str(CHROMA_ROOT))
collection = client.get_collection(name="papers")

print("[INFO] Collection contains", collection.count(), "vectors.")
print("[INFO] First 3 IDs:", collection.get()["ids"][:3])

  # Test the embed endpoint (replace the model name if you use another one)
OLLAMA_EMBED_MODEL = "nomic-embed-text"
def test_embed(s):
    payload = {"model": OLLAMA_EMBED_MODEL, "input": [s]}
    r = requests.post("http://localhost:11434/api/embed", json=payload, timeout=10)
    r.raise_for_status()
    vec = r.json()["embeddings"][0]
    print("[DEBUG] Embedding length:", len(vec))
    return vec

if __name__ == "__main__":
    test_embed("test query")
