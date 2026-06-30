import json ,requests,sys
from pathlib import Path
import chromadb
from functools import lru_cache


BASE_DIR=Path(__file__).resolve().parents[1]
CHROMA_ROOT= BASE_DIR/ "embeddings" / "chroma_db"
client=chromadb.PersistentClient(path=str(CHROMA_ROOT))
collection=client.get_collection(name="papers")

ollama_embed="nomic-embed-text"
import os
# Minimum similarity score to keep a hit – configurable via env var RAG_MIN_SCORE (default 0.0)
min_score = float(os.getenv("RAG_MIN_SCORE", "0.0"))
# Default number of results – configurable via env var RAG_TOP_K (default 5)
top_k = int(os.getenv("RAG_TOP_K", "5"))

@lru_cache(maxsize=64)   #cache upto 64 different queries 
def embed_text(q:str):
    payload={"model":ollama_embed,"input":[q]}
    return requests.post("http://localhost:11434/api/embed",json=payload).json()["embeddings"][0]

def retrieve(query:str,k:int =top_k):
    q_vec=embed_text(query)
    out=collection.query(
        query_embeddings=[q_vec],
        n_results=k,
        include=["documents","metadatas","distances"]
    )
    hits=[]
    for txt,meta,dist in zip(out["documents"][0],out["metadatas"][0],out["distances"][0]):
        # Convert distance to a similarity score (higher is better)
        # Using 1/(1+dist) works for Euclidean or cosine distances and always yields a value in (0, 1]
        score = 1.0 / (1.0 + dist)
        if score<min_score:
            continue
        hits.append({
            "text":txt,
            "source_file":meta["source_file"],
            "document_id":meta["document_id"],
            "chunk_id":meta["chunk_id"],
            "score": round(score,3),  #Gives the cosine similarity
        })
    hits.sort(key=lambda h:h["score"],reverse=True)
    return hits


