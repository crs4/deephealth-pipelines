#!/usr/bin/env bash
source .env
docker-compose -p ${PROJECT}  -f docker-compose.yaml -f docker-compose.proxy.yaml  -f docker-compose.backend.yaml $@
