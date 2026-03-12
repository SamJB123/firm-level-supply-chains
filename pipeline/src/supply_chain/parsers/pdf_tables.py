from __future__ import annotations

import re


def extract_lines_near_markers(text: str, markers: list[str], window: int = 12) -> list[str]:
    lines = [line.strip() for line in text.splitlines()]
    snippets: list[str] = []
    for index, line in enumerate(lines):
        if any(marker in line for marker in markers):
            start = max(index - 2, 0)
            end = min(index + window, len(lines))
            snippets.append("\n".join(lines[start:end]))
    return snippets


def normalize_table_line(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
