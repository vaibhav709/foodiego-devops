#!/bin/bash
# Idempotent provisioning: Docker + registry, k3s + Helm, Jenkins (configuration as code)
set -eux
export DEBIAN_FRONTEND=noninteractive
REPO_URL="https://github.com/vaibhav709/foodiego-devops.git"
[ -f /swapfile ] || { fallocate -l 4G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile; }

command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh
usermod -aG docker ubuntu
docker inspect registry >/dev/null 2>&1 || docker run -d --restart=always --name registry -p 5000:5000 registry:2

mkdir -p /etc/rancher/k3s
printf 'mirrors:\n  "localhost:5000":\n    endpoint:\n      - "http://localhost:5000"\n' > /etc/rancher/k3s/registries.yaml
command -v k3s >/dev/null || curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--write-kubeconfig-mode 644 --disable traefik" sh -
until kubectl get nodes 2>/dev/null | grep -q " Ready"; do sleep 5; done
install -d -o ubuntu -g ubuntu /home/ubuntu/.kube && install -o ubuntu -g ubuntu -m 600 /etc/rancher/k3s/k3s.yaml /home/ubuntu/.kube/config
command -v helm >/dev/null || curl -fsSL https://get.helm.sh/helm-v3.17.3-linux-amd64.tar.gz | tar -xz --strip-components=1 -C /usr/local/bin linux-amd64/helm

P=/home/ubuntu/.jenkins-admin
[ -f $P ] || { openssl rand -hex 12 > $P; chown ubuntu:ubuntu $P; chmod 600 $P; }
docker build -t foodiego-jenkins /opt/foodiego/jenkins
docker rm -f jenkins >/dev/null 2>&1 || true
docker run -d --name jenkins --restart=always --network host \
  --group-add "$(getent group docker | cut -d: -f3)" \
  -v jenkins_home:/var/jenkins_home -v /var/run/docker.sock:/var/run/docker.sock \
  -v /etc/rancher/k3s/k3s.yaml:/kube/config:ro -e KUBECONFIG=/kube/config \
  -e ADMIN_PASSWORD="$(cat $P)" -e REPO_URL="$REPO_URL" foodiego-jenkins
until curl -sf -o /dev/null http://localhost:8080/login; do sleep 5; done
install -m 755 /opt/foodiego/scripts/run-job.sh /usr/local/bin/run-job
echo "PROVISIONING COMPLETE"
