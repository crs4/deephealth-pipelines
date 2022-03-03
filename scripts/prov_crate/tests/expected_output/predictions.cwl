class: Workflow
cwlVersion: v1.2
http://commonwl.org/cwltool#original_cwlVersion: v1.1
id: file:///cwl/predictions.cwl
inputs:
- id: file:///cwl/predictions.cwl#gleason-batch-size
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#gleason-chunk-size
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#gleason-filter
  type: string
- id: file:///cwl/predictions.cwl#gleason-label
  type: string
- id: file:///cwl/predictions.cwl#gleason-level
  type: int
- id: file:///cwl/predictions.cwl#gpu
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#slide
  type: File
- id: file:///cwl/predictions.cwl#tissue-high-batch-size
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#tissue-high-chunk-size
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#tissue-high-filter
  type: string
- id: file:///cwl/predictions.cwl#tissue-high-label
  type: string
- id: file:///cwl/predictions.cwl#tissue-high-level
  type: int
- id: file:///cwl/predictions.cwl#tissue-low-batch-size
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#tissue-low-chunk-size
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#tissue-low-label
  type: string
- id: file:///cwl/predictions.cwl#tissue-low-level
  type: int
- id: file:///cwl/predictions.cwl#tumor-batch-size
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#tumor-chunk-size
  type:
  - 'null'
  - int
- id: file:///cwl/predictions.cwl#tumor-filter
  type: string
- id: file:///cwl/predictions.cwl#tumor-label
  type: string
- id: file:///cwl/predictions.cwl#tumor-level
  type: int
outputs:
- id: file:///cwl/predictions.cwl#gleason
  outputSource: file:///cwl/predictions.cwl#classify-gleason/gleason
  type: File
- id: file:///cwl/predictions.cwl#tissue
  outputSource: file:///cwl/predictions.cwl#extract-tissue-high/tissue
  type: File
- id: file:///cwl/predictions.cwl#tumor
  outputSource: file:///cwl/predictions.cwl#classify-tumor/tumor
  type: File
steps:
- id: file:///cwl/predictions.cwl#classify-gleason
  in:
  - id: file:///cwl/predictions.cwl#classify-gleason/batch-size
    source: file:///cwl/predictions.cwl#gleason-batch-size
  - id: file:///cwl/predictions.cwl#classify-gleason/chunk-size
    source: file:///cwl/predictions.cwl#gleason-chunk-size
  - id: file:///cwl/predictions.cwl#classify-gleason/filter
    source: file:///cwl/predictions.cwl#gleason-filter
  - id: file:///cwl/predictions.cwl#classify-gleason/filter_slide
    source: file:///cwl/predictions.cwl#extract-tissue-low/tissue
  - id: file:///cwl/predictions.cwl#classify-gleason/gpu
    source: file:///cwl/predictions.cwl#gpu
  - id: file:///cwl/predictions.cwl#classify-gleason/label
    source: file:///cwl/predictions.cwl#gleason-label
  - id: file:///cwl/predictions.cwl#classify-gleason/level
    source: file:///cwl/predictions.cwl#gleason-level
  - id: file:///cwl/predictions.cwl#classify-gleason/src
    source: file:///cwl/predictions.cwl#slide
  out:
  - file:///cwl/predictions.cwl#classify-gleason/gleason
  run:
    arguments:
    - fixed-batch
    - -o
    - $(runtime.outdir)
    - --writer
    - zip
    class: CommandLineTool
    cwlVersion: v1.1
    id: _:46b47f40-7a6c-4daf-a5f0-ef3cfb6c799b
    inputs:
    - id: file:///cwl/predictions.cwl#classify-gleason/run/batch-size
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#classify-gleason/run/chunk-size
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#classify-gleason/run/filter
      inputBinding:
        prefix: -F
      type:
      - 'null'
      - string
    - id: file:///cwl/predictions.cwl#classify-gleason/run/filter_slide
      inputBinding:
        prefix: --filter-slide
      type:
      - 'null'
      - File
    - id: file:///cwl/predictions.cwl#classify-gleason/run/gpu
      inputBinding:
        prefix: --gpu
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#classify-gleason/run/label
      inputBinding:
        prefix: -L
      type: string
    - id: file:///cwl/predictions.cwl#classify-gleason/run/level
      inputBinding:
        prefix: -l
      type: int
    - id: file:///cwl/predictions.cwl#classify-gleason/run/src
      inputBinding:
        position: 1
      secondaryFiles:
      - pattern: "${\n  if (self.nameext == '.mrxs') {\n    return {\n    class: \"\
          File\",\n    location: self.location.match(/.*\\//)[0] + \"/\" + self.nameroot,\n\
          \    basename: self.nameroot};\n  }\n  else return null;\n}"
        required: false
      type: File
    outputs:
    - id: file:///cwl/predictions.cwl#classify-gleason/run/gleason
      outputBinding:
        glob: $(inputs.src.basename).zip
        outputEval: ${self[0].basename=inputs.label + '.zip'; return self;}
      type: File
    requirements:
    - class: DockerRequirement
      dockerPull: crs4/slaid:1.1.0-beta.23-tumor_model-gleason-cudnn
    - class: InitialWorkDirRequirement
      listing:
      - $(inputs.src)
    - class: InlineJavascriptRequirement
