#!/usr/bin/env bash
# Wdrożenie na własnym serwerze. Uruchamiaj w katalogu repozytorium na serwerze:
#   ./deploy/deploy.sh            # pobierz zmiany z gita, zbuduj i uruchom
#   ./deploy/deploy.sh --no-pull  # bez git pull (np. wgrałeś kod innym sposobem)
#
# Wymagania na serwerze: git, docker z pluginem compose (v2+), curl.
set -euo pipefail

cd "$(dirname "$0")/.."

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
PULL=1
[[ "${1:-}" == "--no-pull" ]] && PULL=0

log()  { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mBŁĄD:\033[0m %s\n' "$*" >&2; exit 1; }

# 1. Plik .env musi istnieć i nie może mieć wartości domyślnych
[[ -f .env ]] || die "Brak pliku .env. Skopiuj .env.example do .env i uzupełnij (patrz README)."

check_var() {
  local name="$1" bad="$2"
  local value
  value="$(grep -E "^${name}=" .env | tail -n1 | cut -d= -f2- || true)"
  [[ -n "$value" ]] || die "Zmienna ${name} jest pusta w .env."
  if [[ -n "$bad" && "$value" == *"$bad"* ]]; then
    die "Zmienna ${name} ma wartość domyślną/testową (\"${bad}\"). Ustaw własną wartość w .env."
  fi
}
check_var API_KEY "replace-me"
check_var DJANGO_SECRET_KEY "change-me"
check_var POSTGRES_PASSWORD "zesp"
check_var DJANGO_ALLOWED_HOSTS ""

if ! grep -qE '^DJANGO_DEBUG=0' .env; then
  die "W .env ustaw DJANGO_DEBUG=0 na serwerze produkcyjnym."
fi

# 2. Kod z repozytorium
if [[ $PULL -eq 1 ]]; then
  log "Pobieranie zmian z gita (git pull --ff-only)"
  git pull --ff-only
fi

# 3. Budowa i uruchomienie
log "Budowanie obrazów"
"${COMPOSE[@]}" build

log "Uruchamianie usług"
"${COMPOSE[@]}" up -d --remove-orphans

# 4. Sprawdzenie zdrowia: aplikacja odpowiada przez nginx na /api/
PORT="$(grep -E '^HTTP_PORT=' .env | cut -d= -f2- || true)"
PORT="${PORT:-80}"
log "Czekam na aplikację na porcie ${PORT}"
for _ in $(seq 1 60); do
  if curl -fsS -o /dev/null "http://localhost:${PORT}/"; then
    log "Aplikacja odpowiada."
    "${COMPOSE[@]}" ps
    exit 0
  fi
  sleep 2
done

die "Aplikacja nie odpowiada po 2 minutach. Sprawdź logi: docker compose -f docker-compose.yml -f docker-compose.prod.yml logs --tail=100"
