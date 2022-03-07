import os
from unittest.mock import MagicMock, call, patch

import pytest
import responses
from responses import matchers
from slide_importer import __version__
from slide_importer.local import BaseClient, Client, SlideImporter


@pytest.fixture
def client():
    return Client("http://localhost", "user", "password")


@pytest.fixture
def dag_id():
    return "dag_id"


@pytest.fixture
def dag_run_id():
    return "dag_run_id"


@pytest.fixture
def slide_importer(client, tmp_path, rerun=None) -> SlideImporter:
    mock_client = MagicMock(client)
    mock_client.get_var.side_effect = lambda x: os.path.join(tmp_path, x)
    return SlideImporter(mock_client, rerun)


def test_version():
    assert __version__ == "0.1.0"


def response_get_var(url, name, value):
    return responses.Response(
        responses.GET,
        os.path.join(url, f"api/v1/variables/{name}"),
        json={"value": value},
        status=200,
    )


def response_run_pipeline(url, dag_id, dag_run_id, payload):
    return responses.Response(
        responses.POST,
        os.path.join(url, f"api/v1/dags/{dag_id}/dagRuns"),
        json={"dag_run_id": dag_run_id},
        status=200,
        match=[matchers.json_params_matcher(payload)],
    )


def response_get_state(url, dag_id, dag_run_id, state):
    return responses.Response(
        responses.GET,
        os.path.join(url, f"api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"),
        json={"state": state},
        status=200,
    )


@responses.activate
def test_client_get_var(client):
    var = "var"
    var_value = "var_value"
    responses.add(response_get_var(client.server_url, var, var_value))
    res = client.get_var(var)
    assert res == var_value
    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.url == f"{client.server_url}/api/v1/variables/{var}"
    )


@responses.activate
def test_client_run_pipeline(client, dag_id, dag_run_id):
    date = "2022"
    params = {"p": 1}
    conf = {"slide": "slide", "params": params}

    payload = {"dag_run_id": dag_run_id, "execution_date": date, "conf": conf}
    responses.add(response_run_pipeline(client.server_url, dag_id, dag_run_id, payload))
    res = client.run_pipeline(dag_id, dag_run_id, date, conf)
    assert res == dag_run_id

    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.url
        == f"{client.server_url}/api/v1/dags/{dag_id}/dagRuns"
    )


@responses.activate
def test_client_get_state(client, dag_id, dag_run_id):
    dag_id = "dag_id"
    dag_run_id = "dag_run_id"
    state = "running"
    responses.add(response_get_state(client.server_url, dag_id, dag_run_id, state))
    res = client.get_state(dag_id, dag_run_id)

    assert res == state
    assert len(responses.calls) == 1
    assert (
        responses.calls[0].request.url
        == f"{client.server_url}/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"
    )


@pytest.fixture
def dir_info(tmp_path):
    dir_info = {
        "input_dir": ["input_1.mrxs", "input_2.mrxs"],
        "stage_dir": ["stage_1.mrxs", "stage_2.mrxs"],
    }

    for dir_name, slides in dir_info.items():
        dir_name = os.path.join(tmp_path, dir_name)
        os.makedirs(dir_name)
        for slide in slides:
            open(os.path.join(dir_name, slide), "w")
            no_ext, ext = os.path.splitext(slide)
            if ext == ".mrxs":
                os.makedirs(os.path.join(dir_name, no_ext))

    return dir_info


def test_slide_importer(slide_importer, dag_id, dag_run_id, tmp_path, dir_info):
    slide_importer.import_slides()

    assert slide_importer.client.run_pipeline.call_count == len(dir_info["input_dir"])


@pytest.mark.parametrize("rerun", ["*", "stage_1"])
def test_slide_importer_rerun(slide_importer, dag_id, dag_run_id, dir_info, rerun):
    slide_importer.rerun = "*"
    slide_importer.import_slides()

    assert (
        slide_importer.client.run_pipeline.call_count == len(dir_info["stage_dir"])
        if rerun == "*"
        else 1
    )
