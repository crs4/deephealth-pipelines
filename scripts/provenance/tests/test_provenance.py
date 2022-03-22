#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import pytest
from provenance import NXWorkflowFactory
from cwl_utils.parser import load_document_by_uri


@pytest.fixture
def cwl_workflow():
    return load_document_by_uri("tests/data/predictions.cwl")


@pytest.fixture
def workflow(cwl_workflow):
    return NXWorkflowFactory(cwl_workflow).get()


def test_workflow(workflow):
    inputs = [_in.name for _in in workflow.inputs()]
    assert set(inputs) == set(
        [
            "gpu",
            "slide",
            "tissue-high-batch-size",
            "tissue-high-chunk-size",
            "tissue-high-filter",
            "tissue-high-label",
            "tissue-high-level",
            "tissue-low-batch-size",
            "tissue-low-chunk-size",
            "tissue-low-label",
            "tissue-low-level",
            "tumor-batch-size",
            "tumor-chunk-size",
            "tumor-filter",
            "tumor-label",
            "tumor-level",
        ]
    )

    outputs = [out.name for out in workflow.outputs()]
    assert set(outputs) == set(["tissue", "tumor"])
    steps = workflow.steps()
    assert set([s.name for s in steps]) == set(
        ["classify-tumor", "extract-tissue-high", "extract-tissue-low"]
    )

    tissue_low = workflow.steps("extract-tissue-low")
    assert tissue_low.in_binding == None

    #  assert provenance.slide == "test.mrxs"
    #  assert provenance.type_ == prediction
    #  assert provenance.params.model == "mdrio/slaid:1.0.0-tumor_model-level_1-cudnn"
    #  assert provenance.params.level == 1
    #  assert provenance.params.filter_ == "tissue_low>0.8"
