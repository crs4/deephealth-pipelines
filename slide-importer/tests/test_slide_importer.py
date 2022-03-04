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


def test_slide_importer(slide_importer, dag_id, dag_run_id, tmp_path):
    prepare_dir(tmp_path)
    assert slide_importer.client.get_var.call_count == 2
    slide_importer.client.get_var.assert_any_call("stage_dir")
    slide_importer.client.get_var.assert_any_call("input_dir")

    slide_importer.import_slides()

    assert slide_importer.client.run_pipeline.call_count == 2


@pytest.fixture
def dir_with_data(tmp_path):
    stage_dir = os.path.join(tmp_path, "stage_dir")
    input_dir = os.path.join(tmp_path, "input_dir")

    os.makedirs(stage_dir)
    os.makedirs(input_dir)

    open(os.path.join(input_dir, "a.mrxs"), "a")
    open(os.path.join(input_dir, "b.mrxs"), "a")
    os.makedirs(os.path.join(input_dir, "a"))
    os.makedirs(os.path.join(input_dir, "b"))

    open(os.path.join(stage_dir, "c.mrxs"), "a")
    os.makedirs(os.path.join(stage_dir, "c"))
    return tmp_path


def test_slide_importer_rerun(slide_importer, dag_id, dag_run_id, dir_with_data):
    slide_importer.rerun = "*"
    assert slide_importer.client.get_var.call_count == 2
    slide_importer.client.get_var.assert_any_call("stage_dir")
    slide_importer.client.get_var.assert_any_call("input_dir")

    slide_importer.import_slides()

    assert slide_importer.client.run_pipeline.call_count == 1
