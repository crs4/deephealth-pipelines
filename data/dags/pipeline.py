#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Tuple

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

OME_SEADRAGON_REGISTER_SLIDE = Variable.get('OME_SEADRAGON_REGISTER_SLIDE')
OME_SEADRAGON_URL = Variable.get('OME_SEADRAGON_URL')

PROMORT_TOOLS_IMG = 'lucalianas/promort_tools:dev'


class Prediction(Enum):
    TISSUE = 'tissue'
    TUMOR = 'tumor'


def get_prediction_path(prediction: Prediction, dag_id: str,
                        dag_run_id: str) -> str:
    output_dir = get_output_dir(dag_id, dag_run_id)

    with open(os.path.join(output_dir, 'workflow_report.json'),
              'r') as report_file:
        report = json.load(report_file)

    return report[prediction.value]['location'].replace('file://', '')


def get_output_dir(dag_id, dag_run_id):
    return os.path.join(Variable.get('OUT_DIR'), dag_id,
                        dag_run_id).replace(':', '_').replace('+', '_')


with DAG('pipeline', default_args=default_args, schedule_interval=None) as dag:

    @task(multiple_outputs=True)
    def register_slide_to_omeseadragon() -> Dict[str, str]:
        slide = get_current_context()['params']['slide']
        slide_name = os.path.splitext(slide)[0]
        response = requests.get(OME_SEADRAGON_REGISTER_SLIDE,
                                params={'slide_name': slide_name})

        logger.info('response.text %s', response.text)
        response.raise_for_status()
        omero_id = response.json()['mirax_index_omero_id']

        return {'slide': slide, 'omero_id': omero_id}

    @task
    def trigger_predictions() -> Tuple[str, str]:
        slide = get_current_context()['params']['slide']
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
            time.sleep(10)

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
        command = [
            'docker', 'run', '--rm', PROMORT_TOOLS_IMG, 'importer.py',
            '--host',
            f'{connection.conn_type}://{connection.host}:{connection.port}',
            '--user', connection.login, '--passwd', connection.password,
            '--session-id', 'promort-dev_sessionid', 'slides_importer',
            '--slide-label', slide, '--extract-case', '--omero-id',
            str(omero_id), '--mirax', '--omero-host', OME_SEADRAGON_URL,
            '--ignore-duplicated'
        ]
        subprocess.check_output(command, stderr=subprocess.PIPE)

    @task
    def register_predictions_to_omero(dag_info):
        dag_id, dag_run_id = dag_info
        output_dir = get_output_dir(dag_id, dag_run_id)
        predictions_dir = Variable.get('PREDICTIONS_DIR')
        ome_seadragon_register_predictions = Variable.get(
            'OME_SEADRAGON_REGISTER_PREDICTIONS')

        with open(os.path.join(output_dir, 'workflow_report.json'),
                  'r') as report_file:
            report = json.load(report_file)

        res = {}
        for prediction in ['tissue', 'tumor']:
            location = report[prediction]['location'].replace('file://', '')
            basename = os.path.basename(location)
            shutil.copy(location, os.path.join(predictions_dir, basename))

            response = requests.get(ome_seadragon_register_predictions,
                                    params={
                                        'dataset_label': basename,
                                        'keep_archive': True
                                    })
            response.raise_for_status()
            res[prediction] = response.json()

        logger.info(res)
        return res

    @task
    def import_predictions_to_promort(slide_info: Dict[str, str],
                                      predictions_info: Dict[str, str]):

        slide = slide_info['slide']
        connection = BaseHook.get_connection('promort')
        for prediction_name, data in predictions_info.items():
            command = [
                'docker', 'run', '--rm', PROMORT_TOOLS_IMG, 'importer.py',
                '--host',
                f'{connection.conn_type}://{connection.host}:{connection.port}',
                '--user', connection.login, '--passwd', connection.password,
                '--session-id', 'promort-dev_sessionid',
                'predictions_importer', '--prediction-label', data['label'],
                '--slide-label', slide, '--prediction-type',
                prediction_name.upper(), '--omero-id',
                str(data['omero_id'])
            ]

            logger.info('command %s', command)
            subprocess.check_output(command, stderr=subprocess.PIPE)

    slide_info_ = register_slide_to_omeseadragon()
    dag_info = trigger_predictions()
    slide_to_promort = import_slide_to_promort(slide_info_)
    slide_to_promort >> dag_info
    predictions_info = register_predictions_to_omero(dag_info)
    import_predictions_to_promort(slide_info_, predictions_info)
