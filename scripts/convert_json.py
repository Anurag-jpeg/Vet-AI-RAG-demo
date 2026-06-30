
import datetime
import json
import pathlib
from pathlib import Path
from src.config import PDF_ROOT
from PyPDF2 import PdfReader
import re
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter


BASE_DIR=Path(__file__).resolve().parents[1]
CLEANED_DIR=PDF_ROOT / "cleaned"
OUTPUT_JSON_DIR=BASE_DIR / "output" / "json"

OUTPUT_JSON_DIR.mkdir(parents=True,exist_ok=True)

def chunk_text(clean_text:str):
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )
    return splitter.split_text(clean_text)


def get_page_count(pdf_path:Path) -> int :

    try:
        reader=PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception as exc:
        print(f"Count not read page from {pdf_path}: {exc}")
        return 0

def load_cleaned_text(text_path:Path) -> str:
    """Read the cleaned text file"""
    try:
        return text_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"Could not read cleaned text {text_path}: {exc}")
        return ""

def extract_abstract(cleaned_text) -> str | None:
    abstract_match=re.search(r"abstract(.*?)(introduction|keywords)",cleaned_text,re.IGNORECASE| re.DOTALL)
    abstract=(
        abstract_match.group(1).strip()
        if abstract_match
        else None
    )
    return abstract


    

def extract_result(text:str)-> str |None:
    pattern=(
        r"results\s*(.*?)\s"
        r"(discussion|conclusion|references)"
    )
    match=re.search(pattern,text,flags=re.IGNORECASE|re.DOTALL)
    
    if not match:
        return None
    return match.group(1).strip()


def build_json_record(doc_id: int ,pdf_path: pathlib.Path ,cleaned_text:str) -> dict :
    """Assemble the Json format for single documents"""

    base_name=pdf_path.stem
    word_count=len(cleaned_text.split())
    page_count=get_page_count(pdf_path)

    return {
        "document_id":doc_id,
        "paper_name":base_name,
        "file_name":pdf_path.name,
        "source_file":str(pdf_path.relative_to(BASE_DIR)).replace("\\","/"),
    
        "result":extract_result(cleaned_text),
        "abstract":extract_abstract(cleaned_text),
        "author":None,
        "species":None,
        "conditions":None,
        "word_count":word_count,
        "page_count":page_count,
        "chunks":[
            {
                "chunk_id":idx+1,
                "text":chunk

            }
            for idx,chunk in enumerate(chunk_text(cleaned_text))
        ],
        "file_size_bytes":pdf_path.stat().st_size,
        "cleaned_text":cleaned_text,
        "processed_at": datetime.utcnow().isoformat(),
        
    }

def main() -> None :
    pdf_files=sorted(PDF_ROOT.glob("*.pdf"))
    if not pdf_files:
          print("[INFO] No PDFs found under", PDF_ROOT)
          return
    for idx,pdf_path in enumerate(pdf_files,start=1):
        cleaned_txt_path=CLEANED_DIR / f"{pdf_path.stem}.txt"

        cleaned_text=load_cleaned_text(cleaned_txt_path)
        if not cleaned_text:
              print(f"[WARN] Skipping {pdf_path.name}: cleaned text missing.")
              continue
        
        record=build_json_record(idx,pdf_path,cleaned_text)
        
        out_path = OUTPUT_JSON_DIR / f"{pdf_path.stem}.json"
        out_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[DONE] [{idx}/{len(pdf_files)}] → {out_path.relative_to(BASE_DIR)}")

if __name__ =="__main__":
    main()
