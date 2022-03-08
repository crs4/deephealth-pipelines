#!/usr/bin/env bash
set -eoux
./rocrate.sh
./importer.sh
./integration.sh
