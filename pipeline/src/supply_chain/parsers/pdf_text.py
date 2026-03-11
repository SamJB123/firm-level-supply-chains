from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(path: str | Path, max_pages: int | None = None) -> str:
    reader = PdfReader(str(path))
    pages = reader.pages if max_pages is None else reader.pages[:max_pages]
    extracted: list[str] = []
    for page in pages:
        text = page.extract_text() or ""
        extracted.append(text)
    return "\n".join(extracted)
