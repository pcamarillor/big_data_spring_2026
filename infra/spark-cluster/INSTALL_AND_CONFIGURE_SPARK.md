# Spark Cluster with Docker & docker-compose

# General

A simple spark standalone cluster for your testing environment purposses. A *docker-compose up* away from you solution for your spark development environment.

# Installation

The following steps will make you run your spark cluster's containers.

## Pre requisites

* Docker installed

* Docker compose installed

## Build the docker images

The first step to deploy the cluster will be the build of the custom images, these builds can be performed with the *build-images.sh* script. 

The executions is as simple as the following steps:

For Linux/MacOS users:

```sh
chmod +x build-images.sh
./build-images.sh
```

For Windows users:

```sh
docker build -t spark-base:latest ./base
docker build -t spark-master:latest ./spark-master
docker build -t spark-worker:latest ./spark-worker
```

This will create the following docker images:

* spark-base: A base image based on Spark 4.0.1, Scala2.13 and Java17 running on the top of an ubuntu base image

* spark-master: An image based on the previously created spark image, used to create a spark master containers.

* spark-worker: An image based on the previously created spark image, used to create spark worker containers.

* jupyter-notebook: An image that installs Jupyter Notebook server on the top of Java, Scala, and Spark stack

## Run the docker-compose

The final step to create your test cluster will be to run the compose file:

```sh
docker compose up --scale spark-worker=3 -d
```

## Validate your cluster

Just validate your cluster accessing the spark UI on [master URL](http://localhost:9090)


### Binded Volumes

To make app running easier I've shipped two volume mounts described in the following chart:

Host Mount|Container Mount|Purposse
---|---|---
./notebooks|/opt/spark/work-dir/notebooks|Used to make available your notebook's code and jars on all workers & master nodes.
./data|/opt/spark/work-dir/data| Used to make available your notebook's data on all workers & master nodes.
./src|/opt/spark/work-dir/src| Used to make available the code developed by each student as well to store examples.


