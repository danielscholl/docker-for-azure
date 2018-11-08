#!/bin/bash
VERSION=1.0
docker build -t guide-azure:$VERSION .
docker tag guide-azure:$VERSION rscaptain/guide-azure:$VERSION
docker push rscaptain/guide-azure:$VERSION
