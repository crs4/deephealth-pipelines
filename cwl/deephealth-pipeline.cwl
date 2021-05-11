#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow


# requirements:
#   InlineJavascriptRequirement: {}


inputs:
  slide: File
  tissue-low-level: int
  tissue-low-label: string
  tissue-high-level: int
  tissue-high-label: string
  tissue-high-filter: string

  # tumor-level:
  #   type: int
  # tumor-label:
  #   type: string
  # tumor-filter: string
  gpu: int?

outputs:
  # tumor:
  #   type: Directory
  #   outputSource: classify-tumor/tumor
  tissue:
    type: Directory
    outputSource: extract-tissue-high/tissue


steps:
  extract-tissue-low:
    run: /home/mauro/deephealth-pipelines/cwl/extract_tissue.cwl
    in:
      src: slide
      level: tissue-low-level
      label: tissue-low-label
      gpu: gpu
    out: [tissue]

  extract-tissue-high:
    run: /home/mauro/deephealth-pipelines/cwl/extract_tissue.cwl
    in:
      src: slide
      level: tissue-high-level
      label: tissue-high-label
      filter-slide: extract-tissue-low/tissue
      filter: tissue-high-filter
      gpu: gpu
    out: [tissue]


  # classify-tumor:
  #   run: classify-tumor.cwl
  #   in:
  #     src: slide
  #     level: tumor-level
  #     label: tumor-label
  #     filter_slide: extract-tissue/tissue
  #     filter: tumor-filter
  #     gpu: gpu
  #   out:
  #     [tumor]
#
