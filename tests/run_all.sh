#!/usr/bin/env bash
set -eoux
./rocrate.sh
./integration.sh
./importer.sh
