#!/usr/bin/env bash

sed  "s|AIRFLOW_HOME_PLACEHOLDER|$(pwd)/data|g" env.template > .env
source .env

mkdir -p $PREDICTIONS_DIR
chmod a+w $PREDICTIONS_DIR

mkdir -p $INPUT_DIR
chmod a+w $INPUT_DIR

mkdir -p $STAGE_DIR
chmod a+w $STAGE_DIR

mkdir -p $FAILED_DIR
chmod a+w $FAILED_DIR
