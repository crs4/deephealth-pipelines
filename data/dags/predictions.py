#!/usr/bin/env python
# -*- coding: utf-8 -*-
from cwl_airflow.extensions.cwldag import CWLDAG

dag = CWLDAG(workflow="/cwl/predictions.cwl",
             dag_id="predictions",
             concurrency=1)
