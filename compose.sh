#!/usr/bin/env bash
docker-compose  -f docker-compose.yaml  -f docker-compose.omero.yaml -f docker-compose.promort.yaml  $@
