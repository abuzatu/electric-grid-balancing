#!/bin/bash
: "${PROJECT_NAME:=electric-grid-balancing}"

docker exec -i -t  ${PROJECT_NAME} \
    poetry run dotenv run ipython