import os
import gradio as gr
from pathlib import Path
import logging
from scripts.rag_pipeline import rag_query, RAG_TOP_K
import requests
#project imports
from src import retrieve
from src.extractor import extract_text
from src.cleaner import clean_text
from src.config import PDF_ROOT,RAG_MAX_TOKENS,RAG_TOP_K,RAG_TEMPERATURE
from src.retrieve_chroma import collection, embed_text

def embed_batches(texts:list[str])->list[list[float]]:
    payload={"model":"nomic-embed-text","input":texts}
    resp=requests.post("http://localhost:11434/api/embed", json=payload, timeout=30)
    resp.raise_for_status()
    # Ollama returns a list of embeddings, one per input string
    return [list(map(float, vec)) for vec in resp.json()["embeddings"]]

def ingest_pdf(pdf_file_path:str,filename:str)->str:
    """
    Process an uploaded PDF and add its chunks to the Chroma collection.

    Parameters
    ----------
    pdf_file_path: str
        Temporary path where Gradio saved the uploaded file.
    filename: str
        Original name of the uploaded PDF (used for metadata).

    Returns
    -------
    str
        Human‑readable status message displayed in the UI.
    """
    log=logging.getLogger(__name__)
    try:
        raw_txt=extract_text(Path(pdf_file_path))
        if not raw_txt:
            return f" Extraction failed – no text found in **{filename}**."
    except Exception as exc:
        return f" PDF extraction error for **{filename}**: {exc}"

    cleaned=clean_text(raw_txt,lower=False)

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter=RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=150, separators=["\n\n", "\n", ". ", " ", ""],)
    chunks=splitter.split_text(cleaned)
    if not chunks:
        return f" No chunks produced from **{filename}**."
    
    #Embed-Same as the embed file we have
    batch_size=32
    ids, embeddings, documents, metadatas = [], [], [], []
    # Use a deterministic document id (timestamp + filename) so the same PDF
    # uploaded twice will generate a new id each time.
    doc_id = f"{int(os.path.getmtime(pdf_file_path))}_{filename}"
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        batch_ids = [
            f"{filename}::chunk_{i + idx + 1}" for idx in range(len(batch))
        ]
        batch_embeddings = embed_text(batch)

        ids.extend(batch_ids)
        embeddings.extend(batch_embeddings)
        documents.extend(batch)
        metadatas.extend(
            [
                {
                    "source_file": f"uploaded/{filename}",
                    "document_id": doc_id,
                    "chunk_id": i + idx + 1,
                    "token_len": len(txt.split()),
                }
                for idx, txt in enumerate(batch)
            ]
        )

        # Add each batch to Chroma (this way we don’t hold the whole DB in RAM)
        collection.add(
            ids=batch_ids,
            embeddings=batch_embeddings,
            documents=batch,
            metadatas=metadatas[-len(batch) :],
        )
        log.info(
            " Added %d chunks from %s (total now %d)",
            len(batch),
            filename,
            collection.count(),
        )

    return f" **{filename}** ingested: {len(chunks)} chunks added to the vector store."





def answer(question: str, k: int = RAG_TOP_K) -> str:
    """
    Wrapper used by Gradio.
    Calls the RAG pipeline and returns the formatted answer.
    """
    return rag_query(question, k=k)

with gr.Blocks() as demo:
    gr.Markdown("Vet Research Based RAG")
    with gr.Row():
        with gr.Column():
            pdf_uploader = gr.File(
                label="Upload your PDF",
                file_types=[".pdf"],
                type="filepath",
            )
            upload_btn=gr.Button("UPLOAD")
            upload_status=gr.Markdown("")

        with gr.Column():
            txt_question = gr.Textbox(
                label="Your question",
                placeholder="Ask anything about the indexed documents..."
            )
            num_k = gr.Slider(
                minimum=1,
                maximum=10,
                step=1,
                value=5,
                label="Number of chunks to retrieve (k)",
            )
            btn = gr.Button("Get answer")
        with gr.Column():
            out_answer = gr.Textbox(
                label="Answer",
                lines=15,
                interactive=False,  
            )
    upload_btn.click(
        fn=lambda file_path: ingest_pdf(file_path, os.path.basename(file_path))
        if file_path
        else " No file selected.",
        inputs=[pdf_uploader],
        outputs=upload_status,
    )
    btn.click(fn=answer, inputs=[txt_question, num_k], outputs=out_answer)

if __name__ == "__main__":
    # Run on localhost, port 7860 (default for Gradio)
    demo.launch()