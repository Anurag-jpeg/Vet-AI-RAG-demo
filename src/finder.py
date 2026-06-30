"""Utilities for locating PDF files in the repository.

The helper respects the ``RECURSIVE`` flag from :mod:`src.config`
to decide whether to walk sub‑directories.
"""

import logging
from pathlib import Path
from .config import PDF_ROOT, RECURSIVE

log = logging.getLogger(__name__)

def find_pdfs() -> list[Path]:
    """Return a sorted list of absolute PDF paths under ``PDF_ROOT``.

    If ``RECURSIVE`` is ``True`` we search sub‑folders (``**/*.pdf``);
    otherwise we look only at the top level (``*.pdf``).

    Logs a warning if ``PDF_ROOT`` does not exist.
    """
    if not PDF_ROOT.exists():
        log.warning("PDF_ROOT '%s' does not exist – no PDFs will be found", PDF_ROOT)
        return []

    pattern = "**/*.pdf" if RECURSIVE else "*.pdf"
    return sorted(PDF_ROOT.glob(pattern))


