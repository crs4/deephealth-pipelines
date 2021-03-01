#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import subprocess
from datetime import datetime, timedelta

from airflow import DAG
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.decorators import task

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'start_date': datetime.now(),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG('watch_dir',
         default_args=default_args,
         schedule_interval=None,
         catchup=False) as dag:
    file_sensor = FileSensor(task_id="file_sensor",
                             poke_interval=5,
                             filepath="/opt/airflow/dags/inputs")

    @task
    def trigger_dag():
        dirname = "/opt/airflow/dags/inputs"
        for fname in os.listdir(dirname):
            print(fname)
            subprocess.call([
                'airflow', 'dags', 'trigger', 'predictions', '-c',
                json.dumps({'input': os.path.join(dirname, fname)})
            ])

    file_sensor >> trigger_dag()
