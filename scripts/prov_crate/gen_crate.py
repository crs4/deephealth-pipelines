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
from cwl_utils.parser import load_document_by_uri
from rocrate.rocrate import ROCrate
from rocrate.model.contextentity import ContextEntity
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


METADATA_BASENAME = "metadata.yaml"
WORKFLOW_NAME = "Promort tissue and tumor prediction"
WORKFLOW_VERSION = "0.1.0b1"
WORKFLOW_URL = "https://github.com/crs4/deephealth-pipelines"
WORKFLOW_LICENSE = "MIT"
TYPE_MAP = {
    "string": "Text",
    "int": "Number",
    "long": "Number",
    "float": "Number",
    "double": "Number",
    "File": "File",
}


def get_metadata(source):
    metadata_path = source / METADATA_BASENAME
    with open(metadata_path) as f:
        return yaml.load(f, Loader=Loader)


def get_params(source, metadata):
    params_path = source / metadata["params"]
    with open(params_path) as f:
        params = json.load(f)
    for k, v in params.items():
        if isinstance(v, dict) and v.get("class") == "File":
            params[k] = v["path"]
    return params


def get_workflow(source, metadata):
    workflow_path = source / metadata["workflow"]
    return load_document_by_uri(workflow_path)


def get_param_types(params, wf_def):
    rval = {}
    inputs_by_id = {_.id.rsplit("#", 1)[1]: _ for _ in wf_def.inputs}
    for k, v in params.items():
        in_ = inputs_by_id[k]
        t = in_.type
        if isinstance(t, list):
            t = [_ for _ in t if _ != "null"][0]
        rval[k] = TYPE_MAP[t]
    return rval


def add_action(crate, metadata):
    start_date = metadata["start_date"].isoformat()
    end_date = metadata["end_date"].isoformat()
    workflow = crate.mainEntity
    properties = {
        "@type": "CreateAction",
        "name": f"Promort prediction run on {start_date}",
        "startTime": start_date,
        "endTime": end_date,
    }
    action = crate.add(ContextEntity(crate, properties=properties))
    action["instrument"] = workflow
    return action


def add_params(params, param_types, metadata, source, crate, action):
    workflow = crate.mainEntity
    inputs, outputs, objects, results = [], [], [], []
    for k, v in params.items():
        in_ = crate.add(ContextEntity(crate, f"#param-{k}", properties={
            "@type": "FormalParameter",
            "name": k,
            "additionalType": param_types[k],
        }))
        inputs.append(in_)
        if isinstance(v, dict) and v.get("class") == "File":
            obj = crate.add_file(v["path"])
        else:
            obj = crate.add(ContextEntity(crate, f"#pv-{k}", properties={
                "@type": "PropertyValue",
                "additionalType": param_types[k],
                "name": k,
                "value": v,
            }))
        objects.append(obj)
    workflow["input"] = inputs
    action["object"] = objects
    for k, v in metadata["outs"].items():
        assert v["class"] == "File"
        assert k not in params  # so that IDs are unique
        out = crate.add(ContextEntity(crate, f"#param-{k}", properties={
            "@type": "FormalParameter",
            "name": k,
            "additionalType": "File",
        }))
        outputs.append(out)
        path = source / v["location"]
        assert path.is_file()
        res = crate.add_file(path, v["location"], properties={
            "contentSize": v["size"],
        })
        results.append(res)
    workflow["output"] = outputs
    action["result"] = results


def make_crate(source, out_dir):
    metadata = get_metadata(source)
    workflow_path = source / metadata["workflow"]
    crate = ROCrate(gen_preview=False)
    wf_def = get_workflow(source, metadata)
    workflow = crate.add_workflow(
        workflow_path, metadata["workflow"], main=True, lang="cwl",
        lang_version=wf_def.cwlVersion, gen_cwl=False
    )
    workflow["name"] = crate.root_dataset["name"] = WORKFLOW_NAME
    workflow["version"] = WORKFLOW_VERSION  # this should be in the report
    workflow["url"] = crate.root_dataset["isBasedOn"] = WORKFLOW_URL
    crate.root_dataset["license"] = WORKFLOW_LICENSE
    # No README.md for now
    action = add_action(crate, metadata)
    params = get_params(source, metadata)
    param_types = get_param_types(params, wf_def)
    add_params(params, param_types, metadata, source, crate, action)
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
