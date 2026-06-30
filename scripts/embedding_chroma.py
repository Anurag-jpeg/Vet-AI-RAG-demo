import json
from pathlib import Path
import os
import requests
import chromadb
import concurrent.futures


BASE_DIR=Path(__file__).resolve().parents[1]
JSON_DIR= BASE_DIR / "output" / "json"
CHROMA_ROOT=BASE_DIR / "embeddings" / "chroma_db"
#If chroma directory not there it will create it
CHROMA_ROOT.mkdir(parents=True,exist_ok=True)

ollama_embed_model="nomic-embed-text"
ollama_model="mistral"
batch_size=32

def embed_text(texts:list[str])->list[list[float]]:
    """Embed a list of texts concurrently (still uses Ollama’s /embed endpoint)."""

    def _call(txt):
        payload = {"model": ollama_embed_model, "input": [txt]}
        resp = requests.post("http://localhost:11434/api/embed", json=payload, timeout=30)
        resp.raise_for_status()
        return [float(v) for v in resp.json()["embeddings"][0]]
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        # map returns results in the same order as `texts`
        return list(executor.map(_call, texts))

    # payload={"model":ollama_embed_model,"input":texts}
    # resp=requests.post("http://localhost:11434/api/embed",json=payload,timeout=60)
    # resp.raise_for_status()
    # raw=resp.json()["embeddings"]
    # embeddings=[[float(v) for v in vec] for vec in raw]
    # print(
    #       f"[DEBUG] Embedded {len(texts)} texts → {len(embeddings)} vectors "
    #       f"(dim={len(embeddings[0]) if embeddings else 'n/a'})"
    #   )
    # return embeddings

client=chromadb.PersistentClient(path=str(CHROMA_ROOT))
column="papers"
if column in [c.name for c in client.list_collections()]:
    collection=client.get_collection(name=column)
    print("Loaded existing chroma")
else:
    collection=client.create_collection(name=column)
    print("Chroma created")

def deterministic_id(source_file: str, chunk_id: int) -> str:#gives the id for each chunk useful to not duplicate 
    return f"{source_file}::chunk_{chunk_id}"


def main():
    json_paths=sorted(JSON_DIR.glob("*.json"))
    already_id=set(collection.get()["ids"]) #keeps notice of the ids in collection so as to not duplicate
   
    batch_ids=[]
    batch_vecs=[]
    batch_meta=[]
    batch_texts=[]
    
    for p in json_paths:
        data=json.loads(p.read_text(encoding="utf-8"))
        source_file = str(p.relative_to(BASE_DIR)).replace("\\", "/")
        doc_id = data.get("Document_id")

        for chunk in data.get("chunks",[]):
            id=deterministic_id(source_file,chunk["chunk_id"])
            if id in already_id:
                continue

            batch_ids.append(id)
            batch_texts.append(chunk["text"])
            clean_meta={
                "source_file":source_file,
                "document_id":str(doc_id) if doc_id is not None else "",
                "chunk_id":int(chunk["chunk_id"]),
                "token_len":int(chunk.get("token_len",len(chunk["text"].split()))),
                "text":chunk["text"],
            }
            batch_meta.append(clean_meta)
            
            if len(batch_ids)>=batch_size:
                try:
                    batch_vecs=embed_text(batch_texts)
                    collection.add(
                        ids=batch_ids,
                        embeddings=batch_vecs,
                        documents=batch_texts,
                        metadatas=batch_meta,
                    )
                    print(
                          f"[INFO] Added {len(batch_ids)} chunks "
                          f"(total now {collection.count()})")
                except Exception as e:
                    print(f"[ERROR] Failed final batch add (size {len(batch_ids)}): {e}")
                batch_ids,batch_vecs,batch_meta,batch_texts=[] ,[],[],[]
    
    if batch_ids:
        try:
            batch_vecs = embed_text(batch_texts)
            collection.add(
                ids=batch_ids,
                embeddings=batch_vecs,
                documents=batch_texts,
                metadatas=batch_meta,
            )
            print(
                  f"[INFO] Added final {len(batch_ids)} chunks "
                  f"(total now {collection.count()})"
              )
        except Exception as e:
            print(f"[ERROR] Failed final batch add (size {len(batch_ids)}): {e}")

        print("[DONE] Indexing finished.")


if __name__== "__main__":
    main()