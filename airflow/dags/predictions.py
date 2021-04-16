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
    'retry_delay': timedelta(minutes=1),
}
base_image = '***REMOVED***:5000/slaid:0.30.0-develop'
tissue_image = f'{base_image}-tissue_model-extract_tissue_eddl_1.1'
tumor_image = f'{base_image}-tumor_model-promort_vgg16_weights_ep_41_vacc_0.91'
network = 'deephealth-pipelines_default'
with DAG('predictions',
         default_args=default_args,
         schedule_interval=None,
         catchup=False) as dag:

    tissue_low_res = DockerOperator(
        task_id='tissue_low_res',
        image=tissue_image,
        api_version='auto',
        auto_remove=True,
        force_pull=True,
        user='root',
        command=
        'parallel  -f tissue_8 -o {{ dag_run.conf["output"] }} --overwrite'
        ' {{ "--gpu" if "gpu" in dag_run.conf else ""  }} '
        ' {{ dag_run.conf["gpu"] if "gpu" in dag_run.conf  else ""  }} '
        ' {{ "-b" if "tissue-batch" in dag_run.conf else ""  }} '
        ' {{ dag_run.conf["tissue-batch"] if "tissue-batch" in dag_run.conf  else ""  }} '
        ' {{ "-l" if "tissue-level" in dag_run.conf else ""  }} '
        ' {{ dag_run.conf["tissue-level"] if "tissue-level" in dag_run.conf  else ""  }} '
        ' {{ "--scheduler"   if "scheduler"  in dag_run.conf else "" }} '
        ' {{   dag_run.conf["scheduler"] if "scheduler"  in dag_run.conf else "" }} '
        ' {{ dag_run.conf["slide"]["dirname"] }}/{{ dag_run.conf["slide"]["filename"] }}',
        volumes=['/mnt/tdm-dic:/mnt/tdm-dic'],
        docker_url="unix://var/run/docker.sock",
        network_mode=network)

    tissue_high_res = DockerOperator(
        task_id='tissue_high_res',
        image=tissue_image,
        api_version='auto',
        auto_remove=True,
        force_pull=True,
        user='root',
        command='parallel  -f tissue -o {{ dag_run.conf["output"] }} --overwrite'
        ' {{ "--gpu" if "gpu" in dag_run.conf else ""  }} '
        ' {{ dag_run.conf["gpu"] if "gpu" in dag_run.conf  else ""  }} '
        ' -F "{{ dag_run.conf["tissue-label"]   }}>0.1" '
        ' -l 0'
        ' -T 1024 '
        ' -b 1000000 '
        ' {{ "--scheduler"   if "scheduler"  in dag_run.conf else "" }} '
        ' {{   dag_run.conf["scheduler"] if "scheduler"  in dag_run.conf else "" }} '
        ' {{ dag_run.conf["output"] }}/{{ dag_run.conf["slide"]["filename"] }}.zarr',
        volumes=['/mnt/tdm-dic:/mnt/tdm-dic'],
        docker_url="unix://var/run/docker.sock",
        network_mode=network)

    tumor = DockerOperator(
        task_id='tumor',
        image=base_image,
        api_version='auto',
        auto_remove=True,
        force_pull=True,
        user='root',
        command=
        'parallel  -f {{ dag_run.conf["tumor-label"] }} -o {{ dag_run.conf["output"] }} --overwrite'
        ' -m /home/mauro/slaid/slaid/resources/models/tumor_model-classify_tumor_eddl_0.1.bin  '
        ' {{ "--gpu" if "gpu" in dag_run.conf else ""  }} '
        ' {{ dag_run.conf["gpu"] if "gpu" in dag_run.conf  else ""  }} '
        ' -T 1024 '
        ' -b 1000000 '
        ' -F "{{ dag_run.conf["tissue-label"]   }}>0.6" '
        ' -l {{ dag_run.conf["tumor-level"] }}'
        ' {{ "--scheduler"   if "scheduler"  in dag_run.conf else "" }} '
        ' {{   dag_run.conf["scheduler"] if "scheduler"  in dag_run.conf else "" }} '
        ' {{ dag_run.conf["output"] }}/{{ dag_run.conf["slide"]["filename"] }}.zarr',
        volumes=['/mnt/tdm-dic:/mnt/tdm-dic'],
        docker_url="unix://var/run/docker.sock",
        network_mode=network)

    tissue_low_res >> [tumor, tissue_high_res]
