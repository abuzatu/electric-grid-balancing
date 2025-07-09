#!/bin/bash
: "${PROJECT_NAME:=electric-grid-balancing}"

if [ $(hostname) = "vps" ]; then
    echo "Hostname is vps"
    MY_IP=$(hostname -I | awk '{print $1}')
    URL_STEM="${MY_IP}"
else
    echo "Hostname is not vps, assume it is local"
    URL_STEM="localhost"
fi
echo "URL_STEM=${URL_STEM}"

# For multiple files, we need to use the -m flag for each file
docker exec -i -t ${PROJECT_NAME} \
  poetry run dotenv run dagster dev \
  --host 0.0.0.0 \
  --port 3002 \
  -m src.dagster_app.unit_commitment -m src.dagster_app.virtual_power_plant