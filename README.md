# FoodieGo DevOps — PBL-III

**Vaibhav Shelke**

DevOps practicals implemented on **AWS Academy Learner Lab** for *FoodieGo*, an online food-ordering platform,
and *CareSync*, a clinic appointment & e-prescription service used for the healthcare DevSecOps practical.

| # | Practical | Jenkins job | Endpoint |
|---|-----------|-------------|----------|
| 7 | CI/CD pipeline deploying a Dockerized app on Kubernetes via Jenkins | `FoodieGo/01-CI-CD-Helm` | `:31001` |
| 8 | Automated Blue-Green deployment (Jenkins, Kubernetes, Docker) | `FoodieGo/02-Blue-Green` | prod `:31002`, stage `:31012` |
| 9 | DevSecOps in a healthcare system | `FoodieGo/03-CareSync-DevSecOps` | `:31003` |

## Stack
Python 3.12 / Flask / Gunicorn · Docker multi-stage · private Docker registry · k3s Kubernetes · **Helm 3** ·
Jenkins (Pipeline, Job DSL, Configuration-as-Code) · AWS EC2 (Ubuntu 24.04, encrypted gp3, IMDSv2) ·
Gitleaks · Bandit · pip-audit · Checkov · Trivy (+ CycloneDX SBOM) · OWASP ZAP

## Layout
```
app/          FoodieGo Flask app + pytest suite + Dockerfile (builder → test → runtime)
caresync/     CareSync clinic API (RBAC, PII masking, audit log) + security tests + Dockerfile
helm/foodiego Helm chart used by the CI/CD pipeline (Practical 7)
k8s/bluegreen prod/stage Services + slot template (Practical 8)
k8s/caresync  hardened manifests: PSA restricted, NetworkPolicy, read-only FS, secret-as-file (Practical 9)
pipelines/    Jenkinsfile.cicd · Jenkinsfile.bluegreen · Jenkinsfile.devsecops
jenkins/      Jenkins image + JCasC (creates the FoodieGo folder and all jobs)
infra/        launch-ec2.sh (CloudShell) · cloud-init.sh · provision.sh
scripts/      run-job helper
```

## Quick start
```bash
# AWS CloudShell
curl -fsSL https://raw.githubusercontent.com/vaibhav709/foodiego-devops/main/infra/launch-ec2.sh | bash
# on the instance, ~10 min later
run-job FoodieGo/01-CI-CD-Helm
run-job FoodieGo/02-Blue-Green RELEASE=r2 MODE=release
run-job FoodieGo/03-CareSync-DevSecOps
```
Stop the EC2 instance afterwards to save Learner Lab credit.
