
import os
import logging
from pathlib import Path
from typing import List

import requests
from fastapi import FastAPI, File, UploadFile, HTTPException, Body, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ------------------------------------------------------------------
# Project imports (your existing library code)
# ------------------------------------------------------------------
from src import retrieve                     # legacy retrieve function (not used for query)
from scripts.rag_pipeline import rag_query                     # actual RAG query implementation
from src.extractor import extract_text       # PDF → raw text
from src.cleaner import clean_text           # text cleaning
from src.config import PDF_ROOT, MAX_PROMPT_CHARS
from src.retrieve_chroma import collection   # Chroma collection

# ------------------------------------------------------------------
# Logging setup
# ------------------------------------------------------------------
log = logging.getLogger("vet_ai_server")
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
log.addHandler(handler)

# ------------------------------------------------------------------
# FastAPI app definition
# ------------------------------------------------------------------
app = FastAPI(
    title="Vet‑AI RAG Demo",
    description="Upload PDFs and ask questions – no Gradio, just HTML/CSS/JS.",
)

# Allow the frontend (served from the same origin) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the static front‑end (index.html, style.css, script.js)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

# Serve the main page at root
@app.get("/", response_class=FileResponse)
async def serve_root():
    return FileResponse(path="static/index.html", media_type="text/html")

# ------------------------------------------------------------------
# Helper: embed a batch of texts using Ollama's embed endpoint
# ------------------------------------------------------------------
def embed_batch(texts: List[str]) -> List[List[float]]:
    """Send a batch of strings to Ollama's embed model and return vectors."""
    payload = {"model": "nomic-embed-text", "input": texts}
    resp = requests.post(
        "http://localhost:11434/api/embed", json=payload, timeout=30
    )
    resp.raise_for_status()
    # Ollama returns a list of embeddings (one per input string).
    return [list(map(float, vec)) for vec in resp.json()["embeddings"]]

# ------------------------------------------------------------------
# PDF ingestion – called when a user uploads a file via the UI
# ------------------------------------------------------------------
def ingest_pdf(temp_path: Path, original_name: str) -> str:
    """Extract, clean, chunk, embed and store a newly uploaded PDF.

    Parameters
    ----------
    temp_path: Path
        Path to the temporary file created by FastAPI's upload handling.
    original_name: str
        The original filename (used for metadata and citations).
    """
    # 1️⃣ Extract raw text from the PDF
    raw = extract_text(temp_path)
    if not raw:
        return f"❌ Extraction failed – no text found in **{original_name}**."

    # 2️⃣ Clean the extracted text
    cleaned = clean_text(raw, lower=False)

    # 3️⃣ Chunk the cleaned text (same splitter config used elsewhere)
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(cleaned)
    if not chunks:
        return f"❌ No chunks could be created from **{original_name}**."

    # 4️⃣ Embed the chunks in batches (default 32, you can tweak)
    batch_size = 32
    doc_id = f"{int(os.path.getmtime(temp_path))}_{original_name}"

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_ids = [
            f"{original_name}::chunk_{i + idx + 1}" for idx in range(len(batch))
        ]
        batch_embeddings = embed_batch(batch)
        batch_meta = [
            {
                "source_file": f"uploaded/{original_name}",
                "document_id": doc_id,
                "chunk_id": i + idx + 1,
                "token_len": len(txt.split()),
            }
            for idx, txt in enumerate(batch)
        ]
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch,
            metadatas=batch_meta,
        )
        log.info(
            "✅ Added %d chunks from %s (total now %d)",
            len(batch),
            original_name,
            collection.count(),
        )

    return f"✅ **{original_name}** ingested: {len(chunks)} chunks added."

# ------------------------------------------------------------------
# API endpoint: upload a PDF
# ------------------------------------------------------------------
@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted")

    upload_dir = Path("uploaded")
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest_path = upload_dir / file.filename

    # Write the uploaded file to disk (streamed to avoid loading whole file into memory)
    with dest_path.open("wb") as out:
        while chunk := await file.read(1024 * 1024):  # 1 MiB chunks
            out.write(chunk)

    try:
        message = ingest_pdf(dest_path, file.filename)
    except Exception as exc:
        log.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc))

    return JSONResponse(content={"status": "ok", "message": message})

# ------------------------------------------------------------------
# API endpoint: ask a question (RAG query)
# ------------------------------------------------------------------
from fastapi import Request

@app.post("/api/query")
async def api_query(request: Request):
    payload = await request.json()
    question: str = payload.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'question' field")
    k: int = int(payload.get("k", 5))
    try:
        answer = rag_query(question, k=k)
    except Exception as exc:
        log.exception("RAG query failed")
        raise HTTPException(status_code=500, detail=str(exc))
    return JSONResponse(content={"status": "ok", "answer": answer})

# ------------------------------------------------------------------
# Health‑check endpoint (optional)
# ------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "message": "Server is running"}

# ------------------------------------------------------------------
# Entry point – start the server with uvicorn
# ------------------------------------------------------------------
if __name__ == "__main__":
    # Verify Ollama is reachable before launching the API.
    try:
        requests.get("http://localhost:11434/api/version", timeout=3)
    except Exception:
        log.error(
            "⚠️  Ollama does not appear to be running on http://localhost:11434.\n"
            "    Start it with `ollama serve` and pull a model before launching the UI."
        )
        raise SystemExit(1)

    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
