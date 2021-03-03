#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

#  from airflow.operators.docker_operator import DockerOperator
from airflow.providers.docker.operators.docker import DockerOperator

from airflow import DAG
# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['airflow@example.com'],
    'start_date': datetime(2018, 1, 3),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}
with DAG('predictions',
         default_args=default_args,
         schedule_interval=None,
         catchup=False) as dag:
    t1 = DockerOperator(
        task_id='tissue_8',
        image='***REMOVED***:5000/slaid:'
        '0.9.2-ref_lazy-net-creation-tissue_model-extract_tissue_eddl_1.1',
        api_version='auto',
        auto_remove=True,
        #  force_pull=True,
        user='root',
        command='parallel  -f tissue -o {{ dag_run.conf["output"] }} --overwrite'
        ' {{ "--gpu" if "gpu" in dag_run.conf else ""  }} '
        ' {{ dag_run.conf["gpu"] if "gpu" in dag_run.conf  else ""  }} '
        ' {{ "-b" if "tissue-batch" in dag_run.conf else ""  }} '
        ' {{ dag_run.conf["tissue-batch"] if "tissue-batch" in dag_run.conf  else ""  }} '
        ' {{ "-l" if "tissue-level" in dag_run.conf else ""  }} '
        ' {{ dag_run.conf["tissue-level"] if "tissue-level" in dag_run.conf  else ""  }} '
        ' {{ "--scheduler"   if "scheduler"  in dag_run.conf else "" }} '
        ' {{   dag_run.conf["scheduler"] if "scheduler"  in dag_run.conf else "" }} '
        ' {{ dag_run.conf["slide"]["path"] }}',
        volumes=['/mnt/tdm-dic:/mnt/tdm-dic'],
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge")
