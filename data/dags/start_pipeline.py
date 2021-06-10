#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import time
from datetime import datetime, timedelta

import requests
import yaml
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.decorators import task
from airflow.models import DagRun, Variable
from airflow.operators.python import get_current_context
from airflow.utils import timezone
from airflow.utils.types import DagRunType

from airflow import DAG

JOB_CONF = \
    """
slide:
  class: File
  path: 
tissue-low-level: 8
tissue-low-label: tissue_low
tissue-high-level: 0
tissue-low-chunk: 256
tissue-high-label: tissue_high
tissue-high-filter: "tissue_low>0.8"
tissue-high-chunk: 1536
tumor-chunk: 1536
gpu: 0


tumor-level: 0
tumor-label: tumor
tumor-filter: 'tissue_low>0.8'
    """

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

with DAG('start_pipeline', default_args=default_args,
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
        logger.info("incoming_files %s", incoming_files)
        params = yaml.safe_load(JOB_CONF)
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
