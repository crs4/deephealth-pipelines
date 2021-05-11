#!/usr/bin/env bash

sed  "s|AIRFLOW_HOME_PLACEHOLDER|$(pwd)/data|g" env.template > .env
