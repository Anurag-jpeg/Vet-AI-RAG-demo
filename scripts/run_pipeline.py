import logging
from os import name
from pathlib import Path

from src.config import(
    PDF_ROOT,
    RAW_OUT_ROOT,
    CLEAN_OUT_ROOT,
    CLEAN_LOWERCASE,
    RAW_OUT_ROOT
)

from src.finder import find_pdfs
from src.cleaner import clean_text
from src.extractor import extract_text
from src.io import ensure_output,write_text
from scripts.convert_json import main as convert_json_main

logging.basicConfig(
      level=logging.INFO,
      format="[%(levelname)s] %(message)s",
  )
log = logging.getLogger(__name__)

def main() -> None :
    #Ensure the output directories exists
    ensure_output()
    #Find the pdfs
    pdf_path=find_pdfs()
    if not pdf_path:
        log.error("There is no pdfs in %s" ,PDF_ROOT)
        return
    #extract the text from the pdfs one by one 
    for pdf in pdf_path:
        raw=extract_text(pdf)
        if not raw:
              log.warning("No extractable text for  – skipping")
              continue
        #write the raw extraction for later
        raw_out_path=RAW_OUT_ROOT / f"{pdf.stem}.txt"
        write_text(raw_out_path,raw)
        #get the cleaned data we used from the raw data
        cleaned=clean_text(raw,lower=CLEAN_LOWERCASE)
        #write to the clean path
        clean_out_path=CLEAN_OUT_ROOT / f"{pdf.stem}.txt"
        write_text(clean_out_path,cleaned)


if __name__=="__main__":
    main()


    
