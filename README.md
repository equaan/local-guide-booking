# Local Guide Booking System

A small Flask application for guide availability and traveler bookings, delivered through a local DevSecOps pipeline.

Travelers browse a guide's future availability slots and request bookings. Guides manage their slots and confirm or cancel requests. The project demonstrates the full path from tested source code to a monitored Kubernetes release: Jenkins, Selenium, SonarQube, Trivy, Docker Hub, Argo CD, K3s, Prometheus, and Grafana.

## Highlights

- Role-based traveler and guide accounts with CSRF-protected authentication.
- Guide slot creation, overlap prevention, public browsing, and city/date filtering.
- Transactional booking state machine: PENDING, CONFIRMED, and CANCELLED.
- Database-enforced prevention of duplicate active and confirmed bookings.
- Unit, integration, and Selenium acceptance tests.
- Health, readiness, request logging, and Prometheus metrics.
- CI quality gates, non-root Docker image, image vulnerability scanning, GitOps deployment, rollback rehearsal, and monitoring.

## Architecture

~~~
Browser
  -> Flask + Jinja + SQLAlchemy
  -> SQLite locally (PostgreSQL-compatible through DATABASE_URL)

Git push
  -> Jenkins: test -> Selenium -> SonarQube gate -> Docker build -> Trivy
  -> Docker Hub immutable image
  -> GitOps repository image-tag commit
  -> Argo CD -> K3s
  -> Prometheus -> Grafana
~~~

## Quick Start

Python 3.11+ is required; Python 3.12 is the target runtime.

~~~
git clone https://github.com/equaan/local-guide-booking.git
cd local-guide-booking

python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements-dev.txt
# Windows PowerShell
Copy-Item .env.example .env
# macOS/Linux
# cp .env.example .env

flask --app wsgi db upgrade
python scripts/seed.py
flask --app wsgi run --debug
~~~

Open http://127.0.0.1:5000. The seed script is idempotent, so it is safe to run again.

For complete local, Docker, CI, Selenium, WSL/K3s, GitOps, Prometheus, and Grafana instructions, read **[SETUP.md](SETUP.md)**.

## Verification

~~~
# Unit and integration tests. E2E tests are excluded by default.
python -m pytest
python -m pytest --cov=app --cov-report=term-missing

# Code quality and security checks
ruff check .
ruff format --check .
bandit -r app -q
~~~

While the application is running, inspect:

- http://127.0.0.1:5000/health
- http://127.0.0.1:5000/ready
- http://127.0.0.1:5000/metrics

The project includes 51 unit/integration checks and five Selenium acceptance journeys. A prior full coverage review recorded 94% coverage of app.

## Features

| Area | Behaviour |
|---|---|
| Accounts | Case-insensitive unique email, hashed password, 8-character minimum, city required for guides |
| Slots | Future active slots, duration/price validation, overlap prevention, guide ownership checks |
| Bookings | Traveler request, guide confirmation, cancellation, automatic competing-request cancellation |
| Data integrity | Partial unique indexes enforce one confirmed booking per slot and one active booking per traveler/slot pair |
| Security | CSRF, safe errors, session-cookie protections, role/resource ownership checks |
| Observability | Health, readiness, metrics, request durations/logging, booking and registration counters |

## Acceptance Journeys

The Selenium suite covers five independent browser journeys:

1. Traveler registration, logout, and login.
2. Guide registration and future-slot publication.
3. Traveler booking request with PENDING status.
4. Guide confirmation with CONFIRMED status.
5. Traveler cancellation, complete timeline, and returned slot availability.

## DevSecOps Delivery Flow

1. Jenkins creates a clean virtual environment and runs pytest with JUnit and coverage output.
2. Jenkins starts a temporary Gunicorn application and runs the Selenium suite through a remote Chrome container.
3. SonarQube analyzes the code and its webhook-driven quality gate blocks failing builds.
4. Jenkins builds a multi-stage, non-root Docker image with an immutable version/build/Git-SHA tag.
5. Trivy scans the image for fixable HIGH and CRITICAL vulnerabilities before publication.
6. Jenkins pushes the image to Docker Hub and updates only the image tag in the separate GitOps repository.
7. Argo CD observes that GitOps commit and reconciles it to the local K3s cluster.
8. Prometheus scrapes application metrics and Grafana displays request, latency, error, and booking-transition panels.

The deployed local-lab release uses immutable Docker Hub image tags, including `equaan/local-guide-booking:v0.1.0-22-3d72a976732d`.

## Repository Layout

~~~
app/                 Flask application, services, blueprints, templates, metrics
migrations/          Alembic migration history
tests/               Unit, integration, and Selenium E2E suites
scripts/             Seed data and report-generation helpers
ansible/             Ubuntu WSL2, Docker, K3s, Argo CD, monitoring provisioning
argocd/              Argo CD Application definitions
docs/                PRD, task evidence, prompts, design notes, AI usage log
Dockerfile           Multi-stage non-root application image
Jenkinsfile          CI/CD pipeline as code
JenkinsDockerfile    Jenkins image with Python and Docker CLI support
SETUP.md             Reproducible setup and operations guide
~~~

## Documentation

- [Setup and operations guide](SETUP.md)
- [Product requirements](docs/PRD.md)
- [Course task tracker](docs/TASKS.md)
- [Agent and contribution rules](AGENTS.md)
- [Ansible/K3s/GitOps notes](ansible/README.md)
- [AI usage log](docs/AI-USAGE-LOG.md)

The Helm chart and release values live in the separate [Local Guide Booking GitOps repository](https://github.com/equaan/local-guide-booking-gitops).

## Local-Lab Limits

This repository demonstrates a local single-node WSL2/K3s deployment, not a production high-availability platform. The Kubernetes demonstration uses ephemeral SQLite storage. A production deployment should use PostgreSQL, persistent storage/backups, TLS, ingress, external secret management, alerting, and multiple nodes.

## Student Details

- **Student:** Mohammad Equaan Kacchi
- **Roll No:** 23102A0073
- **Course Project:** Selenium Testing for a Local Guide Booking System
- **Faculty:** Snehal Andhare, Ma'am
