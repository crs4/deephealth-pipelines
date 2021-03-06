#!/usr/bin/env bash
PROJECT=$1
REPO=${2:-https://github.com/crs4/deephealth-pipelines.git}
BRANCH=${3:-develop}

git clone $REPO $PROJECT
cd $PROJECT
git checkout $BRANCH
./create_env.sh
sed -i "s|PROJECT=dev|PROJECT=$(basename $PROJECT)|g" .env
sed -i "s|DOCKER_NETWORK=deephealth|DOCKER_NETWORK=deephealth-$(basename $PROJECT)|g" .env
source .env
sed  -i "s|omeseadragon:4080|$(basename $PROJECT).omenginx.local:${PROXY_PORT}|g" promort_config/config.yaml
