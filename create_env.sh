#!/usr/bin/env bash

sed  "s|AIRFLOW_HOME_PLACEHOLDER|$(pwd)/data|g" env.template > .env

source .env

cp promort_config/config.yaml.template promort_config/config.yaml

sed  -i "s|PROMORT_DB|${PROMORT_DB}|g" promort_config/config.yaml
sed  -i "s|PROMORT_USER|${PROMORT_USER}|g" promort_config/config.yaml
sed  -i "s|PROMORT_PASSWORD|${PROMORT_PASSWORD}|g" promort_config/config.yaml
sed  -i "s|PROMORT_SESSION_ID|${PROMORT_SESSION_ID}|g" promort_config/config.yaml

mkdir -p $PREDICTIONS_DIR
chmod a+w $PREDICTIONS_DIR

mkdir -p $INPUT_DIR
chmod a+w $INPUT_DIR

mkdir -p $STAGE_DIR
chmod a+w $STAGE_DIR

mkdir -p $FAILED_DIR
chmod a+w $FAILED_DIR

mkdir -p $BACKUP_DIR
chmod a+w $BACKUP_DIR

CWL_AIRFLOW_DIR=build/cwl-airflow
if [ ! -d $CWL_AIRFLOW_DIR ]; then
  git clone git@github.com:mdrio/cwl-airflow.git $CWL_AIRFLOW_DIR
fi

