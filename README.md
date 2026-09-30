# Local Guide Booking System

A small Flask web application plus a complete DevSecOps delivery pipeline: Git, Jenkins, SonarQube, Trivy, Selenium, Docker Hub, ArgoCD, Kubernetes, Prometheus and Grafana.

- Student: Mohammad Equaan Kacchi | Roll No 67 | ID 23102A0073 | BE-VII Computer Engineering, Division A
- Course: DevOps project, Academic Year 2026-27 (ODD semester)
- Course project title: Selenium Testing for a Local Guide Booking System

## What the application does

Travelers browse a guide's availability slots and request a booking. Guides confirm or cancel. Everyone can see the status history of a booking. Full requirements: [docs/PRD.md](docs/PRD.md).

## Status

| Course task | Title | Status |
|---|---|---|
| 1 | Problem Definition and Scope | Drafted, needs validation evidence |
| 2 | Agile Planning and DevOps Workflow | Drafted, needs board screenshots |
| 3 | Requirements, Architecture and Technology Setup | Not started |
| 4 | Git and GitHub Repository Initialization | Not started |
| 5 | Feature Development with Branching | Not started |
| 6 | MVP Completion and Git Collaboration | Not started |
| 7 | Jenkins Installation and Continuous Integration Job | Not started |
| 8 | Pipeline as Code and Deployment | Not started |
| 9 | Selenium Test Design and Local Execution | Not started |
| 10 | Continuous Testing and Quality Gates in Jenkins | Not started |
| 11 | Docker Image and Container Lifecycle | Not started |
| 12 | Jenkins-Docker Continuous Delivery | Not started |
| 13 | Configuration Management and Cluster Setup | Not started |
| 14 | Automated Provisioning, GitOps and Reliability Validation | Not started |
| 15 | Final End-to-End Release, Observability, Documentation and Viva | Not started |

## Quick start

Available after work item B-00 is merged. Commands are in [AGENTS.md](AGENTS.md) section 3.

## Repository map

| Path | Contents |
|---|---|
| `docs/PRD.md` | Product requirements (source of truth for behaviour) |
| `docs/TASKS.md` | Task tracker and build work items with acceptance checks |
| `docs/PROMPTS.md` | Prompts used with the coding agent and coach prompts for DevOps tasks |
| `docs/task-NN.md` | One report per course task (merged into the final PDF) |
| `docs/00-*.md` | Deviations register and rewritten task list |
| `docs/AI-USAGE-LOG.md` | Honest log of AI assistance and what was reviewed |
| `AGENTS.md` | Rules for coding agents |
| `CONTRIBUTING.md` | Branch, commit and PR policy |
| `app/`, `tests/`, `migrations/` | Application code (created by work items) |

## Building the report

```bash
pip install -r requirements-docs.txt    # also install pandoc
bash scripts/build_report.sh            # writes build/report.docx
```

Open the .docx in Word, review, then export to PDF for submission.

## Companion repository

Kubernetes manifests and Helm chart live in a separate GitOps repository, `local-guide-gitops` (created in Task 4, used from Task 12).
