#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
FROM spark:4.0.1-scala2.13-java17-ubuntu
LABEL author="Pablo Camarillo" email="pablo.camarillo@iteso.mx"
LABEL version="0.4"
USER root

RUN set -ex; \
    apt-get update; \
    apt-get install -y python3 python3-pip; \
    pip3 install --no-cache-dir jupyter; \
    rm -rf /var/lib/apt/lists/*

ENV PYSPARK_DRIVER_PYTHON='jupyter'
ENV PYSPARK_DRIVER_PYTHON_OPTS='notebook --no-browser --port=8888'

EXPOSE 8888

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

RUN pip install findspark
RUN pip install numpy