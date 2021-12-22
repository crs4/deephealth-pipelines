#!/usr/bin/env python

# Copyright (c) 2021 CRS4
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""\
Generate an RO-Crate for a workflow run.
"""

import argparse
import atexit
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

import yaml
from rocrate.rocrate import ROCrate
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


# hardwired in gather_report pipeline step
WORKFLOW_BASENAME = "predictions.cwl"
PARAMS_BASENAME = "params.json"
METADATA_BASENAME = "metadata.yaml"
WORKFLOW_NAME = "Promort tissue and tumor prediction"
WORKFLOW_VERSION = "0.1.0b1"
WORKFLOW_URL = "https://github.com/crs4/deephealth-pipelines"
WORKFLOW_LICENSE = "MIT"


def get_params(source):
    params_path = source / PARAMS_BASENAME
    with open(params_path) as f:
        return json.load(f)


def get_workflow(source):
    workflow_path = source / WORKFLOW_BASENAME
    with open(workflow_path) as f:
        return yaml.load(f, Loader=Loader)


def make_crate(source, out_dir):
    workflow_path = source / WORKFLOW_BASENAME
    crate = ROCrate(gen_preview=False)
    wf_def = get_workflow(source)
    workflow = crate.add_workflow(
        workflow_path, WORKFLOW_BASENAME, main=True, lang="cwl",
        lang_version=wf_def["cwlVersion"], gen_cwl=False
    )
    workflow["name"] = crate.root_dataset["name"] = WORKFLOW_NAME
    workflow["version"] = WORKFLOW_VERSION  # this should be in the report
    workflow["url"] = crate.root_dataset["isBasedOn"] = WORKFLOW_URL
    crate.root_dataset["license"] = WORKFLOW_LICENSE
    # No README.md for now
    # TODO: add metadata on parameters
    crate.write(out_dir)


def main(args):
    if zipfile.is_zipfile(args.run_report):
        source = tempfile.mkdtemp(prefix="gen_crate_")
        atexit.register(shutil.rmtree, source)
        with zipfile.ZipFile(args.run_report, "r") as zf:
            zf.extractall(source)
        source = Path(source)
    else:
        source = Path(args.run_report)
        if not source.is_dir():
            raise RuntimeError(
                "input must be either a zip file or a directory"
            )
    make_crate(source, args.out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("run_report", metavar="RUN_REPORT",
                        help="workflow run report dir or zip")
    parser.add_argument("-o", "--out-dir", metavar="DIR",
                        default="pipeline_run",
                        help="output RO-Crate directory")
    main(parser.parse_args())
