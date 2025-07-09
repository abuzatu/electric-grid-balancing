#!/bin/bash
: "${PROJECT_NAME:=electric-grid-balancing}"

CONTAINER_NAME="${PROJECT_NAME}"

if  docker ps | grep "$CONTAINER_NAME$"; then
    docker stop $CONTAINER_NAME
    docker rm $CONTAINER_NAME
elif docker ps -a | grep "$CONTAINER_NAME$"; then
    docker rm $CONTAINER_NAME
else
    echo "Container does not exist"
fi

if docker image ls -a | grep "${PROJECT_NAME} " ; then
    docker image rm ${PROJECT_NAME}
fi
