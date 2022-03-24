#!/usr/bin/env bash

set -eoux

cd ../scripts/provenance/
pip install -r requirements.txt
pip install -r requirements-dev.txt
python3 -m pytest

