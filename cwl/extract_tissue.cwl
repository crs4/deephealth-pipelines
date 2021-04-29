#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: CommandLineTool
baseCommand: parallel
requirements:
  # NetworkAccess:
  #   networkAccess: true
  # InitialWorkDirRequirement:
  #   listing:
  #     - $(inputs.src)
    #   - class: Directory
    #     location: $("file://" + inputs.src.dirname)
      # - entry: |-
      #     ${
      #     return {
      #       class: "Directory",
      #       location: inputs.src.location.match(/.*\//)[0] + "/" + inputs.src.nameroot};
      #     }
  InlineJavascriptRequirement: {}
  DockerRequirement:
    dockerPull: ***REMOVED***:5000/slaid:0.30.0-develop-tissue_model-extract_tissue_eddl_1.1
    # dockerOutputDirectory: /home/mauro/venvs
  # InplaceUpdateRequirement:
  #   inplaceUpdate: true
  InitialWorkDirRequirement:
    listing:
      -  $(inputs.src)
      # - entry: $(inputs.src)
      #   entryname: $(inputs.src.basename)
      #   writable: True
      # - entry: |-
      #     ${
      #     return {
      #       class: "File",
      #       location: inputs.src.location.match(/.*\//)[0] + "/" + inputs.src.nameroot,
      #       basename: inputs.src.nameroot};
      #     }
      #
      #   entryname: /data/$(inputs.src.nameroot)
      # - entry: $(runtime.outdir)
      #   entryname: ${ return runtime.outdir}
      #   writable: true
      # - entry: "$({class: 'Directory', listing:[], basename: inputs.outdir.basename})"
      #   entryname: /test
      #   writable: true
inputs:
  src:
    type: File
    inputBinding:
      position: 1
    # secondaryFiles:
    #   - pattern: |-
    #       ${
    #       return {
    #         class: "File",
    #         location: self.location.match(/.*\//)[0] + "/" + self.nameroot,
    #         basename: self.nameroot};
    #       }
    #     required: false
    #
  level:
    type: int
    inputBinding:
      prefix: -l
  label:
    type: string
    inputBinding:
      prefix: -f
  # outdir:
  #   type: Directory
  #   inputBinding:
  #     prefix: -o


# arguments: ["-o", $(runtime.outdir)]
arguments: ['--overwrite','-o', $(runtime.outdir)]

outputs:
  tissue:
    type: Directory
    outputBinding:
      # glob: '$(inputs.src.basename).zarr'
      glob: '*.zarr'
