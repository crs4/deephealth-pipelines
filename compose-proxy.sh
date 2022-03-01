#!/usr/bin/env bash
source .env

proxy_nginx_container=dh-nginx-proxy
if [ $(docker ps | grep ${proxy_nginx_container} | wc -l ) -eq 0  ]; then
  docker run -d -p ${PROXY_PORT}:80  --name ${proxy_nginx_container}  -v /var/run/docker.sock:/tmp/docker.sock:ro nginxproxy/nginx-proxy
fi

if [ $(docker network list | grep ${DOCKER_NETWORK} | wc -l ) -eq 0  ]; then
  docker network create ${DOCKER_NETWORK}
fi

if [ $(docker container inspect ${proxy_nginx_container}   | grep ${DOCKER_NETWORK} | wc -l ) -eq 0  ]; then
  docker network connect ${DOCKER_NETWORK} ${proxy_nginx_container}
fi
docker-compose -p ${PROJECT}  -f docker-compose.yaml -f docker-compose.proxy.yaml  -f docker-compose.backend.yaml $@
