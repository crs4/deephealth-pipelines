set -ex

sleep 10
airflow users create  --username $AIRFLOW_USER --firstname firstname --lastname lastname --role Admin --email firstname@lastname.org -p $AIRFLOW_PASSWORD

airflow variables set INPUT_DIR  $INPUT_DIR
airflow variables set STAGE_DIR  $CWL_INPUTS_FOLDER
airflow variables set OUT_DIR  $OUT_DIR
airflow variables set FAILED_DIR  $FAILED_DIR
airflow variables set PREDICTIONS_DIR  $PREDICTIONS_DIR
airflow variables set BACKUP_DIR  $BACKUP_DIR

airflow variables set OME_SEADRAGON_REGISTER_SLIDE $OME_SEADRAGON_URL/ome_seadragon/mirax/register_slide
airflow variables set OME_SEADRAGON_REGISTER_PREDICTIONS $OME_SEADRAGON_URL/ome_seadragon/arrays/register_dataset
airflow variables set OME_SEADRAGON_URL $OME_SEADRAGON_URL

airflow variables set PREDICTIONS_MODE 'serial'
airflow variables set SERIAL_PREDICTIONS_PARAMS '{ "slide": { "class": "File", "path": null }, "tissue-low-level": 9, "tissue-low-label": "tissue_low", "tissue-high-level": 4,  "tissue-high-label": "tissue_high", "tissue-high-filter": "tissue_low>0.1",   "gpu": 0, "tumor-level": 1, "tumor-label": "tumor", "tumor-filter": "tissue_low>0.8", "gleason-level": 1, "gleason-label": "gleason", "gleason-filter": "tissue_low>0.8"  }'

airflow variables set ROI_THRESHOLD '0.8'
airflow variables set PROMORT_TOOLS_IMG  $PROMORT_TOOLS_IMG
airflow variables set DOCKER_NETWORK $DOCKER_NETWORK

airflow variables set PROMORT_SESSION_ID $PROMORT_SESSION_ID

if  ! airflow connections get promort; then
  airflow connections add promort --conn-host ${PROMORT_HOST} --conn-type ${PROMORT_CONN_TYPE} --conn-port ${PROMORT_PORT} --conn-login ${PROMORT_USER} --conn-password ${PROMORT_PASSWORD}
fi



