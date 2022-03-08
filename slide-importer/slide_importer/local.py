#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import shutil
import sys
import time
from dataclasses import dataclass
from collections import defaultdict
from getpass import getpass
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

import clize
import pytz
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger("local-importer")

_registry = {}


def copy_slide(slide_path: Path, dest: Path) -> Path:
    return _registry.get(slide_path.suffix[1:], SlideCopy)(slide_path).to(dest)


class PipelineFailure(Exception):
    ...


class SlideCopy:
    def __init_subclass__(cls, name, **kwargs):
        _registry[name] = cls

    def __init__(self, slide_path: Path):
        self.slide_path = slide_path

    def to(self, dest_dir: Path) -> Path:
        dest_path = Path(dest_dir, self.slide_path.name)
        self._cp(self.slide_path.absolute().as_posix(), dest_path.absolute().as_posix())
        return dest_path

    def _cp(self, src, dest, as_tree=False):
        func = shutil.copytree if as_tree else shutil.copy
        try:
            func(src, dest)
        except (FileExistsError, shutil.SameFileError):
            logger.warning("src %s already exists", src)


class MRXSCopy(SlideCopy, name="mrxs"):
    def to(self, dest_dir: Path) -> Path:
        dest_path = Path(dest_dir, self.slide_path.stem)
        self._cp(
            Path(self.slide_path.parent.absolute(), self.slide_path.stem)
            .absolute()
            .as_posix(),
            dest_path,
            True,
        )
        return super().to(dest_dir)


class SlideImporter:
    def __init__(
        self,
        client: "BaseClient",
        wait: bool = False,
        re_run: str = None,
    ):
        self.client = client
        self._stage_dir = self._get_stage_dir()
        self._input_dir = self._get_input_dir()
        self.wait = wait
        self.re_run = re_run

    def _get_stage_dir(self):
        return self.client.get_var("stage_dir")

    def _get_input_dir(self):
        return self.client.get_var("input_dir")

    def import_slides(self, params: Dict = None) -> int:
        params = params or {}
        source_dir = self._stage_dir if self.re_run else self._input_dir
        pattern = self.re_run or "*"
        slides = list(Path(source_dir).glob(pattern))
        faiures = 0
        for slide in self._iter_slides(slides):
            logger.info("Processing slide %s", slide)
            try:
                self._run_pipeline(slide, params)
            except PipelineFailure as ex:
                logger.error(ex)
                faiures += 1
        return faiures

    def _run_pipeline(self, slide: Path, params: Dict):
        now = datetime.datetime.now()
        timezone = pytz.timezone("Europe/Rome")
        now = timezone.localize(now)
        date = now.isoformat()
        dag_run_id = f"{slide.name}-{date}"
        conf = {"slide": slide.name, "params": params}
        dag_id = "pipeline"
        dag_run_id = self.client.run_pipeline(dag_id, dag_run_id, date, conf)

        if self.wait:
            self._check_completion(slide, dag_id, dag_run_id)

    def _check_completion(self, slide, dag_id, dag_run_id):
        state = "running"
        while state == "running":
            time.sleep(10)
            state = self.client.get_state(dag_id, dag_run_id)

        if state != "success":
            raise PipelineFailure(f"pipeline failed for slide {slide}")
        logger.info("pipeline run SUCCESSFULLY for slide %s", slide)

    def _iter_slides(self, slides: List[Path]) -> List[Path]:
        for slide in slides:
            logger.info("slide %s slide.is_dir() %s", slide.as_posix(), slide.is_dir())
            if not slide.is_dir() and slide.exists():
                yield slide


class BaseClient(ABC):
    @abstractmethod
    def run_pipeline(self, dag_id: str, dag_run_id, date: str, conf: Dict) -> str:
        ...

    @abstractmethod
    def get_var(self, name: str) -> str:
        ...

    @abstractmethod
    def get_state(self, dag_id, dag_run_id):
        ...


@dataclass
class Client(BaseClient):
    server_url: str
    user: str
    password: str

    def run_pipeline(self, dag_id: str, dag_run_id, date: str, conf: Dict) -> str:
        payload = {"dag_run_id": dag_run_id, "execution_date": date, "conf": conf}

        response = requests.post(
            os.path.join(self.server_url, f"api/v1/dags/{dag_id}/dagRuns"),
            auth=HTTPBasicAuth(self.user, self.password),
            headers={"Content-type": "application/json"},
            json=payload,
        )
        logger.debug(response.json())
        response.raise_for_status()
        dag_run_id = requests.utils.quote(response.json()["dag_run_id"])
        return dag_run_id

    def get_var(self, name: str) -> str:
        response = requests.get(
            os.path.join(self.server_url, f"api/v1/variables/{name}"),
            auth=HTTPBasicAuth(self.user, self.password),
        )
        response.raise_for_status()
        return response.json()["value"]

    def get_state(self, dag_id, dag_run_id):
        response = requests.get(
            os.path.join(self.server_url, f"api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"),
            auth=HTTPBasicAuth(self.user, self.password),
            headers={"Content-type": "application/json"},
        )
        response.raise_for_status()
        state = response.json()["state"]
        return state


def main(
    *,
    server_url: str,
    user: str,
    log_level: str = "info",
    params: (str, "p") = None,
    wait: bool = False,
    password: (str, "P") = None,
    re_run: str = None,
):
    """
    :params params: json containing params to override when running
    predictions on the imported slide. For debug only.
    """
    params = json.loads(params) if params else {}
    logging.basicConfig()
    logger.setLevel(getattr(logging, log_level.upper()))
    password = password or getpass()
    failures = SlideImporter(
        Client(server_url, user, password), wait, re_run=re_run
    ).import_slides(params)
    sys.exit(failures)


if __name__ == "__main__":
    clize.run(main)
