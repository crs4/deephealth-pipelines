#!/usr/bin/env bash
set -x
cd ../slide-importer
poetry install
poetry run pytest


