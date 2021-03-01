#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import timedelta

from airflow import DAG
from datetime import datetime
#  from airflow.operators.docker_operator import DockerOperator
from airflow.providers.docker.operators.docker import DockerOperator

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
         schedule_interval="5 * * * *",
         catchup=False) as dag:
    t1 = DockerOperator(
        task_id='tissue_8',
        image='mobydick.crs4.it:5000/slaid:'
        '0.9.2-ref_lazy-net-creation-tissue_model-extract_tissue_eddl_1.1',
        api_version='auto',
        auto_remove=True,
        force_pull=True,
        user='root',
        command=[
            'parallel', '-l', '8', '-f', 'tissue_8', '-o',
            '/mnt/tdm-dic/slaid/airflow', '--scheduler',
            'tdmnode03.crs4.it:8786', '--overwrite',
            'mnt/tdm-dic/users/cesco/o/slides/AN0021-01.mrxs'
        ],
        volumes=['/mnt/tdm-dic:/mnt/tdm-dic'],
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge")
