#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow


requirements:
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


inputs:
  slide:
    type: File
  tissue-level:
    type: int
  tissue-label:
    type: string
  tumor-level:
    type: int
  tumor-label:
    type: string
  tumor-filter: string

outputs:
  tumor:
    type: Directory
    outputSource: classify-tumor/tumor
  # tissue:
  #   type: Directory
  #   outputSource: extract-tissue/tissue


steps:
  extract-tissue:
    run: /home/mauro/airflow/dags/extract_tissue.cwl
    in:
      src: slide
      level: tissue-level
      label: tissue-label
    out: [tissue]


  classify-tumor:
    run: /home/mauro/airflow/dags/classify-tumor.cwl
    in:
      src: slide
      level: tumor-level
      label: tumor-label
      filter_slide: extract-tissue/tissue
      filter: tumor-filter
    out:
      [tumor]
#
