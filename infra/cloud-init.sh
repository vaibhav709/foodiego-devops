#!/bin/bash
exec > /var/log/foodiego-setup.log 2>&1
set -eux
apt-get update -y && apt-get install -y git jq curl
git clone https://github.com/vaibhav709/foodiego-devops.git /opt/foodiego
bash /opt/foodiego/infra/provision.sh
