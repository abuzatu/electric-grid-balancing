#!/bin/bash
: "${PROJECT_NAME:=electric-grid-balancing}"

docker build --platform linux/amd64 --no-cache -t $PROJECT_NAME:latest .
