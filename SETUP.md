# Setup and Operations Guide

This guide starts with the smallest useful path: run the Flask app locally. Docker, Selenium Grid, Jenkins, K3s, GitOps, and monitoring are optional follow-on sections.

## 1. Prerequisites

### Required for local development

- Git
- Python 3.11 or newer; Python 3.12 is the target runtime
- pip and Python virtual environments

### Optional by capability

| Capability | Additional tools |
|---|---|
| Browser acceptance tests | Google Chrome or Chromium |
| Container image | Docker Desktop or Docker Engine |
| CI/CD | Jenkins, SonarQube, Selenium standalone Chrome, Docker access from Jenkins |
| Kubernetes/GitOps/monitoring | Ubuntu 24.04 WSL2 with systemd, Ansible, native Docker, K3s |

Never commit .env, database files, Jenkins credentials, Docker Hub tokens, GitHub tokens, or Grafana passwords.

## 2. Clone and Run Locally

~~~
git clone https://github.com/equaan/local-guide-booking.git
cd local-guide-booking
python -m venv .venv
~~~

Activate the virtual environment:

~~~powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
~~~

~~~bash
# macOS/Linux
source .venv/bin/activate
~~~

Install dependencies and create local configuration:

~~~bash
pip install -r requirements-dev.txt
~~~

~~~powershell
# Windows PowerShell
Copy-Item .env.example .env
~~~

~~~bash
# macOS/Linux
cp .env.example .env
~~~

Apply schema, seed data, and start the app:

~~~bash
flask --app wsgi db upgrade
python scripts/seed.py
flask --app wsgi run --debug
~~~

Open http://127.0.0.1:5000. Seed data is idempotent.

### Environment variables

| Variable | Local default | Meaning |
|---|---|---|
| APP_ENV | dev | dev, test, prod |
| SECRET_KEY | development value in .env | Required and non-default in production |
| DATABASE_URL | sqlite:///app.db | SQLite locally; PostgreSQL URL is supported |
| LOG_LEVEL | INFO | Application logging level |
| APP_VERSION | dev | Release metadata |
| GIT_SHA | local | Release metadata |
| PORT | 8000 | Gunicorn/container port |

## 3. Verify Local Quality

~~~bash
python -m pytest
python -m pytest --cov=app --cov-report=term-missing
ruff check .
ruff format --check .
bandit -r app -q
~~~

Use python -m pytest on this Windows environment; standalone pytest can resolve to a stale Anaconda launcher.

While the app is running:

~~~powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/ready
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/metrics
~~~

Health proves process liveness without a database query. Ready checks database access with SELECT 1.

## 4. Run Selenium E2E Tests

In terminal 1:

~~~bash
flask --app wsgi db upgrade
flask --app wsgi run --debug
~~~

In terminal 2:

~~~powershell
$env:BASE_URL = "http://127.0.0.1:5000"
$env:E2E_HEADLESS = "1"
python -m pytest -m e2e
~~~

The suite creates unique test users and writes screenshots to test-artifacts on failure.

### Optional Selenium Grid

~~~powershell
docker network create lgb-ci
docker run -d --name selenium-chrome --network lgb-ci -p 4444:4444 -p 7900:7900 selenium/standalone-chrome:4.48.0-20260905
Invoke-RestMethod http://localhost:4444/status

$env:BASE_URL = "http://host.docker.internal:5000"
$env:SELENIUM_REMOTE_URL = "http://localhost:4444/wd/hub"
$env:E2E_HEADLESS = "1"
python -m pytest -m e2e
~~~

## 5. Build and Run the Docker Image

~~~powershell
docker build -t local-guide-booking:dev .
docker run --rm --name local-guide-booking -p 8000:8000 -e APP_ENV=dev -e SECRET_KEY=change-me-for-local-only -e DATABASE_URL=sqlite:///app.db local-guide-booking:dev
~~~

In a second terminal:

~~~powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/ready
docker run --rm --entrypoint id local-guide-booking:dev
~~~

The image runs Gunicorn on port 8000 as non-root appuser. EXPOSE documents the port; -p 8000:8000 publishes it.

## 6. Jenkins, SonarQube, and Trivy

The repository Jenkinsfile expects:

