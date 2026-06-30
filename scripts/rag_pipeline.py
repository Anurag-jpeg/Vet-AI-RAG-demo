import os
import requests
import sys
import logging
from typing import List,Dict,Any
from tqdm import tqdm

from src import retrieve
from src.config import MAX_PROMPT_CHARS

RAG_LLM: str=os.getenv("RAG_LLM","qwen2.5:3b").lower()
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
RAG_MIN_SCORE: float = float(os.getenv("RAG_MIN_SCORE", "0.1"))
MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "2000"))
RAG_TEMPERATURE: float = float(os.getenv("RAG_TEMPERATURE", "0.7"))
RAG_MAX_TOKENS: int = int(os.getenv("RAG_MAX_TOKENS", "1024"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(level=LOG_LEVEL,format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def truncate_to_token_budget(text:str,max_tokens:int)->str:
    """Approximate: 1 token = 4 characters"""
    return text[:max_tokens*4]

def build_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Prompt layout:

    <system instruction>
    Context:
    [1] …chunk 1…
    [2] …chunk 2…
    …
    Question: <question>
    Answer (with citations):
    """
    system = (
        "You are a helpful, curious assistant. "
        "First think step‑by‑step, then answer the question. "
        "If the given context does not contain enough information, you may draw on "
        "your own general knowledge, but always cite the retrieved chunks you used."
    )
    # Pre‑process chunk text to remove newlines (avoid backslashes in f‑string expressions)
    cleaned_chunks = []
    for i, c in enumerate(chunks, start=1):
        txt = c['text'].replace("\n", " ")
        cleaned_chunks.append(f"[{i}] {txt}")
    ctx = "\n".join(cleaned_chunks)
    return f"{system}\n\nContext:\n{ctx}\n\nQuestion: {question}\nAnswer (with citations):"

import time

def call_ollama(prompt:str,model:str="qwen2.5:3b",temperature:float=0.01,max_tokens:int=1024,timeout:int=30)->str:
    """Sends a chat request to Ollama and returns the raw completion.It also lets the ollama attempt 2 times if there is any stall"""
    payload={
        "model":model,
        "messages":[{"role":"user","content":prompt}],
        "temperature":temperature,
        "max_tokens":max_tokens,
        "stream":False,
        }
    attempt=0
    while attempt<3:
        try:
            resp=requests.post("http://localhost:11434/api/chat",
                json=payload,
                timeout=timeout,)
            resp.raise_for_status()
            return resp.json()["message"]["content"]

        except Exception as e:
            attempt+=1
            log.warning("Ollama request failed (attempt %d): %s", attempt, e)
            if attempt>=3:
                raise
            time.sleep(1.0*attempt) #simple back-off time

    

def dispatch_llm(prompt: str) -> str:
    """
    Choose the actual Ollama model based on RAG_LLM.
    Supports:
        * "mistral"
        * "qwen2.5"
    Any other string is taken as a raw model name.
    """
    if RAG_LLM in {"mistral", "mistral-7b"}:
        model_name = "mistral"
    elif RAG_LLM in {"qwen2.5", "qwen2.5:3b", "qwen"}:
        model_name = "qwen2.5:3b"
    else:
        model_name = RAG_LLM   # custom model (whichever you want to add)

    log.debug("🦙  Ollama call → model=%s  temp=%.2f  max_tok=%d",
              model_name, RAG_TEMPERATURE, RAG_MAX_TOKENS)

    return call_ollama(
        prompt,
        model=model_name,
        temperature=RAG_TEMPERATURE,
        max_tokens=RAG_MAX_TOKENS,
    )

def render_citations(answer:str,hits:List[Dict[str,Any]])->str:
    """Replace the [1] or [2] etc with the source-file or related"""
    import re
    def repl(m):
        idx=int(m.group(1))-1
        if idx<0 or idx >=len(hits):
            return m.group(0)
        h=hits[idx]
        return f"{h['source_file']} (doc {h['document_id']}, chunk {h['chunk_id']})"
    
    return re.sub(r"\[(\d+)\]", repl, answer)

def rag_query(question:str,k:int=RAG_TOP_K,min_score:float=RAG_MIN_SCORE,max_context_tokens:int=MAX_CONTEXT_TOKENS)->str:
    log.info("Retrieving up to %s chunks (min score=%s)",k,min_score)
    hits=retrieve(question,k=k) #retrieving from chromdb package we made in src
    if not hits:
        fallback_prompt = (
            "You are an AI assistant. Answer the following question using your general knowledge. "
            f"Question: {question}"
        )
        return dispatch_llm(fallback_prompt)
    
    combined=" ".join(hit["text"] for hit in hits)
    trimmed=truncate_to_token_budget(combined,max_context_tokens)

    kept=[]
    cur_len=0
    for hit in hits:
        txt=hit["text"]
        if cur_len + len(txt) > len(trimmed):
            break
        kept.append(hit)
        cur_len+=len(txt)

        if not kept:
            kept=[hits[0]]
    prompt = build_prompt(question, kept)
    if len(prompt)>MAX_PROMPT_CHARS:
        #TRIM FROM THE TAIL
        prompt=prompt[:MAX_PROMPT_CHARS]
        log.debug("Prompt trimmed to %d chars (MAX_PROMPT_CHAR)",MAX_PROMPT_CHARS)


    log.debug("🖊️ Prompt length=%d chars", len(prompt))

    raw_answer = dispatch_llm(prompt)
    log.info("✅ LLM answered (%d characters)", len(raw_answer))

    return render_citations(raw_answer, kept)

def _cli() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/rag_pipeline.py \"<question>\" [k]\n"
            "       Set RAG_LLM=mistral|qwen2.5 to choose the Ollama model.\n"
            "       Optional vars: RAG_TEMPERATURE, RAG_MAX_TOKENS, etc."
        )
        sys.exit(1)

    question = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else RAG_TOP_K
    answer = rag_query(question, k=k)
    print("\n=== Answer ===\n")
    print(answer)

if __name__ == "__main__":
    _cli()
