sleep 10
airflow users create  --username $AIRFLOW_USER --firstname firstname --lastname lastname --role Admin --email firstname@lastname.org -p $AIRLFLOW_PASSWORD
airflow variables set STAGE  $STAGE_DIR