- Jenkins with Pipeline, Git, JUnit, SonarQube Scanner, and Credentials plugins.
- Jenkins built from JenkinsDockerfile for Python, venv, curl, and Docker CLI.
- selenium-chrome and SonarQube on the same Docker network as Jenkins.
- Jenkins Sonar server configuration named sonarqube-local plus a SonarQube webhook.
- Jenkins credential IDs dockerhub-local-guide-booking and github-gitops-writer.

The pipeline tests/analyzes code, runs E2E, builds/scans/pushes an immutable Docker image, and updates the GitOps image tag.

~~~powershell
docker exec jenkins sh -lc "python3 --version; docker version"
docker exec jenkins sh -lc "curl -fsS http://sonarqube:9000/api/system/status"
Invoke-RestMethod http://localhost:4444/status
~~~

Open Jenkins at http://localhost:8080 and SonarQube at http://localhost:9000 in the documented Docker Desktop lab setup.

## 7. Ubuntu WSL2 and K3s

K3s and Docker Desktop Kubernetes are separate. Enter Ubuntu:

~~~powershell
wsl -d Ubuntu-24.04
~~~

Inside Ubuntu, verify native Docker/K3s:

~~~bash
type -a docker
docker version
docker run --rm hello-world
systemctl is-active docker
systemctl is-active k3s
~~~

Provision and rerun to prove idempotency:

~~~bash
ansible-playbook -i ansible/inventory.ini ansible/bootstrap.yml --ask-become-pass
ansible-playbook -i ansible/inventory.ini ansible/bootstrap.yml --ask-become-pass
~~~

Plain kubectl may point at Docker Desktop. Use K3s's binary and kubeconfig:

~~~bash
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get nodes
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get pods -A
~~~

## 8. GitOps and Monitoring

The companion [GitOps repository](https://github.com/equaan/local-guide-booking-gitops) contains Helm chart/release values watched by Argo CD.

~~~bash
ansible-playbook -i ansible/inventory.ini ansible/gitops.yml --ask-become-pass

sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get application -n argocd
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n lgb-dev get deployment,service,pods
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n lgb-dev rollout status deployment/local-guide-booking --timeout=180s
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get pods -n monitoring
~~~

The playbook installs Helm, Argo CD, Prometheus, and Grafana for this local lab. Grafana's password is created as a Kubernetes Secret and is never written to Git.

## 9. Access the Deployed Services

### Application

~~~bash
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n lgb-dev port-forward service/local-guide-booking 8000:8000
~~~

In another terminal:

~~~bash
curl -fsS http://127.0.0.1:8000/health; echo
curl -fsS http://127.0.0.1:8000/ready; echo
~~~

### Prometheus

~~~bash
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n monitoring port-forward service/lgb-prometheus-server 9090:80
curl -fsS 'http://127.0.0.1:9090/api/v1/query?query=up%7Bjob%3D%22local-guide-booking%22%7D'
~~~

Expected result: an up sample for job local-guide-booking with value 1.

### Grafana

~~~bash
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n monitoring get secret lgb-grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d; echo
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml -n monitoring port-forward service/lgb-grafana 3000:80
~~~

Open http://127.0.0.1:3000. Do not commit or share the Grafana password.

## 10. Troubleshooting

| Problem | First checks |
|---|---|
| ModuleNotFoundError app in Jenkins | Activate .venv-ci and run python -m pytest from workspace root |
| Jenkins cannot find Python | Recreate Jenkins from JenkinsDockerfile |
| Browser test cannot reach app | Check BASE_URL; containers use network service names, not their own localhost |
| SonarQube gate waits | Check webhook, Jenkins Sonar configuration/token, Docker network |
| Trivy database timeout | Initial DB download is slow; use cache, alternate registries, longer timeout |
| kubectl shows docker-desktop | Use explicit K3s command and kubeconfig |
| Argo Synced but Progressing | Check rollout, pods, events, and logs |
| Prometheus up equals zero | Check target error, app logs, metrics endpoint, migrations |

## 11. Local-Lab Boundaries

The K3s stack is a learning environment, not production infrastructure. It is single-node; deployed SQLite is ephemeral; Prometheus retention is 24 hours; Grafana persistence is disabled; and Alertmanager, ingress, TLS, external secrets, PostgreSQL backups, and high availability are not configured.

For further K3s, Argo CD, and monitoring details, see [ansible/README.md](ansible/README.md).

