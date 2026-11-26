import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from documents import vectorstore
from documents.models import DocumentChunk
from llm import client as llm


class Command(BaseCommand):
    help = "Uruchamia eval/questions.json na prawdziwym indeksie (tylko embeddingi) i sugeruje próg podobieństwa."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="eval/questions.json")

    def handle(self, *args, **options):
        with open(options["file"], encoding="utf-8") as file:
            questions = json.load(file)

        answerable_scores, refused_scores = [], []
        for item in questions:
            embedding = llm.embed([item["question"]])[0]
            matches = vectorstore.query(embedding, settings.TOP_K)
            if not matches:
                raise CommandError("Indeks jest pusty - najpierw wgraj dokument.")
            best_score = matches[0][1]
            pages = [DocumentChunk.objects.get(chroma_id=chroma_id).page for chroma_id, _ in matches]
            expected = item["expected_page"]  # None = oczekiwana odmowa
            # oczekiwana strona musi być wśród fragmentów przekazywanych modelowi
            verdict = "OK" if expected is None or expected in pages else "PUDŁO"
            (refused_scores if expected is None else answerable_scores).append(best_score)
            self.stdout.write(
                f"{best_score:.3f} top{settings.TOP_K}_strony={pages} oczekiwana={expected} "
                f"{verdict} | {item['question']}"
            )

        low = max(refused_scores, default=0)
        high = min(answerable_scores, default=1)
        suggestion = f"{(low + high) / 2:.2f}" if low < high else "BRAK - klasy się nakładają"
        self.stdout.write(f"maks. podobieństwo odmów={low:.3f}, min. podobieństwo pytań z odpowiedzią={high:.3f}")
        self.stdout.write(f"sugerowany próg: {suggestion}")
