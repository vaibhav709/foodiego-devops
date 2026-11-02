# Jenkins controller for FoodieGo: Docker CLI, kubectl, Helm, envsubst + DevSecOps scanners, configured as code
FROM jenkins/jenkins:lts-jdk21
USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg jq git openssl gettext-base python3-venv \
 && install -m 0755 -d /etc/apt/keyrings \
 && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
 && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" > /etc/apt/sources.list.d/docker.list \
 && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin \
 && rm -rf /var/lib/apt/lists/*
# kubectl + Helm (pinned)
RUN curl -fsSLo /usr/local/bin/kubectl https://dl.k8s.io/release/v1.32.3/bin/linux/amd64/kubectl && chmod +x /usr/local/bin/kubectl \
 && curl -fsSL https://get.helm.sh/helm-v3.17.3-linux-amd64.tar.gz | tar -xz --strip-components=1 -C /usr/local/bin linux-amd64/helm
# Trivy and Gitleaks (pinned)
RUN curl -fsSL https://github.com/aquasecurity/trivy/releases/download/v0.72.0/trivy_0.72.0_Linux-64bit.tar.gz | tar -xz -C /usr/local/bin trivy \
 && curl -fsSL https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz | tar -xz -C /usr/local/bin gitleaks
# Python security tools in an isolated virtualenv: Bandit (SAST), pip-audit (SCA), Checkov (IaC)
RUN python3 -m venv /opt/sec && /opt/sec/bin/pip install --no-cache-dir bandit pip-audit checkov \
 && ln -s /opt/sec/bin/bandit /opt/sec/bin/pip-audit /opt/sec/bin/checkov /usr/local/bin/
USER jenkins
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY casc/ /usr/share/jenkins/ref/casc/
ENV CASC_JENKINS_CONFIG=/usr/share/jenkins/ref/casc/jenkins.yaml \
    JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
