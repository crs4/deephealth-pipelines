#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import logging
import os
import shutil
from getpass import getpass
from pathlib import Path
from typing import Dict, List

import clize
import pytz
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger()

_registry = {}


def copy_slide(slide_path: Path, dest: Path) -> Path:
    return _registry.get(slide_path.suffix[1:], SlideCopy)(slide_path).to(dest)


class SlideCopy:
    def __init_subclass__(cls, name, **kwargs):
        _registry[name] = cls

    def __init__(self, slide_path: Path):
        self.slide_path = slide_path

    def to(self, dest_dir: Path) -> Path:
        dest_path = Path(dest_dir, self.slide_path.name)
        shutil.copy(self.slide_path.absolute().as_posix(),
                    dest_path.absolute().as_posix())
        return dest_path


class MRXSCopy(SlideCopy, name='mrxs'):
    def to(self, dest_dir: Path) -> Path:
        dest_path = Path(dest_dir, self.slide_path.stem)
        shutil.copytree(
            Path(self.slide_path.parent.absolute(),
                 self.slide_path.stem).absolute().as_posix(), dest_path)
        return super().to(dest_dir)


class SlideImporter:
    def __init__(self, server_url: str, user: str, password: str):
        self.server_url = server_url
        self._user = user
        self._password = password
        self._stage_dir = self._get_stage_dir()

    def _get_stage_dir(self):
        response = requests.get(os.path.join(self.server_url,
                                             'api/v1/variables/stage'),
                                auth=HTTPBasicAuth(self._user, self._password))
        response.raise_for_status()
        return response.json()['value']

    def import_slides(self, slides: Path, params: Dict = None):
        params = params or {}
        for slide in self._cp_files(slides):
            self._trigger_predictions(slide, params)

    def _trigger_predictions(self, slide: Path, params: Dict):
        now = datetime.datetime.now()
        timezone = pytz.timezone("Europe/Rome")
        now = timezone.localize(now)
        payload = {
            "dag_run_id": f"predictions-{now.isoformat()}",
            "execution_date": now.isoformat(),
            "conf": {
                'slides': [slide.name],
                'params': params
            }
        }
        logger.debug('trigger dag with payload %s', payload)
        response = requests.post(os.path.join(self.server_url,
                                              'api/v1/dags/pipeline/dagRuns'),
                                 auth=HTTPBasicAuth(self._user,
                                                    self._password),
                                 headers={'Content-type': 'application/json'},
                                 json=payload)
        logger.debug(response.json())
        response.raise_for_status()

    def _cp_files(self, slides: Path) -> List[Path]:
        logger.info('copying files %s to stage', slides)
        slides = [slides] if not slides.is_dir() else slides.iterdir()
        for slide in slides:
            if not slide.is_dir():
                yield copy_slide(slide, self._stage_dir)


def main(slides_path: str,
         *,
         server_url: str,
         user: str,
         log_level: str = 'info',
         params: (str, 'p') = None):
    """
    :params params: json containing params to override when running
    predictions on the imported slide
    """
    params = json.loads(params) if params else {}
    logging.basicConfig()
    logger.setLevel(getattr(logging, log_level.upper()))
    password = getpass()
    SlideImporter(server_url, user,
                  password).import_slides(Path(slides_path), params)


if __name__ == '__main__':
    clize.run(main)
