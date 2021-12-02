#!/usr/bin/env bash
set -x


check_omeseadragon (){
  docker run --network deephealth curlimages/curl $1
  echo $?
}

poetry shell
./create_env.sh
cat promort_config/config.yaml
source .env
./compose.sh up -d

cp -r tests/data/Mirax2-Fluorescence-2* $INPUT_DIR
ls -la $INPUT_DIR

running=$(docker-compose ps --services --filter "status=running" | grep init)
while [ $running ]; do
  echo waiting for init to complete
  sleep 5
  running=$(docker-compose ps --services --filter "status=running" | grep init)
done
deactivate

ome_sedragon_status=$(check_omeseadragon $OME_SEADRAGON_URL)

echo $ome_sedragon_status
while [ $ome_sedragon_status -ne 0 ]; do
  echo waiting for omeseadragon to be up and running
  sleep 5
  ome_sedragon_status=$(check_omeseadragon $OME_SEADRAGON_URL)
done

./compose.sh ps

cd slide-importer
poetry install
poetry shell
set -e
python slide_importer/local.py  --user $AIRFLOW_USER -P $AIRFLOW_PASSWORD --server-url http://localhost:8080  -p '{ "tissue-high-level": 8, "tissue-high-filter": "tissue_low>1", "tumor-filter": "tissue_low>1", "gpu": null,"tumor-chunk": 1024}' --wait
