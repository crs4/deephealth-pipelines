#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import subprocess
from datetime import datetime, timedelta

import yaml

from airflow import DAG
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.decorators import task
from airflow.operators.python import get_current_context
from airflow.operators.bash import BashOperator

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
                             filepath='{{ dag_run["conf"]["dropbox"] }}')

    move_files = BashOperator(
        task_id='move_files',
        bash_command=
        'mv {{ dag_run["conf"]["dropbox"] }}/* {{ dag_run["conf"]["stage"] }}')

    @task
    def trigger_dag():
        ctx = get_current_context()
        dirname = ctx['params']['stage']
        output_dir = ctx['params']['output']
        with open('dags/predictions.yml') as f:
            params = yaml.load(f)
        for fname in os.listdir(dirname):
            params['slide'] = {'path': os.path.join(dirname, fname)}
            params['output'] = output_dir
            subprocess.check_call([
                'airflow', 'dags', 'trigger', 'predictions', '-c',
                json.dumps(params)
            ])

    file_sensor >> move_files >> trigger_dag()
