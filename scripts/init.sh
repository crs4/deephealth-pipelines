set -ex

sleep 10
airflow users create  --username $AIRFLOW_USER --firstname firstname --lastname lastname --role Admin --email firstname@lastname.org -p $AIRLFLOW_PASSWORD

airflow variables set STAGE  $STAGE_DIR
airflow variables set OUT_DIR  $OUT_DIR
airflow variables set PREDICTIONS_DIR  $PREDICTIONS_DIR
airflow variables set OME_SEADRAGON_REGISTER_SLIDE $OME_SEADRAGON_URL/ome_seadragon/mirax/register_slide
airflow variables set OME_SEADRAGON_REGISTER_PREDICTIONS $OME_SEADRAGON_URL/ome_seadragon/arrays/register_dataset
airflow variables set OME_SEADRAGON_URL $OME_SEADRAGON_URL

airflow variables set PREDICTIONS_MODE 'serial'
airflow variables set SERIAL_PREDICTIONS_PARAMS '{ "slide": { "class": "File", "path": null }, "mode": "serial", "tissue-low-level": 9, "tissue-low-label": "tissue_low", "tissue-high-level": 0, "tissue-low-chunk": 256, "tissue-high-label": "tissue_high", "tissue-high-filter": "tissue_low>0.8", "tissue-high-chunk": 1536, "tumor-chunk": 1536, "gpu": 0, "tumor-level": 1, "tumor-label": "tumor", "tumor-filter": "tissue_low>0.8" }'
airflow variables set PARALLEL_PREDICTIONS_PARAMS '{ "slide": { "class": "File", "path": null }, "mode": "parallel", "tissue-low-level": 9, "tissue-low-label": "tissue_low", "tissue-high-level": 0, "tissue-low-chunk": 256, "tissue-high-label": "tissue_high", "tissue-high-filter": "tissue_low>0.8", "tissue-high-chunk": 2048, "tumor-chunk": 2048, "gpu": 0, "tumor-level": 1, "tumor-label": "tumor", "tumor-filter": "tissue_low>0.8", "tumor-batch": 1000000, "tissue-high-batch": 1000000}'

env
airflow connections add promort --conn-host ${PROMORT_HOST} --conn-type ${PROMORT_CONN_TYPE} --conn-port ${PROMORT_PORT} --conn-login ${PROMORT_USER} --conn-password ${PROMORT_PASSWORD}
