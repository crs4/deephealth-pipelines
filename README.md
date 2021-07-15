# DeepHealth Pipelines


## Configure

To modify the location where data are stored, create ```.env``` file executing:
```
./create_env.sh
```
Then edit properly the output ```.env```. In particular, check the variable ```CWL_INPUTS_FOLDER``` and the ones with no default values.


Edit env variable ```CWL_DOCKER_GPUS ``` for setting the gpus to be used on docker container used for predictions.


For configuring extra hosts preserving sensitive data, it is possibile to add the informatsion in a docker-compose.ovverride.yml file.
Example:

```
services:
    scheduler:
        extra_hosts:
          - <SERVER NAME>:<SERVER IP>
```


## Deploy

```
git clone  http://mauro@***REMOVED***/DF/deephealth-pipelines
cd deephealth-pipelines
git checkout airflow
docker-compose up -d
```

Check if ```init``` service exited with 0 code, otherwise restart it. It can fail for timing reason, typically sql tables do not exist yet.

To visit Airflow, go to http://localhost:<AIRFLOW_WEBSERVER_PORT>, user admin, password admin.



## Upload data

```
cd slide-importer
docker build -t slide-importer .
```

To import a slide, run:
```
. .env #docker-compose env file for airflow
docker run --rm -it -v $CWL_INPUTS_FOLDER:$CWL_INPUTS_FOLDER -v /PATH/TO/SLIDE:/upload --network deephealth-pipelines_default     slide-importer --server-url http://webserver:8080 /upload/SLIDE_FILENAME --user admin
```

It prompts asking the airflow password, the default is ```admin```




