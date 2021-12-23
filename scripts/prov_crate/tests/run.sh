#!/usr/bin/env bash
set -eoux

pip install -r ../requirements.txt
python ../gen_crate.py data -o out
[[ -f out/predictions.cwl ]]
[[ -f out/ro-crate-metadata.json ]]
[[ -f out/tissue_high.zip ]]
[[ -f out/tumor.zip ]]
rm -r out

