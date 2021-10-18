#!/usr/bin/env bash
set -ex

cd /home/promort/app/ProMort/promort
python manage.py shell < /scripts/create_user.py
