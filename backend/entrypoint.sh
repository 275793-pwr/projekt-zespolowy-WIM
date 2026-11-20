#!/bin/sh
set -e
python manage.py migrate --noinput
# jeden worker: wbudowana Chroma (sqlite) nie może być współdzielona przez wiele procesów
exec gunicorn config.wsgi:application -b 0.0.0.0:8000 --workers 1 --threads 8 --timeout 600
