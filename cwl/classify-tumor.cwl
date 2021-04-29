#!/usr/bin/env cwl-runner

cwlVersion: v1.2
class: CommandLineTool
baseCommand: parallel
requirements:
  InlineJavascriptRequirement: {}
  DockerRequirement:
    dockerPull: slaid:0.9.0-develop-tumor_model-promort_vgg16_weights_ep_41_vacc_0.91
inputs:
  src:
    type: File
    inputBinding:
      position: 1
    # secondaryFiles:
    #   - pattern: |-
    #       ${
    #       return {
    #         class: "Directory",
    #         location: self.location.match(/.*\//)[0] + "/" + self.nameroot,
    #         basename: self.nameroot};
    #       }
    #     required: false

  level:
    type: int
    inputBinding:
      prefix: -l
  label:
    type: string
    inputBinding:
      prefix: -f
  filter_slide:
    type: Directory?
    inputBinding:
      prefix: --filter-slide
  filter:
    type: string
    inputBinding:
      prefix: -F?
  gpu:
    type: int?
    inputBinding:
      prefix: --gpu

arguments: ["-o", $(runtime.outdir), '-b', '1000000']
outputs:
  tumor:
    type: Directory
    outputBinding:
      glob: '$(inputs.src.basename).zarr'