- id: file:///cwl/predictions.cwl#classify-tumor
  in:
  - id: file:///cwl/predictions.cwl#classify-tumor/batch-size
    source: file:///cwl/predictions.cwl#tumor-batch-size
  - id: file:///cwl/predictions.cwl#classify-tumor/chunk-size
    source: file:///cwl/predictions.cwl#tumor-chunk-size
  - id: file:///cwl/predictions.cwl#classify-tumor/filter
    source: file:///cwl/predictions.cwl#tumor-filter
  - id: file:///cwl/predictions.cwl#classify-tumor/filter_slide
    source: file:///cwl/predictions.cwl#extract-tissue-low/tissue
  - id: file:///cwl/predictions.cwl#classify-tumor/gpu
    source: file:///cwl/predictions.cwl#gpu
  - id: file:///cwl/predictions.cwl#classify-tumor/label
    source: file:///cwl/predictions.cwl#tumor-label
  - id: file:///cwl/predictions.cwl#classify-tumor/level
    source: file:///cwl/predictions.cwl#tumor-level
  - id: file:///cwl/predictions.cwl#classify-tumor/src
    source: file:///cwl/predictions.cwl#slide
  out:
  - file:///cwl/predictions.cwl#classify-tumor/tumor
  run:
    arguments:
    - fixed-batch
    - -o
    - $(runtime.outdir)
    - --writer
    - zip
    class: CommandLineTool
    cwlVersion: v1.1
    id: _:cbc880b1-4738-45bf-98f6-415f3b878718
    inputs:
    - id: file:///cwl/predictions.cwl#classify-tumor/run/batch-size
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#classify-tumor/run/chunk-size
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#classify-tumor/run/filter
      inputBinding:
        prefix: -F
      type:
      - 'null'
      - string
    - id: file:///cwl/predictions.cwl#classify-tumor/run/filter_slide
      inputBinding:
        prefix: --filter-slide
      type:
      - 'null'
      - File
    - id: file:///cwl/predictions.cwl#classify-tumor/run/gpu
      inputBinding:
        prefix: --gpu
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#classify-tumor/run/label
      inputBinding:
        prefix: -L
      type: string
    - id: file:///cwl/predictions.cwl#classify-tumor/run/level
      inputBinding:
        prefix: -l
      type: int
    - id: file:///cwl/predictions.cwl#classify-tumor/run/src
      inputBinding:
        position: 1
      secondaryFiles:
      - pattern: "${\n  if (self.nameext == '.mrxs') {\n    return {\n    class: \"\
          File\",\n    location: self.location.match(/.*\\//)[0] + \"/\" + self.nameroot,\n\
          \    basename: self.nameroot};\n  }\n  else return null;\n}"
        required: false
      type: File
    outputs:
    - id: file:///cwl/predictions.cwl#classify-tumor/run/tumor
      outputBinding:
        glob: $(inputs.src.basename).zip
        outputEval: ${self[0].basename=inputs.label + '.zip'; return self;}
      type: File
    requirements:
    - class: DockerRequirement
      dockerPull: mdrio/slaid:1.0.0-tumor_model-level_1-cudnn
    - class: InitialWorkDirRequirement
      listing:
      - $(inputs.src)
    - class: InlineJavascriptRequirement
