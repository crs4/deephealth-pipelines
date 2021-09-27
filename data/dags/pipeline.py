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
from typing import Dict, List, Tuple

import requests
from airflow.api.common.experimental.trigger_dag import trigger_dag
from airflow.decorators import task
from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from airflow.models import DagRun, Variable
from airflow.operators.python import get_current_context
from airflow.utils import timezone
from airflow.utils.state import State
from airflow.utils.task_group import TaskGroup
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


PROMORT_CONNECTION = BaseHook.get_connection('promort')
PREDICTIONS_DIR = Variable.get('PREDICTIONS_DIR')

PROMORT_TOOLS_IMG = 'lucalianas/promort_tools:dev'


def create_dag():
    with DAG('pipeline', default_args=default_args,
             schedule_interval=None) as dag:

        with TaskGroup(group_id='add_slide_to_backend'):
            slide_info_ = task_add_slide_to_omero()
            slide = slide_info_['slide']
            slide_to_promort = task_add_slide_to_promort(slide_info_)

        dag_info = task_predictions()
        slide_to_promort >> dag_info

        for prediction in Prediction:
            with TaskGroup(group_id=f'add_{prediction.value}_to_backend'):
                prediction_info = task(
                    task_add_prediction_to_omero,
                    task_id=f'add_{prediction.value}_to_omero')(
                        prediction.value, dag_info)
                prediction_label = prediction_info['label']
                omero_id = str(prediction_info['omero_id'])

                prediction_id = task(
                    task_add_prediction_to_promort,
                    task_id=f'add_{prediction.value}_to_promort')(
                        prediction.value, slide, prediction_label, omero_id)

                if prediction == Prediction.TUMOR:
                    tumor_branch(prediction_label, prediction, slide, omero_id)
                elif prediction == Prediction.TISSUE:
                    tissue_branch(prediction_label, prediction_id)
        return dag


@task(multiple_outputs=True)
def task_add_slide_to_omero() -> Dict[str, str]:
    slide = get_current_context()['params']['slide']
    slide_name = os.path.splitext(slide)[0]
    response = requests.get(OME_SEADRAGON_REGISTER_SLIDE,
                            params={'slide_name': slide_name})

    logger.info('response.text %s', response.text)
    response.raise_for_status()
    omero_id = response.json()['mirax_index_omero_id']

    return {'slide': slide, 'omero_id': omero_id}


@task
def task_predictions() -> Dict[str, str]:
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
            return {'dag_id': dag_id, 'dag_run_id': triggered_run_id}


@task
def task_add_slide_to_promort(slide_info: Dict[str, str]):

    slide = slide_info['slide']
    omero_id = slide_info['omero_id']
    command = [
        'docker', 'run', '--rm', PROMORT_TOOLS_IMG, 'importer.py', '--host',
        f'{PROMORT_CONNECTION.conn_type}://{PROMORT_CONNECTION.host}:{PROMORT_CONNECTION.port}',
        '--user', PROMORT_CONNECTION.login, '--passwd',
        PROMORT_CONNECTION.password, '--session-id', '***REMOVED***',
        'slides_importer', '--slide-label', slide, '--extract-case',
        '--omero-id',
        str(omero_id), '--mirax', '--omero-host', OME_SEADRAGON_URL,
        '--ignore-duplicated'
    ]
    subprocess.check_output(command, stderr=subprocess.PIPE)


def task_add_prediction_to_omero(prediction, dag_info) -> Dict[str, str]:
    dag_id, dag_run_id = dag_info['dag_id'], dag_info['dag_run_id']
    logger.info(
        'register prediction %s to omero with dag_id %s, dag_run_id %s',
        prediction, dag_id, dag_run_id)
    output_dir = get_output_dir(dag_id, dag_run_id)
    location = _get_prediction_location(prediction, output_dir)
    _move_prediction_to_omero_dir(location)
    return _register_prediction_to_omero(os.path.basename(location))


