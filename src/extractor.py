import logging
from optparse import Option
from pathlib import Path
from typing import Optional
from PyPDF2 import PdfReader

log=logging.getLogger(__name__)

def extract_pdf(pdf_path: Path) -> Optional[str] :
    try:
        reader=PdfReader(str(pdf_path))
    except Exception as exc:
        log.warning(
            "PdfReader failed for %s: %s",
            pdf_path,
            exc
        )
        return None
    
    if not reader.pages:
          log.info("No pages in %s", pdf_path.name)
          return None
    
    out=[]

    for i,page in enumerate(reader.pages):
        txt=page.extract_text() or ""
        out.append(f"\n--Page{i+1}---\n{txt}")
    
    return "".join(out)
    
def extract_text(pdf_path:Path) -> Optional[str] :
    
    raw=extract_pdf(pdf_path) 

    return raw