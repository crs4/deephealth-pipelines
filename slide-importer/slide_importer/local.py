#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import shutil
import sys
import time
from getpass import getpass
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
    def __init__(self, server_url: str, user: str, password: str, wait: bool = False):
        self.server_url = server_url
        self._user = user
        self._password = password
        self._stage_dir = self._get_stage_dir()
        self.wait = wait

    def _get_stage_dir(self):
        response = requests.get(
            os.path.join(self.server_url, "api/v1/variables/stage"),
            auth=HTTPBasicAuth(self._user, self._password),
        )
        response.raise_for_status()
        return response.json()["value"]

    def import_slides(self, slides: Path, params: Dict = None) -> int:
        params = params or {}
        slides = [slides] if not slides.is_dir() else list(slides.iterdir())
        faiures = 0
        for slide in self._cp_files(slides):
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
        payload = {
            "dag_run_id": f"predictions-{now.isoformat()}",
            "execution_date": now.isoformat(),
            "conf": {"slide": slide.name, "params": params},
        }
        logger.debug("trigger dag with payload %s", payload)
        dag_id = "pipeline"
        response = requests.post(
            os.path.join(self.server_url, f"api/v1/dags/{dag_id}/dagRuns"),
            auth=HTTPBasicAuth(self._user, self._password),
            headers={"Content-type": "application/json"},
            json=payload,
        )
        logger.debug(response.json())
        response.raise_for_status()
        if self.wait:
            dag_run_id = requests.utils.quote(response.json()["dag_run_id"])
            self._check_completion(slide, dag_id, dag_run_id)

    def _check_completion(self, slide, dag_id, dag_run_id):
        state = "running"
        while state == "running":
            time.sleep(10)
            response = requests.get(
                os.path.join(
                    self.server_url, f"api/v1/dags/{dag_id}/dagRuns/{dag_run_id}"
                ),
                auth=HTTPBasicAuth(self._user, self._password),
                headers={"Content-type": "application/json"},
            )
            response.raise_for_status()
            state = response.json()["state"]
        if state != "success":
            raise PipelineFailure(f"pipeline failed for slide {slide}")
        logger.info("pipeline run SUCCESSFULLY for slide %s", slide)

    def _cp_files(self, slides: List[Path]) -> List[Path]:
        logger.info("copying files %s to stage", slides)
        for slide in slides:
            if not slide.is_dir():
                yield copy_slide(slide, self._stage_dir)


def main(
    slides_path: str,
    *,
    server_url: str,
    user: str,
    log_level: str = "info",
    params: (str, "p") = None,
    wait: bool = False,
):
    """
    :params params: json containing params to override when running
    predictions on the imported slide. For debug only.
    """
    params = json.loads(params) if params else {}
    logging.basicConfig()
    logger.setLevel(getattr(logging, log_level.upper()))
    password = getpass()
    failures = SlideImporter(server_url, user, password, wait).import_slides(
        Path(slides_path), params
    )
    sys.exit(failures)


if __name__ == "__main__":
    clize.run(main)