- id: file:///cwl/predictions.cwl#extract-tissue-high
  in:
  - id: file:///cwl/predictions.cwl#extract-tissue-high/batch
    source: file:///cwl/predictions.cwl#tissue-high-batch-size
  - id: file:///cwl/predictions.cwl#extract-tissue-high/chunk
    source: file:///cwl/predictions.cwl#tissue-high-chunk-size
  - id: file:///cwl/predictions.cwl#extract-tissue-high/filter
    source: file:///cwl/predictions.cwl#tissue-high-filter
  - id: file:///cwl/predictions.cwl#extract-tissue-high/filter_slide
    source: file:///cwl/predictions.cwl#extract-tissue-low/tissue
  - id: file:///cwl/predictions.cwl#extract-tissue-high/gpu
    source: file:///cwl/predictions.cwl#gpu
  - id: file:///cwl/predictions.cwl#extract-tissue-high/label
    source: file:///cwl/predictions.cwl#tissue-high-label
  - id: file:///cwl/predictions.cwl#extract-tissue-high/level
    source: file:///cwl/predictions.cwl#tissue-high-level
  - id: file:///cwl/predictions.cwl#extract-tissue-high/src
    source: file:///cwl/predictions.cwl#slide
  out:
  - file:///cwl/predictions.cwl#extract-tissue-high/tissue
  run:
    arguments:
    - fixed-batch
    - -o
    - $(runtime.outdir)
    - --writer
    - zip
    class: CommandLineTool
    cwlVersion: v1.1
    id: _:6e228cf9-f74b-4a1d-8bc2-d48279f5c02e
    inputs:
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/batch-size
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/chunk-size
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/filter
      inputBinding:
        prefix: -F
      type:
      - 'null'
      - string
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/filter_slide
      inputBinding:
        prefix: --filter-slide
      type:
      - 'null'
      - File
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/gpu
      inputBinding:
        prefix: --gpu
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/label
      inputBinding:
        prefix: -L
      type: string
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/level
      inputBinding:
        prefix: -l
      type: int
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/src
      inputBinding:
        position: 1
      secondaryFiles:
      - pattern: "${\n  if (self.nameext == '.mrxs') {\n    return {\n    class: \"\
          File\",\n    location: self.location.match(/.*\\//)[0] + \"/\" + self.nameroot,\n\
          \    basename: self.nameroot};\n  }\n  else return null;\n}"
        required: false
      type: File
    outputs:
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/tissue
      outputBinding:
        glob: $(inputs.src.basename).zip
        outputEval: ${self[0].basename=inputs.label + '.zip'; return self;}
      type: File
    requirements:
    - class: DockerRequirement
      dockerPull: mdrio/slaid:1.0.0-tissue_model-eddl_2-cudnn
    - class: InitialWorkDirRequirement
      listing:
      - $(inputs.src)
    - class: InlineJavascriptRequirement
- id: file:///cwl/predictions.cwl#extract-tissue-low
  in:
  - id: file:///cwl/predictions.cwl#extract-tissue-low/batch-size
    source: file:///cwl/predictions.cwl#tissue-low-batch-size
  - id: file:///cwl/predictions.cwl#extract-tissue-low/chunk-size
    source: file:///cwl/predictions.cwl#tissue-low-chunk-size
  - id: file:///cwl/predictions.cwl#extract-tissue-low/gpu
    source: file:///cwl/predictions.cwl#gpu
  - id: file:///cwl/predictions.cwl#extract-tissue-low/label
    source: file:///cwl/predictions.cwl#tissue-low-label
  - id: file:///cwl/predictions.cwl#extract-tissue-low/level
    source: file:///cwl/predictions.cwl#tissue-low-level
  - id: file:///cwl/predictions.cwl#extract-tissue-low/src
    source: file:///cwl/predictions.cwl#slide
  out:
  - file:///cwl/predictions.cwl#extract-tissue-low/tissue
  run:
    arguments:
    - fixed-batch
    - -o
    - $(runtime.outdir)
    - --writer
    - zip
    class: CommandLineTool
    cwlVersion: v1.1
    id: _:6e228cf9-f74b-4a1d-8bc2-d48279f5c02e
    inputs:
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/batch-size
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/chunk-size
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/filter
      inputBinding:
        prefix: -F
      type:
      - 'null'
      - string
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/filter_slide
      inputBinding:
        prefix: --filter-slide
      type:
      - 'null'
      - File
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/gpu
      inputBinding:
        prefix: --gpu
      type:
      - 'null'
      - int
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/label
      inputBinding:
        prefix: -L
      type: string
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/level
      inputBinding:
        prefix: -l
      type: int
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/src
      inputBinding:
        position: 1
      secondaryFiles:
      - pattern: "${\n  if (self.nameext == '.mrxs') {\n    return {\n    class: \"\
          File\",\n    location: self.location.match(/.*\\//)[0] + \"/\" + self.nameroot,\n\
          \    basename: self.nameroot};\n  }\n  else return null;\n}"
        required: false
      type: File
    outputs:
    - id: file:///cwl/predictions.cwl#extract-tissue-high/run/tissue
      outputBinding:
        glob: $(inputs.src.basename).zip
        outputEval: ${self[0].basename=inputs.label + '.zip'; return self;}
      type: File
    requirements:
    - class: DockerRequirement
      dockerPull: mdrio/slaid:1.0.0-tissue_model-eddl_2-cudnn
    - class: InitialWorkDirRequirement
      listing:
      - $(inputs.src)
    - class: InlineJavascriptRequirement
