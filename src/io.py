from pathlib import Path
import logging

log=logging.getLogger(__name__)

def ensure_output() -> None :
    """Create the raw/ and cleaned/ folders under PDF_ROOT."""
    from .config import RAW_OUT_ROOT, CLEAN_OUT_ROOT

    RAW_OUT_ROOT.mkdir(parents=True, exist_ok=True)
    CLEAN_OUT_ROOT.mkdir(parents=True, exist_ok=True)

def write_text(path: Path, content: str) -> None:
    """Write UTF‑8 text to *path* (overwrites if it exists)."""
    with path.open("w", encoding="utf-8") as f:
        f.write(content)
    log.info("Wrote %s", path)