def task_add_prediction_to_promort(prediction, slide_label: str,
                                   prediction_label: str,
                                   omero_id: str) -> str:

    command = [
        'docker', 'run', '--rm', PROMORT_TOOLS_IMG, 'importer.py', '--host',
        f'{PROMORT_CONNECTION.conn_type}://{PROMORT_CONNECTION.host}:{PROMORT_CONNECTION.port}',
        '--user', PROMORT_CONNECTION.login, '--passwd',
        PROMORT_CONNECTION.password, '--session-id', '***REMOVED***',
        'predictions_importer', '--prediction-label', prediction_label,
        '--slide-label', slide_label, '--prediction-type',
        prediction.upper(), '--omero-id', omero_id
    ]

    logger.info('command %s', command)
    res = subprocess.check_output(command, stderr=subprocess.PIPE)
    return json.loads(res)['id']


@task
def task_convert_to_tiledb(dataset_label):

    command = [
        'docker', 'run', '--rm', '-v', f'{PREDICTIONS_DIR}:/data',
        PROMORT_TOOLS_IMG, 'zarr_to_tiledb.py', '--zarr-dataset',
        f'/data/{dataset_label}', '--out-folder', '/data'
    ]
    return run(command)


def tumor_branch(prediction_label, prediction, slide_label, omero_id):
    task_convert_to_tiledb(prediction_label) >> [
        task(_register_prediction_to_omero,
             task_id=f'add_{prediction.value}.tiledb_to_omero')
        (f'{prediction_label}.tiledb'),
        task(task_add_prediction_to_promort,
             task_id=f'add_{prediction.value}.tiledb_to_promort')
        (prediction.value, slide_label, f'{prediction_label}.tiledb', omero_id)
    ]


def tissue_branch(dataset_label, prediction_id):
    #  TODO add variable for threshold
    shapes = task_generate_roi(dataset_label)
    task_create_tissue_fragments(prediction_id, shapes)


@task(multiple_outputs=True)
def task_generate_roi(dataset_label) -> Dict:
    threshold = Variable.get('ROI_THRESHOLD')

    command = [
        'docker', 'run', '--rm', '-v', f'{PREDICTIONS_DIR}:/data',
        PROMORT_TOOLS_IMG, 'mask_to_shapes.py', f'/data/{dataset_label}', '-t',
        str(threshold), '--scale-func', 'fit'
    ]
    out = run(command)
    return json.loads(out)


@task
def task_create_tissue_fragments(prediction_id, shapes):
    command = [
        'docker', 'run', '--rm', PROMORT_TOOLS_IMG, 'importer.py', '--host',
        f'{PROMORT_CONNECTION.conn_type}://{PROMORT_CONNECTION.host}:{PROMORT_CONNECTION.port}',
        '--user', PROMORT_CONNECTION.login, '--passwd',
        PROMORT_CONNECTION.password, '--session-id', '***REMOVED***',
        'tissue_fragments_importer', '--prediction-id',
        str(prediction_id), '--shapes', f"{json.dumps(shapes)}"
    ]
    run(command)


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


def _move_prediction_to_omero_dir(location):
    basename = os.path.basename(location)
    shutil.copy(location, os.path.join(PREDICTIONS_DIR, basename))


def _register_prediction_to_omero(label):
    ome_seadragon_register_predictions = Variable.get(
        'OME_SEADRAGON_REGISTER_PREDICTIONS')

    response = requests.get(ome_seadragon_register_predictions,
                            params={
                                'dataset_label': label,
                                'keep_archive': True
                            })
    response.raise_for_status()
    res_json = response.json()

    logger.info(res_json)
    return res_json


def run(command):
    logger.info('command %s', command)
    out = subprocess.check_output(command, stderr=subprocess.PIPE).decode()
    logger.info('out %s', out)
    return out


def _get_prediction_location(prediction, output_dir):
    with open(os.path.join(output_dir, 'workflow_report.json'),
              'r') as report_file:
        report = json.load(report_file)

    return report[prediction]['location'].replace('file://', '')


dag = create_dag()
