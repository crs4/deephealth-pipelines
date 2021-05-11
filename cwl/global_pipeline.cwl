#!/usr/bin/env cwl-runner

cwlVersion: v1.1
class: Workflow

inputs:
  slide: File
  tissue-low-level: int
  tissue-low-label: string

  tissue-high-level: int
  tissue-high-label: string
  tissue-high-filter: string

  tumor-level: int
  tumor-label: string
  tumor-filter: string

  gpu: int?

outputs:
  tissue:
    type: File
    outputSource: zip-tissue/out
  tumor:
    type: File
    outputSource: zip-tumor/out

steps:
  extract-tissue-low:
    run: &extract_tissue
      cwlVersion: v1.1
      class: CommandLineTool
      baseCommand: parallel
      requirements:
        InlineJavascriptRequirement: {}
        DockerRequirement:
          dockerPull: slaid:0.40.0-fix_filter-slide-tissue_model-extract_tissue_eddl_1.1
        InitialWorkDirRequirement:
          listing:
            -  $(inputs.src)
      inputs:
        src:
          type: File
          inputBinding:
            position: 1
          secondaryFiles:
            - pattern: |-
                ${
                  if (self.nameext == '.mrxs') {
                    return {
                    class: "File",
                    location: self.location.match(/.*\//)[0] + "/" + self.nameroot,
                    basename: self.nameroot};
                  }
                  else return null;
                }
              required: false
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
          type: string?
          inputBinding:
            prefix: -F
        gpu:
          type: int?
          inputBinding:
            prefix: --gpu
      arguments: ['--overwrite','-o', $(runtime.outdir)]
      outputs:
        tissue:
          type: Directory
          outputBinding:
            glob: '$(inputs.src.basename).zarr'
            outputEval: ${self[0].basename=inputs.label + '.zarr'; return self;}

    in:
      src: slide
      level: tissue-low-level
      label: tissue-low-label
      gpu: gpu
    out: [tissue]

  extract-tissue-high:
    run: *extract_tissue
    in:
      src: slide
      level: tissue-high-level
      label: tissue-high-label
      filter_slide: extract-tissue-low/tissue
      filter: tissue-high-filter
      gpu: gpu
    out: [tissue]


  classify-tumor:
    run: 
      cwlVersion: v1.1
      class: CommandLineTool
      baseCommand: parallel
      requirements:
        InlineJavascriptRequirement: {}
        DockerRequirement:
          dockerPull: slaid:0.40.0-fix_filter-slide-tumor_model-classify_tumor_eddl_0.1
        InitialWorkDirRequirement:
          listing:
            -  $(inputs.src)
      inputs:
        src:
          type: File
          inputBinding:
            position: 1
          secondaryFiles:
            - pattern: |-
                ${
                  if (self.nameext == '.mrxs') {
                    return {
                    class: "File",
                    location: self.location.match(/.*\//)[0] + "/" + self.nameroot,
                    basename: self.nameroot};
                  }
                  else return null;
                }
              required: false

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
          type: string?
          inputBinding:
            prefix: -F
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
            outputEval: ${self[0].basename=inputs.label + '.zarr'; return self;}
    in:
      src: slide
      level: tumor-level
      label: tumor-label
      filter_slide: extract-tissue-low/tissue
      filter: tumor-filter
      gpu: gpu
    out:
      [tumor]
  
  zip-tissue:
    run: &zip
      cwlVersion: v1.1
      class: CommandLineTool
      baseCommand: python3
      inputs:
        src:
          type: Directory
          loadListing: deep_listing
      arguments:
        - -m
        - zipfile
        - -c
        - $(inputs.src.basename).zip
        - $(inputs.src.listing)
      outputs:
        out:
          type: File
          outputBinding:
            glob: $(inputs.src.basename).zip
    in:
      src: extract-tissue-high/tissue
    out: 
      [out]

  zip-tumor:
    run: *zip
    in:
      src: classify-tumor/tumor
    out: 
      [out]
