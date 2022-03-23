#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

import pytest
from provenance import NXWorkflowFactory, ArtefactFactory
from cwl_utils.parser import load_document_by_uri


@pytest.fixture
def cwl_workflow():
    return load_document_by_uri("tests/data/predictions.cwl")


@pytest.fixture
def workflow(cwl_workflow):
    return NXWorkflowFactory(cwl_workflow).get()


@pytest.fixture
def params():
    return json.load(open("tests/data/params.json", "r"))


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
    tissue_low = workflow.steps("extract-tissue-low")
    assert tissue_low.in_binding == expected_steps["extract-tissue-low"]
    assert tissue_low.command == None
    assert tissue_low.docker_image == "mdrio/slaid:1.0.0-tissue_model-eddl_2-cudnn"

    tissue_high = workflow.steps("extract-tissue-high")
    assert tissue_high.in_binding == expected_steps["extract-tissue-high"]
    assert tissue_high.command == None
    assert tissue_low.docker_image == "mdrio/slaid:1.0.0-tissue_model-eddl_2-cudnn"

    tumor = workflow.steps("classify-tumor")
    assert tumor.in_binding == expected_steps["classify-tumor"]
    assert tumor.command == None
    assert tumor.docker_image == "mdrio/slaid:1.0.0-tumor_model-level_1-cudnn"


def test_artefacts(workflow, params):
    artefact_factory = ArtefactFactory(workflow, params)
    artefacts = artefact_factory.get()
    assert len(artefacts) == 3

    tissue_low = artefact_factory.get("extract-tissue-low/tissue")

    assert tissue_low.workflow_step == workflow.steps("extract-tissue-low")
    expected_inputs = {
        "batch-size": None,
        "chunk-size": None,
        "gpu": 0,
        "label": "tissue_low",
        "level": 9,
        "src": {"class": "File", "path": "test.mrxs"},
    }
    assert tissue_low.inputs == expected_inputs
    assert tissue_low.command == None
    assert tissue_low.docker_image == "mdrio/slaid:1.0.0-tissue_model-eddl_2-cudnn"

    tumor = artefact_factory.get("tumor")
    assert tumor.name == "tumor"
    assert tumor.workflow_step == workflow.steps("classify-tumor")
    expected_inputs = {
        "batch-size": None,
        "chunk-size": None,
        "filter": "tissue_low>0.8",
        "gpu": 0,
        "label": "tumor",
        "level": 1,
        "src": {"class": "File", "path": "test.mrxs"},
        "filter_slide": tissue_low,
    }
    assert tumor.inputs == expected_inputs
    assert tumor.command == None
    assert tumor.docker_image == "mdrio/slaid:1.0.0-tumor_model-level_1-cudnn"

    tissue = artefact_factory.get("tissue")
    assert tissue.name == "tissue"
    assert tissue.workflow_step == workflow.steps("extract-tissue-high")
    expected_inputs = {
        "batch": None,
        "chunk": None,
        "filter": "tissue_low>0.1",
        "gpu": 0,
        "label": "tissue_high",
        "level": 4,
        "src": {"class": "File", "path": "test.mrxs"},
        "filter_slide": tissue_low,
    }
    assert tissue.inputs == expected_inputs
    assert tissue.command == None
    assert tissue.docker_image == "mdrio/slaid:1.0.0-tissue_model-eddl_2-cudnn"
