#!/usr/bin/env python

# Copyright (c) 2025 CRS4
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
Generate a Workflow RO-Crate for the tissue-tumor prediction workflow.
"""

import argparse
from pathlib import Path
from urllib.parse import urlsplit

from cwl_utils.parser import load_document_by_uri
from rocrate.rocrate import ROCrate
from rocrate.model import ContextEntity, Person

THIS_DIR = Path(__file__).absolute().parent
WF_DIR = THIS_DIR.parent.parent / "cwl"
WF_PATH = WF_DIR / "predictions.cwl"
WORKFLOW_NAME = "Digital pathology tissue/tumor prediction"
WORKFLOW_URL = "https://github.com/crs4/deephealth-pipelines"
WORKFLOW_LICENSE = "MIT"
WROC_PROFILE_BASE_URL = "https://w3id.org/workflowhub/workflow-ro-crate"
WROC_PROFILE_VERSION = "1.0"
README = THIS_DIR / "README.md"
AUTHOR_NAME = "Mauro Del Rio"
AUTHOR_ID = "https://orcid.org/0000-0003-4934-128X"


def add_profile(crate):
    wroc_profile_id = f"{WROC_PROFILE_BASE_URL}/{WROC_PROFILE_VERSION}"
    profile = crate.add(ContextEntity(crate, wroc_profile_id, properties={
        "@type": "CreativeWork",
        "name": "Workflow RO-Crate",
        "version": WROC_PROFILE_VERSION,
    }))
    crate.root_dataset["conformsTo"] = profile


def make_crate(source, out_dir):
    crate = ROCrate(gen_preview=False)
    add_profile(crate)
    wf_def = load_document_by_uri(WF_PATH, load_all=True)
    workflow = crate.add_workflow(
        WF_PATH, main=True, lang="cwl", lang_version=wf_def.cwlVersion,
        gen_cwl=False
    )
    workflow["name"] = crate.root_dataset["name"] = WORKFLOW_NAME
    crate.root_dataset["description"] = WORKFLOW_NAME
    workflow["url"] = crate.root_dataset["isBasedOn"] = WORKFLOW_URL
    crate.root_dataset["license"] = WORKFLOW_LICENSE
    readme = crate.add_file(README)
    readme["about"] = crate.root_dataset
    readme["encodingFormat"] = "text/markdown"
    author = crate.add(Person(crate, AUTHOR_ID, properties={
        "name": AUTHOR_NAME
    }))
    crate.root_dataset["author"] = author
    for step in wf_def.steps:
        tool_path = Path(urlsplit(step.run).path)
        crate.add_file(tool_path, properties={
            "name": f"{tool_path.stem} CWL tool"
        })
    return crate


def main(args):
    output = Path(args.output)
    crate = make_crate(WF_DIR, output)
    if output.suffix == ".zip":
        crate.write_zip(output)
    else:
        crate.write(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-o", "--output", metavar="STRING",
                        default="tissue-tumor-predict.crate.zip",
                        help="output RO-Crate directory or zip file")
    main(parser.parse_args())
