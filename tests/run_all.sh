#!/usr/bin/env bash
set -eoux

./provenance.sh
./rocrate.sh
./importer.sh
./integration.sh
