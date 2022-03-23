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
    expected_inputs = [
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
    assert len(inputs) == len(expected_inputs)
    assert set(inputs) == set(expected_inputs)

    outputs = [out.name for out in workflow.outputs()]
    expected_outputs = ["tissue", "tumor"]
    assert len(outputs) == len(expected_outputs)
    assert set(outputs) == set(expected_outputs)

    steps = workflow.steps()

    assert set([s.name for s in steps]) == set(
        ["classify-tumor", "extract-tissue-high", "extract-tissue-low"]
    )

    expected_steps = {
        "extract-tissue-low": {
            "batch-size": workflow.inputs("tissue-low-batch-size"),
            "chunk-size": workflow.inputs("tissue-low-chunk-size"),
            "gpu": workflow.inputs("gpu"),
            "label": workflow.inputs("tissue-low-label"),
            "level": workflow.inputs("tissue-low-level"),
            "src": workflow.inputs("slide"),
        },
        "extract-tissue-high": {
            "batch": workflow.inputs("tissue-high-batch-size"),
            "chunk": workflow.inputs("tissue-high-chunk-size"),
            "gpu": workflow.inputs("gpu"),
            "label": workflow.inputs("tissue-high-label"),
            "level": workflow.inputs("tissue-high-level"),
            "src": workflow.inputs("slide"),
            "filter": workflow.inputs("tissue-high-filter"),
            "filter_slide": workflow.nodes("extract-tissue-low/tissue"),
        },
        "classify-tumor": {
            "batch-size": workflow.inputs("tumor-batch-size"),
            "chunk-size": workflow.inputs("tumor-chunk-size"),
            "gpu": workflow.inputs("gpu"),
            "label": workflow.inputs("tumor-label"),
            "level": workflow.inputs("tumor-level"),
            "src": workflow.inputs("slide"),
            "filter": workflow.inputs("tumor-filter"),
            "filter_slide": workflow.nodes("extract-tissue-low/tissue"),
        },
    }
    assert (
        workflow.steps("extract-tissue-low").in_binding
        == expected_steps["extract-tissue-low"]
    )

    assert (
        workflow.steps("extract-tissue-high").in_binding
        == expected_steps["extract-tissue-high"]
    )
    assert (
        workflow.steps("classify-tumor").in_binding == expected_steps["classify-tumor"]
    )
