"""Configuration constants for the Vet‑AI pipeline.

- ``PDF_ROOT``       : Directory that should contain the source PDF files.
- ``RAW_OUT_ROOT``   : Where raw extracted PDF text will be written.
- ``CLEAN_OUT_ROOT`` : Where cleaned text will be written.
- ``RECURSIVE``      : If ``True``, PDF discovery walks sub‑folders.
- ``CLEAN_LOWERCASE``: Lower‑case the cleaned text when set.
- ``PAGE_SEPARATOR``: Template used by older code to separate pages.
"""
import os
from pathlib import Path

PDF_ROOT: Path = Path(__file__).resolve().parents[1] / "papers"
# Ensure the folder exists on first use (no‑op if already present)
PDF_ROOT.mkdir(parents=True, exist_ok=True)

RAW_OUT_ROOT: Path = PDF_ROOT / "raw"
CLEAN_OUT_ROOT: Path = PDF_ROOT / "cleaned"

RECURSIVE: bool = False
CLEAN_LOWERCASE: bool = False

RAG_LLM: str = os.getenv("RAG_LLM", "qwen2.5:3b").lower()
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
# Minimum similarity score required to keep a chunk (default = 0.0 – keep everything)
RAG_MIN_SCORE: float = float(os.getenv("RAG_MIN_SCORE", "0.0"))
# Maximum number of tokens the **LLM** is allowed to output
# (the Ollama “max_tokens” argument). 1024 works well for short answers.
RAG_MAX_TOKENS: int = int(os.getenv("RAG_MAX_TOKENS", "1024"))
# Temperature for the generation model – 0.0 = deterministic, 1.0 = v
# Temperature for the generation model – 0.0 = deterministic, 1.0 = very random
RAG_TEMPERATURE: float = float(os.getenv("RAG_TEMPERATURE", "0.0"))
# Maximum number of tokens we will allow in the **prompt** (roughly
# 4 characters per token).  This is a hard cap that keeps the request
# payload small and avoids Ollama‑side time‑outs.
MAX_PROMPT_CHARS: int = int(os.getenv("MAX_PROMPT_CHARS", "8000"))
# Maximum context size (in tokens) that the prompt‑builder will try to fit
# before it starts trimming chunks.  One token ≈ 4 characters.
MAX_CONTEXT_TOKENS: int = int(os.getenv("MAX_CONTEXT_TOKENS", "3000"))


PAGE_SEPARATOR = "\n--- Page {num} ---\n"