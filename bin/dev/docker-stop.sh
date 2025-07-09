#!/bin/bash
: "${PROJECT_NAME:=electric-grid-balancing}"

CONTAINER_NAME="${PROJECT_NAME}"

if  docker ps | grep "$CONTAINER_NAME$"; then
    docker stop $CONTAINER_NAME
else
    echo "Container not running."
fi
