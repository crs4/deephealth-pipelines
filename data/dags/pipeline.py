#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import time
from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.decorators import task
from airflow.models import DagRun, Variable
from airflow.operators.python import get_current_context
from airflow.utils import timezone
from airflow.utils.types import DagRunType

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

with DAG('pipeline', default_args=default_args,
         schedule_interval=None) as dag:

    @task
    def register_to_omeseadragon():
        incoming_files = get_current_context()['params']['slides']
        for fname in incoming_files:
            requests.get(Variable.get('OME_SEADRAGON_REGISTER_SLIDE'),
                         params={'slide_name': os.path.splitext(fname)[0]})

    @task
    def trigger_predictions():
        incoming_files = get_current_context()['params']['slides']
        params_to_update = get_current_context()['params']['params']
        mode = params_to_update.get('mode') or Variable.get('PREDICTIONS_MODE')
        if mode == 'serial':
            params = Variable.get('SERIAL_PREDICTIONS_PARAMS',
                                  deserialize_json=True)
        else:
            params = Variable.get('PARALLEL_PREDICTIONS_PARAMS',
                                  deserialize_json=True)

        params.update(params_to_update)
        for fname in incoming_files:
            params['slide']['path'] = fname
            execution_date = timezone.utcnow()
            triggered_run_id = DagRun.generate_run_id(DagRunType.MANUAL,
                                                      execution_date)
            triggered_run_id = f'{fname}-{triggered_run_id}'

            logger.info('triggering dag with id %s', triggered_run_id)
            trigger_dag(dag_id='predictions',
                        run_id=triggered_run_id,
                        execution_date=execution_date,
                        conf={'job': params},
                        replace_microseconds=False)
            time.sleep(1)

    register_to_omeseadragon() >> trigger_predictions()
