#!/bin/bash

docker build .. --file java-shard-17.Dockerfile -t docker.pkg.github.com/teammonumenta/monumenta-automation/monumenta-java-shard-17 --build-arg USERNAME=epic --build-arg UID=1000 --build-arg GID=1000 && docker push docker.pkg.github.com/teammonumenta/monumenta-automation/monumenta-java-shard-17
