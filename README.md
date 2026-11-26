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

## Role

- **Student** – zadaje pytania.
- **Administrator korpusu** – dodatkowo wgrywa dokumenty PDF.

## Wdrożenie na własnym serwerze

Wymagania na serwerze: Linux, Docker z pluginem `docker compose` (v2.24+), git, curl.

1. Sklonuj repozytorium i przejdź do katalogu:
   ```
   git clone <adres-repo> wim && cd wim
   ```
2. Utwórz `.env` i ustaw **własne** wartości (skrypt odmówi wdrożenia, jeśli zostaną wartości domyślne):
   ```
   cp .env.example .env
   nano .env
   ```
   - `API_KEY` – klucz OpenRouter,
   - `DJANGO_SECRET_KEY` – długi losowy ciąg (np. `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`),
   - `POSTGRES_PASSWORD` – inne niż `zesp`,
   - `DJANGO_ALLOWED_HOSTS` – domena lub IP serwera, np. `wim.example.pl`,
   - `DJANGO_DEBUG=0`.
3. Wdróż:
   ```
   ./deploy/deploy.sh
   ```
   Skrypt robi `git pull`, buduje obrazy, uruchamia usługi (`docker-compose.prod.yml`) i sprawdza, czy aplikacja odpowiada. Aplikacja działa na porcie 80 (zmiana: `HTTP_PORT` w `.env`).
4. Konta testowe tworzą się tylko przy pustej bazie. Na produkcji **zmień hasła** lub usuń konta testowe (`docker compose ... exec backend python manage.py shell`).

Aktualizacja: ponownie `./deploy/deploy.sh`. Dane (baza, Chroma, pliki PDF) są w wolumenach Dockera (`pgdata`, `appdata`) i przetrwają redeploy.

### HTTPS

Aplikacja nie obsługuje TLS sama. Najprościej postawić przed nią reverse proxy z automatycznymi certyfikatami, np. Caddy, który kieruje domenę na `localhost:80`:
```
wim.example.pl {
    reverse_proxy localhost:80
}
```

### Przydatne komendy

```
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend
```

### Automatyczne wdrażanie (self-hosted runner)

Workflow `.github/workflows/deploy.yml` wdraża każdy push na `main` (albo ręcznie: Actions → Deploy → Run workflow). Działa na runnerze zainstalowanym na serwerze. Runner sam łączy się z GitHubem, więc serwer nie potrzebuje publicznego IP ani otwartych portów.

Jednorazowa konfiguracja:

1. **Repo na serwerze** – sklonuj repo (`git clone <adres> ~/wim`). Serwer musi mieć dostęp do GitHuba, bo `deploy.sh` robi `git pull`. Dla prywatnego repo użyj HTTPS z tokenem albo deploy key. Plik `.env` **nie musi** być tworzony ręcznie – generuje go workflow z sekretów (patrz niżej).
2. **Zainstaluj runnera** – w GitHub: Settings → Actions → Runners → New self-hosted runner (Linux). Postępuj zgodnie z podanymi komendami na serwerze (etykiety domyślne wystarczą). Potem zainstaluj go jako usługę:
   ```
   sudo ./svc.sh install && sudo ./svc.sh start
   ```
3. **Uprawnienia do Dockera** – użytkownik, na którym działa runner, musi być w grupie `docker` (`sudo usermod -aG docker <user>`).
4. **Zmienna repo `DEPLOY_PATH`** – w GitHub: Settings → Secrets and variables → Actions → Variables → New repository variable. Wartość to ścieżka do repo na serwerze, np. `/home/deploy/wim` (sprawdź: `cd ~/wim && pwd`).
5. **Sekrety i zmienne konfiguracyjne** – Settings → Secrets and variables → Actions:
   - Sekrety (Secrets): `API_KEY` (klucz OpenRouter), `EMBEDDING_MODEL` (nazwa modelu embeddingów).

   Przy każdym wdrożeniu workflow generuje `.env` na serwerze. `DJANGO_SECRET_KEY` i `POSTGRES_PASSWORD` są losowane przy pierwszym wdrożeniu i zachowywane w kolejnych – nie zmieniaj ich bez ręcznego działania na bazie. `DJANGO_ALLOWED_HOSTS` jest ustawione na `*` (tymczasowo; do zawężenia przed produkcją).

   **Uwaga:** zmiany w `.env` rób w workflow lub w sekretach GitHuba, bo plik jest nadpisywany przy każdym wdrożeniu.

Wynik każdego wdrożenia widać w zakładce Actions. Runner działa tylko dla tego repo, więc nikt spoza projektu nie uruchomi kodu na serwerze.

**Uwaga:** bez publicznego IP przeglądarki spoza sieci serwera nie wejdą na aplikację. Jeśli potrzebujesz dostępu z zewnątrz, rozwiązaniem bez otwierania portów jest tunel, np. Cloudflare Tunnel albo Tailscale Funnel.
