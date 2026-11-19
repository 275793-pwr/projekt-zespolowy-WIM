#!/bin/sh
set -e
python manage.py migrate --noinput
# one worker: embedded Chroma (sqlite) must not be shared by several processes
exec gunicorn config.wsgi:application -b 0.0.0.0:8000 --workers 1 --threads 8 --timeout 600
