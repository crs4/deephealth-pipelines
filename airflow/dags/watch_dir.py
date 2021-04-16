#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import time
from datetime import datetime, timedelta

import yaml
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.decorators import task
from airflow.models import DagRun, Variable
#  from airflow.operators.bash import BashOperator
from airflow.operators.python import get_current_context
from airflow.utils import timezone
from airflow.utils.types import DagRunType

from airflow import DAG

logger = logging.getLogger('watch-dir')
logger.setLevel = logging.INFO
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'start_date': datetime(2019, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG('watch_dir', default_args=default_args,
         schedule_interval=None) as dag:

    @task
    def trigger_predictions():
        incoming_files = get_current_context()['params']['slides']
        logger.info("incoming_files %s", incoming_files)
        stage = Variable.get('stage')
        output = Variable.get('output')
        with open('dags/predictions.yml') as f:
            params = yaml.load(f)
        for fname in incoming_files:
            if not os.path.isdir(os.path.join(stage, fname)):

                params['slide'] = {'dirname': stage, 'filename': fname}
                params['output'] = output
                execution_date = timezone.utcnow()
                triggered_run_id = DagRun.generate_run_id(
                    DagRunType.MANUAL, execution_date)
                triggered_run_id = f'{fname}-{triggered_run_id}'

                logger.info('triggering dag with id %s', triggered_run_id)
                trigger_dag(dag_id='predictions',
                            run_id=triggered_run_id,
                            execution_date=execution_date,
                            conf=params,
                            replace_microseconds=False)
                time.sleep(1)

    trigger_predictions()
