#!/bin/bash
: "${PROJECT_NAME:=electric-grid-balancing}"

CONTAINER_NAME="${PROJECT_NAME}"

if  docker ps | grep " $PROJECT_NAME$"; then
    echo "Container already started. Do nothing"
elif docker ps -a | grep " $PROJECT_NAME$" ; then
    docker start $PROJECT_NAME
else
    # expose port for FastAPI: 8018
    # expose port for streamlit: 8508
    # expose port for Jupyter Notebook: 1342
    # expose port for Dagster: 3002
    docker run -i -d \
            -v $HOME/.ssh:/home/jumbo/.ssh \
            -v `pwd`:/opt/$PROJECT_NAME \
            --add-host=host.docker.internal:host-gateway \
            -p 8018:8018 \
            -p 8508:8508 \
            -p 1342:1342 \
            -p 3002:3002 \
            --name $PROJECT_NAME \
            -t $PROJECT_NAME:latest \
            /bin/bash
    docker exec -i -t $PROJECT_NAME poetry install
fi
