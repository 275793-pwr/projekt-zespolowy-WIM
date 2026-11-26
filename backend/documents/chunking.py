"""Dzielenie tekstu stron PDF na fragmenty. Fragment nigdy nie przekracza granicy strony."""
import re

from django.conf import settings

CHAPTER_RE = re.compile(r"^[ \t]*(§\s*\d+[a-z]?)", re.MULTILINE)
MIN_CHUNK_LENGTH = 20


def _split_page(text, min_size, max_size, overlap):
    """Zwraca zakresy (start, koniec) w `text`, nigdy poza stroną."""
    length = len(text)
    start = 0
    while start < length:
        end = min(start + max_size, length)
        if end < length:
            # tnij na spacji lub końcu linii, żeby nie rozrywać słów
            cut = max(text.rfind(" ", start + min_size, end), text.rfind("\n", start + min_size, end))
            if cut > start:
                end = cut
        yield start, end
        if end >= length:
            break
        overlap_start = end - overlap
        space = text.find(" ", overlap_start, end)
        next_start = space + 1 if space != -1 else overlap_start
        start = next_start if 0 < next_start < end else end


def _chapter_for(start, end, chapters, carried):
    """Ostatni § przed początkiem fragmentu, potem pierwszy § wewnątrz, na końcu § z poprzedniej strony."""
    before = [name for position, name in chapters if position <= start]
    if before:
        return before[-1]
    return next((name for position, name in chapters if start < position < end), carried)


def chunk_pages(pages):
    """pages: lista tekstów stron (indeks 0 = strona 1). Zwraca słowniki z polami page, chunk_index, chapter, text."""
    min_size, max_size = settings.CHUNK_SIZE
    chunks = []
    carried = ""
    for page_number, raw_text in enumerate(pages, start=1):
        text = re.sub(r"[ \t]+", " ", raw_text or "").strip()
        if not text:
            continue
        # [(pozycja, nazwa)] znaczników § na stronie
        chapters = [(match.start(1), re.sub(r"\s+", " ", match.group(1))) for match in CHAPTER_RE.finditer(text)]
        for start, end in _split_page(text, min_size, max_size, settings.CHUNK_OVERLAP):
            piece = text[start:end].strip()
            if len(piece) < MIN_CHUNK_LENGTH:
                continue
            chunks.append({
                "page": page_number,
                "chunk_index": len(chunks),
                "chapter": _chapter_for(start, end, chapters, carried),
                "text": piece,
            })
        if chapters:
            carried = chapters[-1][1]
    return chunks
