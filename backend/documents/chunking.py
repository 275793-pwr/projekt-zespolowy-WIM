import re

from django.conf import settings

CHAPTER_RE = re.compile(r"^[ \t]*(§\s*\d+[a-z]?)", re.MULTILINE)


def _split_page(text, lo, hi, overlap):
    """Zwraca zakresy (start, koniec) w `text`, nigdy poza stroną."""
    n = len(text)
    start = 0
    while start < n:
        end = min(start + hi, n)
        if end < n:
            cut = max(text.rfind(" ", start + lo, end), text.rfind("\n", start + lo, end))
            if cut > start:
                end = cut
        yield start, end
        if end >= n:
            break
        nxt = end - overlap
        sp = text.find(" ", nxt, end)
        start = sp + 1 if sp != -1 else nxt
        if start <= 0 or start >= end:
            start = end


def chunk_pages(pages):
    """pages: lista tekstów stron (indeks 0 = strona 1). Zwraca listę słowników z polami page, chunk_index, chapter, text."""
    lo, hi = settings.CHUNK_SIZE
    overlap = settings.CHUNK_OVERLAP
    chunks, carried = [], ""
    for pno, raw in enumerate(pages, start=1):
        text = re.sub(r"[ \t]+", " ", raw or "").strip()
        if not text:
            continue
        markers = [(m.start(1), re.sub(r"\s+", " ", m.group(1))) for m in CHAPTER_RE.finditer(text)]
        for s, e in _split_page(text, lo, hi, overlap):
            piece = text[s:e].strip()
            if len(piece) < 20:
                continue
            before = [m for m in markers if m[0] <= s]
            inside = [m for m in markers if s < m[0] < e]
            chapter = before[-1][1] if before else (carried if not inside else inside[0][1])
            chunks.append({"page": pno, "chunk_index": len(chunks), "chapter": chapter, "text": piece})
        if markers:
            carried = markers[-1][1]
    return chunks
