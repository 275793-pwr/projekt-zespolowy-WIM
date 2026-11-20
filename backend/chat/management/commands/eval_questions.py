import json

from django.core.management.base import BaseCommand

from documents import vectorstore
from documents.models import DocumentChunk
from llm import client as llm


class Command(BaseCommand):
    help = "Uruchamia eval/questions.json na prawdziwym indeksie (tylko embeddingi) i sugeruje próg podobieństwa."

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
            ok = exp is None or exp in pages  # oczekiwana strona musi być w top 5 przekazanych modelowi
            (answerable if exp is not None else refused).append(sim)
            self.stdout.write(f"{sim:.3f} top5_strony={pages} oczekiwana={exp} {'OK' if ok else 'PUDŁO'} | {q['question']}")
        lo, hi = max(refused, default=0), min(answerable, default=1)
        self.stdout.write(f"maks. podobieństwo odmów={lo:.3f}, min. podobieństwo pytań z odpowiedzią={hi:.3f}")
        self.stdout.write("sugerowany próg: " + (f"{(lo + hi) / 2:.2f}" if lo < hi else "BRAK - klasy się nakładają"))
