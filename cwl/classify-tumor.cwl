#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: parallel
requirements:
  InlineJavascriptRequirement: {}
  DockerRequirement:
    dockerPull: mobydick.crs4.it:5000/slaid:0.30.3-develop-tumor_model-classify_tumor_eddl_0.1 
  InitialWorkDirRequirement:
    listing:
      - entry:  $(inputs.src)
      # - entry:  $(inputs.filter_slide)
      #   writable: true
inputs:
  src:
    type: File
    inputBinding:
      position: 1
  level:
    type: int
    inputBinding:
      prefix: -l
  label:
    type: string
    inputBinding:
      prefix: -f
  filter_slide:
    type: Directory
    inputBinding:
      prefix: --filter-slide
  filter:
    type: string
    inputBinding:
      prefix: -F

arguments: [ '--overwrite','-o', $(runtime.outdir)]
outputs:
  tumor:
    type: Directory
    outputBinding:
      glob: '$(inputs.src.basename).zarr'
