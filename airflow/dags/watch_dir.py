#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import shutil
import time
from datetime import datetime, timedelta

import yaml
from typing import List
from airflow import DAG
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.contrib.sensors.file_sensor import FileSensor
from airflow.decorators import task
from airflow.models import DagRun
#  from airflow.operators.bash import BashOperator
from airflow.operators.python import get_current_context
from airflow.utils import timezone
from airflow.utils.state import State
from airflow.utils.types import DagRunType

logger = logging.getLogger('watch-dir')
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

    #  move_files = BashOperator(
    #      task_id='move_files',
    #      bash_command=
    #      'mv {{ dag_run["conf"]["dropbox"] }}/* {{ dag_run["conf"]["stage"] }}')

    @task
    def move_files() -> List[str]:
        ctx = get_current_context()
        dropbox = ctx['params']['dropbox']
        stage = ctx['params']['stage']
        incoming_files = os.listdir(dropbox)
        for fname in incoming_files:
            shutil.move(os.path.join(dropbox, fname), stage)
        return incoming_files

    @task
    def trigger_predictions(incoming_files: List[str]):
        ctx = get_current_context()
        stage = ctx['params']['stage']
        output_dir = ctx['params']['output']
        with open('dags/predictions.yml') as f:
            params = yaml.load(f)
        dag_runs = []
        for fname in incoming_files:
            params['slide'] = {'path': os.path.join(stage, fname)}
            params['output'] = output_dir

            execution_date = timezone.utcnow()
            run_id = DagRun.generate_run_id(DagRunType.MANUAL, execution_date)
            dag_runs.append(
                trigger_dag(
                    dag_id='predictions',
                    run_id=f'{fname}-{run_id}',
                    conf=params,
                ))
        completed = False
        while not completed:
            time.sleep(10)
            for dag_run in dag_runs:
                dag_run.refresh_from_db()
                state = dag_run.state
                logger.info('state of dag run %s: %s', dag_run, state)
                logger.info('dag_runs %s', dag_runs)
                if state in [State.SUCCESS, State.FAILED]:
                    if state == State.FAILED:
                        # TODO add logging
                        pass
                    dag_runs.remove(dag_run)
            if len(dag_runs) == 0:
                completed = True

    incoming_files = move_files()
    file_sensor >> incoming_files >> trigger_predictions(incoming_files)
