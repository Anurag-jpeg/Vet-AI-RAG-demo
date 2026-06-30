# Vet‑AI RAG Demo

A lightweight Retrieval‑Augmented Generation (RAG) system that lets you:

* **Upload PDF research papers** (the server extracts, cleans, chunks, embeds and indexes them).
* **Ask natural‑language questions** about any indexed paper.
* **Get answers with citations** that point back to the exact PDF and chunk.

Everything runs **locally** – no external API keys required.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running Ollama (LLM backend)](#running-ollama-llm-backend)
- [Indexing your PDFs](#indexing-your-pdfs)
- [Start the web UI](#start-the-web-ui)
- [Usage examples](#usage-examples)
- [Project structure](#project-structure)
- [Customization & hyper‑parameters](#customization--hyper‑parameters)
- [Contributing](#contributing)
- [License](#license)

---

## Prerequisites

* **Python 3.9+** (tested on 3.11)
* **Ollama** – local LLM server. Install it from https://ollama.com.
* **Git** (optional, for cloning the repo).

---

## Installation

```bash
# 1️⃣ Clone the repo
git clone https://github.com/<YOUR‑USERNAME>/vet-ai-rag-demo.git
cd vet-ai-rag-demo

# 2️⃣ Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # PowerShell (or `source venv/bin/activate` on *nix)

# 3️⃣ Install Python dependencies
pip install -r requirements.txt

If requirements.txt is missing, you can generate it with pip freeze > requirements.txt after the install step.

---
Running Ollama (LLM backend)

# Start the Ollama server (keep this terminal open)
ollama serve

# Pull a model (the default in the code is `mistral`)
ollama pull mistral   # or any other model you prefer

You can verify it’s alive:

curl http://localhost:11434/api/version
# → {"model":"mistral","version":"..."}

---
Indexing your PDFs

Place any PDF files you already have under the papers/ directory (you can create sub‑folders if you like). Then run the three‑step pipeline once:

# 1️⃣ Extract raw text + clean it
python -m scripts.run_pipeline

# 2️⃣ Convert cleaned text into JSON chunks
python -m scripts.convert_json

# 3️⃣ Embed the chunks and store them in Chroma
python -m scripts.embedding_chroma

You’ll see a final line like count: 220 indicating how many vectors are now in the store.

▎ Future PDFs can be added through the web UI (see next section) – you don’t need to re‑run the pipeline unless you want to batch‑process many files at once.

---
Start the web UI

# Make sure Ollama is still running, then launch the FastAPI server
python server.py

The server starts on http://localhost:8000. Open that address in any modern browser.

UI Overview

┌────────────────┬────────────────────────────────────────────────────────────────────────────────────────────┐
│    Section     │                                        What it does                                        │
├────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Upload a PDF   │ Choose a PDF, click 📥 Ingest PDF – the file is indexed on‑the‑fly.                        │
├────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Ask a question │ Type a question, adjust the k slider (how many chunks to retrieve), click 🤖 Get answer.   │
├────────────────┼────────────────────────────────────────────────────────────────────────────────────────────┤
│ Answer         │ The generated answer appears with citations such as uploaded/MyPaper.pdf (doc 1, chunk 3). │
└────────────────┴────────────────────────────────────────────────────────────────────────────────────────────┘

---
Usage examples

- Query an existing paper – after you’ve indexed the sample PDFs that ship with the repo:

▎ “What is the purpose of the age‑estimation study?”

- You’ll get a short answer and a citation pointing to uploaded/Age estimation.pdf.
- Add a new paper – click Upload a PDF, select new_research.pdf, wait for the green status message, then ask any question about its content.

---
Project structure

Vet_ai/
│
├─ src/                     # core library (retrieval, config, utils)
├─ scripts/                 # CLI helpers (pipeline, embedding, etc.)
├─ static/                  # HTML/CSS/JS front‑end
├─ uploaded/                # PDFs uploaded via the UI (runtime)
├─ embeddings/              # Chroma DB (runtime)
├─ output/                  # JSON chunk files (runtime)
├─ server.py                # FastAPI backend
├─ .gitignore
├─ README.md
└─ requirements.txt

---
Customization & hyper‑parameters

All RAG‑related knobs live in src/config.py and can be overridden with environment variables:

┌────────────────────┬────────────────────────────────────────────────────────────┬─────────┐
│      Variable      │                          Meaning                           │ Default │
├────────────────────┼────────────────────────────────────────────────────────────┼─────────┤
│ RAG_LLM            │ Generation model (e.g., mistral, qwen2.5)                  │ mistral │
├────────────────────┼────────────────────────────────────────────────────────────┼─────────┤
│ RAG_TOP_K          │ Number of retrieved chunks fed to the LLM                  │ 5       │
├────────────────────┼────────────────────────────────────────────────────────────┼─────────┤
│ RAG_MIN_SCORE      │ Minimum similarity score to keep a chunk                   │ 0.0     │
├────────────────────┼────────────────────────────────────────────────────────────┼─────────┤
│ RAG_MAX_TOKENS     │ Max tokens the LLM may emit                                │ 1024    │
├────────────────────┼────────────────────────────────────────────────────────────┼─────────┤
│ RAG_TEMPERATURE    │ Sampling temperature (0 = deterministic)                   │ 0.0     │
├────────────────────┼────────────────────────────────────────────────────────────┼─────────┤
│ MAX_CONTEXT_TOKENS │ Soft token budget for the prompt                           │ 2000    │
├────────────────────┼────────────────────────────────────────────────────────────┼─────────┤
│ MAX_PROMPT_CHARS   │ Hard character cap for the prompt (prevents huge payloads) │ 4000    │
└────────────────────┴────────────────────────────────────────────────────────────┴─────────┘

Example override (Windows PowerShell):

$env:RAG_TEMPERATURE = "0.7"
$env:RAG_TOP_K = "8"
python server.py

---
Contributing

1. Fork the repository.
2. Create a new branch for your change.
3. Make your modifications (run tests if you added any).
4. Submit a Pull Request with a clear description of what you changed.

Feel free to add unit tests under a tests/ directory – they will be run automatically by the CI workflow (see below).

---
License

This project is released under the MIT License – see the LICENSE file (add one if you wish).

---