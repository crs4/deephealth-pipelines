#!/usr/bin/env bash

./create_env.sh
source .env
./compose.sh up -d

running=$(docker-compose ps --services --filter "status=running" | grep init)
while [ $running ]; do
  echo waiting for init to complete
  sleep 5
  running=$(docker-compose ps --services --filter "status=running" | grep init)
done

cp -r tests/data/Mirax2-Fluorescence-2* $INPUT_DIR

cd slide-importer
poetry install
poetry shell
python slide_importer/local.py  --user $AIRFLOW_USER -P $AIRFLOW_PASSWORD --server-url http://localhost:8080  -p '{ "tissue-high-level": 8, "tissue-high-filter": "tissue_low>1", "tumor-filter": "tissue_low>1", "gpu": null,"tumor-chunk": 1024}' --wait
