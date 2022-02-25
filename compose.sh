#!/usr/bin/env bash
docker-compose  -f docker-compose.yaml -f docker-compose.override.yml  -f docker-compose.backend.yaml -f docker-compose.backend.override.yml $@
