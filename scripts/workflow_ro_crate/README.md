# Digital pathology tissue/tumor prediction workflow

This workflow performs computational annotation of magnified prostate tissue areas and cancer subregions using deep learning models. The workflow consists of three steps:

1. inference of a low-resolution tissue mask to select areas for further processing;

2. high-resolution tissue inference to refine borders;

3. high-resolution cancer tissue identification.
