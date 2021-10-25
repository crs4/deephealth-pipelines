#!/usr/bin/env bash

set -eu

echo "-- Apply migrations --"
python ./manage.py migrate
