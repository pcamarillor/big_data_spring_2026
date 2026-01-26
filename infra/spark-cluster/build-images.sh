#!/bin/bash

set -e

docker build -t spark-base:latest ./base
docker build -t spark-master:latest ./spark-master
docker build -t spark-worker:latest ./spark-worker