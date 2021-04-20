# DeepHealth Pipelines


## Configure

To modify the location where data are stored, please modify the following sections in ```docker-compose.yaml```:
 * volumes > data-volume
 *  x-airflow-common > volumes


If the host machine has gpus, decomment section ```services > worker> deploy``` and set the right ids for the gpus. gpu need to be configured also in file ```airflow/dags/predictions.yml```

## Deploy

```
git clone  http://mauro@repohub.crs4.it/DF/deephealth-pipelines
cd deephealth-pipelines
git checkout airflow
```

Follow the instructions at https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html, in particular the settings of the env file and the initialization.

To visit Airflow, go to http://localhost:8181, user airflow, password airflow.

To visit Dask, go to http://localhost:8787.


## Upload data

Clone the slide-importer repo
```
git clonegit@github.com:mdrio/slide_importer.git
cd slide-importer
docker build -t slide-importer .
```

To import a slide, type this command:
```
docker run --rm -it -v deephealth-pipelines_stage-volume:/data/stage -v /PATH/TO/{SLIDE_DIR}:/upload --network deephealth-pipelines_default   slide-importer--server-url http://airflow-webserver:8080 --user airflow /upload/{SLIDE_FILENAME}
```

It prompts asking the airflow password, the default is ```airflow```




