cwlVersion: v1.1
class: Workflow

inputs:
  slide: File
  tissue-low-level: int
  tissue-low-label: string
  tissue-low-chunk-size: int?
  tissue-low-batch-size: int?

  tissue-high-level: int
  tissue-high-label: string
  tissue-high-filter: string
  tissue-high-chunk-size: int?
  tissue-high-batch-size: int?

  tumor-chunk-size: int?
  tumor-level: int
  tumor-label: string
  tumor-filter: string
  tumor-batch-size: int?

  gpu: int?

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
          dockerPull: mdrio/slaid:1.0.0-beta.13-tissue_model-eddl_2-cudnn

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
            prefix: -L
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
        chunk-size:
          type: int?
        batch-size:
          type: int?

      arguments: ["fixed-batch","-o", $(runtime.outdir), '--writer', 'zip']
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
      chunk-size: tissue-low-chunk-size
      batch-size: tissue-low-batch-size
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
      chunk: tissue-high-chunk-size
      batch: tissue-high-batch-size
    out: [tissue]


  classify-tumor:
    run: 
      cwlVersion: v1.1
      class: CommandLineTool
      requirements:
        InlineJavascriptRequirement: {}
        DockerRequirement:
          dockerPull: mdrio/slaid:1.0.0-beta.13-tumor_model-level_1-cudnn
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
            prefix: -L
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
        chunk-size:
          type: int?
        batch-size:
          type: int?

      arguments: ["fixed-batch","-o", $(runtime.outdir), '--writer', 'zip']
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
      chunk-size: tumor-chunk-size
      batch-size: tumor-batch-size
    out:
      [tumor]
