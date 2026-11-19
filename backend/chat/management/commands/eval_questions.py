import json

from django.core.management.base import BaseCommand

from documents import vectorstore
from documents.models import DocumentChunk
from llm import client as llm


class Command(BaseCommand):
    help = "Runs eval/questions.json against the real index (embeddings only) and suggests a similarity threshold."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="eval/questions.json")

    def handle(self, *a, **o):
        qs = json.load(open(o["file"], encoding="utf-8"))
        answerable, refused = [], []
        for q in qs:
            v = llm.embed([q["question"]]).vectors[0]
            top = vectorstore.query(v, 5)
            cid, sim = top[0]
            pages = [DocumentChunk.objects.get(chroma_id=c).page for c, _ in top]
            exp = q["expected_page"]
            ok = exp is None or exp in pages  # expected page must be among top-5 sent to the model
            (answerable if exp is not None else refused).append(sim)
            self.stdout.write(f"{sim:.3f} top5_pages={pages} expected={exp} {'OK' if ok else 'MISSED'} | {q['question']}")
        lo, hi = max(refused, default=0), min(answerable, default=1)
        self.stdout.write(f"max similarity of refusals={lo:.3f}, min of answerable={hi:.3f}")
        self.stdout.write("suggested threshold: " + (f"{(lo + hi) / 2:.2f}" if lo < hi else "NONE - classes overlap"))
