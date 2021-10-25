#!/usr/bin/env bash

set -eu

GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
WORKERS_TIMEOUT="${WORKERS_TIMEOUT:-120}"

echo "-- Starting gunicorn --"
exec gunicorn promort.wsgi:application \
     --bind 0.0.0.0:8080 \
     --workers "$GUNICORN_WORKERS" \
     --timeout "$WORKERS_TIMEOUT"
