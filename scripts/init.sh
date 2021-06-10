set -e

sleep 10
airflow users create  --username $AIRFLOW_USER --firstname firstname --lastname lastname --role Admin --email firstname@lastname.org -p $AIRLFLOW_PASSWORD
airflow variables set STAGE  $STAGE_DIR
airflow variables set OME_SEADRAGON_REGISTER_SLIDE $OME_SEADRAGON_URL/mirax/register_slide
