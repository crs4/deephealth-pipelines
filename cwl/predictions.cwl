#!/usr/bin/env cwl-runner

cwlVersion: v1.1
class: Workflow

inputs:
  slide: File
  tissue-low-level: int
  tissue-low-label: string
  tissue-low-chunk: int?
  tissue-low-batch: int?

  tissue-high-level: int
  tissue-high-label: string
  tissue-high-filter: string
  tissue-high-chunk: int?
  tissue-high-batch: int?

  tumor-chunk: int?
  tumor-level: int
  tumor-label: string
  tumor-filter: string
  tumor-batch: int?

  gpu: int?
  mode: string?

outputs:
  tissue:
    type: File
    outputSource: extract-tissue-high/tissue
  tumor:
    type: File
    outputSource: classify-tumor/tumor

steps:
  extract-tissue-low:
    run: &extract_tissue
      cwlVersion: v1.1
      class: CommandLineTool
      requirements:
        InlineJavascriptRequirement: {}
        DockerRequirement:
          dockerPull: slaid:0.60.4-develop-tissue_model-extract_tissue_eddl_1.1
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
          type: File?
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
        chunk:
          type: int?
          inputBinding:
            prefix: --chunk
        batch:
          type: int?
          inputBinding:
            prefix: --batch
        mode:
          type: string?
          inputBinding:
            prefix: --mode

      arguments: ["-o", $(runtime.outdir), '--writer', 'zip']
      outputs:
        tissue:
          type: File
          outputBinding:
            glob: '$(inputs.src.basename).zip'
            outputEval: ${self[0].basename=inputs.label + '.zip'; return self;}

    in:
      src: slide
      level: tissue-low-level
      label: tissue-low-label
      gpu: gpu
      chunk: tissue-low-chunk
      batch: tissue-low-batch
      mode: mode
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
      chunk: tissue-high-chunk
      batch: tissue-high-batch
      mode: mode
    out: [tissue]


  classify-tumor:
    run: 
      cwlVersion: v1.1
      class: CommandLineTool
      requirements:
        InlineJavascriptRequirement: {}
        DockerRequirement:
          dockerPull: slaid:0.60.4-develop-tumor_model-classify_tumor_eddl_0.1
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
          type: File?
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
        chunk:
          type: int?
          inputBinding:
            prefix: --chunk
        batch:
          type: int?
          inputBinding:
            prefix: --batch
        mode:
          type: string?
          inputBinding:
            prefix: --mode

      arguments: ["-o", $(runtime.outdir), '--writer', 'zip']
      outputs:
        tumor:
          type: File
          outputBinding:
            glob: '$(inputs.src.basename).zip'
            outputEval: ${self[0].basename=inputs.label + '.zip'; return self;}
    in:
      src: slide
      level: tumor-level
      label: tumor-label
      filter_slide: extract-tissue-low/tissue
      filter: tumor-filter
      gpu: gpu
      chunk: tumor-chunk
      batch: tumor-batch
      mode: mode
    out:
      [tumor]
