#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import subprocess
import time
from datetime import datetime, timedelta
from typing import Dict

import requests
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.decorators import task
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.models import DagRun, Variable
from airflow.operators.python import get_current_context
from airflow.utils import timezone
from airflow.utils.state import State
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

with DAG('pipeline', default_args=default_args, schedule_interval=None) as dag:

    @task(multiple_outputs=True)
    def register_to_omeseadragon() -> Dict[str, str]:
        slide = get_current_context()['params']['slide']
        slide_name = os.path.splitext(slide)[0]
        response = requests.get(Variable.get('OME_SEADRAGON_REGISTER_SLIDE'),
                                params={'slide_name': slide_name})
        response.raise_for_status()
        omero_id = response.json()['mirax_index_omero_id']

        return {'slide': slide_name, 'omero_id': omero_id}

    @task
    def trigger_predictions(slide):
        allowed_states = [State.SUCCESS]
        failed_states = [State.FAILED]
        params_to_update = get_current_context()['params']['params']
        mode = params_to_update.get('mode') or Variable.get('PREDICTIONS_MODE')
        if mode == 'serial':
            params = Variable.get('SERIAL_PREDICTIONS_PARAMS',
                                  deserialize_json=True)
        else:
            params = Variable.get('PARALLEL_PREDICTIONS_PARAMS',
                                  deserialize_json=True)

        params.update(params_to_update)
        params['slide']['path'] = slide
        execution_date = timezone.utcnow()
        triggered_run_id = DagRun.generate_run_id(DagRunType.MANUAL,
                                                  execution_date)
        triggered_run_id = f'{slide}-{triggered_run_id}'

        logger.info('triggering dag with id %s', triggered_run_id)
        dag_id = 'predictions'
        dag_run = trigger_dag(dag_id=dag_id,
                              run_id=triggered_run_id,
                              execution_date=execution_date,
                              conf={'job': params},
                              replace_microseconds=False)
        while True:
            time.sleep(60)

            dag_run.refresh_from_db()
            state = dag_run.state
            if state in failed_states:
                raise AirflowException(
                    f"{dag_id} failed with failed states {state}")
            if state in allowed_states:
                return dag_id, triggered_run_id

    @task
    def import_slide_to_promort(slide_info: Dict[str, str]):
        connection = BaseHook.get_connection('promort')

        slide = slide_info['slide']
        omero_id = slide_info['omero_id']
        image = 'lucalianas/promort_tools:dev'
        command = [
            'docker', 'run', '--rm', image, 'importer.py', '--host',
            f'{connection.conn_type}://{connection.host}:{connection.port}',
            '--user', connection.login, '--passwd', connection.password,
            '--session-id', 'promort-dev_sessionid', 'slides_importer',
            '--slide-label', slide, '--extract-case', '--omero-id',
            str(omero_id), '--mirax', '--omero-host',
            'http://mobydick.crs4.it:8090'
        ]
        subprocess.check_output(command)

    slide_info_ = register_to_omeseadragon()
    #  trigger_predictions(slide_)
    import_slide_to_promort(slide_info_)
