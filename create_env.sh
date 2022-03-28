#!/usr/bin/env bash

echoerr() { echo "$@" 1>&2; }

if [ ! -f .env ]; then
  sed  "s|AIRFLOW_HOME_PLACEHOLDER|$(pwd)/data|g" env.template > .env
else
   echoerr ".env found, skip creation"
fi

source .env

if [ ! -f promort_config/config.yaml ]; then
  cp promort_config/config.yaml.template promort_config/config.yaml
  sed  -i "s|PROMORT_DB|${PROMORT_DB}|g" promort_config/config.yaml
  sed  -i "s|PROMORT_USER|${PROMORT_USER}|g" promort_config/config.yaml
  sed  -i "s|PROMORT_PASSWORD|${PROMORT_PASSWORD}|g" promort_config/config.yaml
  sed  -i "s|PROMORT_SESSION_ID|${PROMORT_SESSION_ID}|g" promort_config/config.yaml
else
   echoerr "promort conf found, skip creation"
fi

mkdir -p $PREDICTIONS_DIR
chmod a+w $PREDICTIONS_DIR

mkdir -p $INPUT_DIR
chmod a+w $INPUT_DIR

mkdir -p $FAILED_DIR
chmod a+w $FAILED_DIR

mkdir -p $BACKUP_DIR
chmod a+w $BACKUP_DIR

CWL_AIRFLOW_DIR=build/cwl-airflow
if [ ! -d $CWL_AIRFLOW_DIR ]; then
  git clone https://github.com/mdrio/cwl-airflow.git $CWL_AIRFLOW_DIR
  cd $CWL_AIRFLOW_DIR
  git checkout "airflow-2.1.4"
  cd -
else
   echoerr "cwl aiflow found, skip cloning"
fi

cd scripts/prov_crate
docker build . -t prov_crate
cd -

cd scripts/provenance
docker build . -t dh/provenance

docker pull ubuntu:20.04

if [ ! -z "$PROMORT_IMG" ]; then
  docker pull ${PROMORT_IMG}
fi


if [ ! -z "$PROMORT_TOOLS_REPO" ]; then
  cd build/promort_tools-docker
  docker build -t $PROMORT_TOOLS_IMG --build-arg PROMORT_TOOLS_REPO=$PROMORT_TOOLS_REPO --build-arg PROMORT_TOOLS_BRANCH=$PROMORT_TOOLS_BRANCH .
  cd -
else
  docker pull ${PROMORT_TOOLS_IMG}
fi
