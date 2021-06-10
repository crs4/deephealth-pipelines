set -e

sleep 10
airflow users create  --username $AIRFLOW_USER --firstname firstname --lastname lastname --role Admin --email firstname@lastname.org -p $AIRLFLOW_PASSWORD

airflow variables set STAGE  $STAGE_DIR
airflow variables set OME_SEADRAGON_REGISTER_SLIDE $OME_SEADRAGON_URL/mirax/register_slide
airflow variables set PREDICTIONS_PARAMS '{ "slide": { "class": "File", "path": null }, "tissue-low-level": 8, "tissue-low-label": "tissue_low", "tissue-high-level": 0, "tissue-low-chunk": 256, "tissue-high-label": "tissue_high", "tissue-high-filter": "tissue_low>0.8", "tissue-high-chunk": 1536, "tumor-chunk": 1536, "gpu": 0, "tumor-level": 0, "tumor-label": "tumor", "tumor-filter": "tissue_low>0.8" }'
