#!/bin/bash
: "${PROJECT_NAME:=electric-grid-balancing}"

docker build --no-cache -t $PROJECT_NAME:latest .
