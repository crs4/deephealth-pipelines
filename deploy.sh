#!/usr/bin/env bash
PROJECT=$1
git clone https://github.com/crs4/deephealth-pipelines.git $PROJECT
cd $PROJECT
./create_env.sh
sed -i "s|PROJECT=dev|PROJECT=${PROJECT}|g" .env 
