# Asystent RAG do dokumentów uczelnianych

Projekt zespołowy „WIM”. Student zadaje pytanie po polsku o dokumenty uczelni (np. Regulamin studiów) i dostaje odpowiedź opartą wyłącznie na wgranych plikach PDF, razem z cytatami (dokument, rozdział, strona, fragment tekstu). Jeśli w dokumentach nie ma odpowiedzi, system odmawia, zamiast zgadywać.

Szczegóły działania: [docs.md](docs.md).

## Technologie

Django + DRF, PostgreSQL, Chroma (baza wektorowa), React (Vite), nginx, OpenRouter (czat i embeddingi).

## Uruchomienie

1. Skopiuj konfigurację i wpisz swój klucz API:
   ```
   cp .env.example .env
   ```
2. Uruchom usługi:
   ```
   docker compose up -d --build
   ```
3. Otwórz aplikację: http://localhost:3000

### Domyślne dane logowania

Tworzone automatycznie przy pierwszym uruchomieniu (gdy baza nie ma jeszcze użytkowników). Ręcznie: `docker compose exec backend python manage.py create_test_users [--password ...]`.

| Rola | E-mail | Hasło |
|---|---|---|
| Student | `student@example.com` | `test1234` |
| Administrator korpusu | `admin@example.com` | `test1234` |

To konta wyłącznie testowe, nie używaj ich na środowisku produkcyjnym.

## Testy

```
docker compose run --rm backend pytest -q
```

## Role

- **Student** – zadaje pytania.
- **Administrator korpusu** – dodatkowo wgrywa dokumenty PDF.
