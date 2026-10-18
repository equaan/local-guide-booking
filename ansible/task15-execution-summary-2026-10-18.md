# Task 15 Execution Summary

## Scope

This record captures the final local-lab observability verification on Ubuntu
24.04 WSL2, K3s, Argo CD, Prometheus, and Grafana. The application is deployed
from the separate `equaan/local-guide-booking-gitops` repository.

## Components

- Argo CD chart `10.10.3` reconciles the GitOps repository into K3s.
- Prometheus chart `29.37.0` scrapes the application `/metrics` endpoint.
- Grafana chart `10.5.15` provisions a Prometheus datasource and the Local
  Guide Booking overview dashboard.
- The Grafana password is generated once in the Kubernetes
  `lgb-grafana-admin` Secret and is not committed to Git.

## Verified Evidence

| Check | Evidence |
| --- | --- |
| Idempotent GitOps provisioning | `ansible-playbook -i ansible/inventory.ini ansible/gitops.yml --ask-become-pass` ended with `ok=19 changed=0 unreachable=0 failed=0 skipped=6`. |
| Argo CD application health | `local-guide-booking`, `lgb-prometheus`, and `lgb-grafana` reported `Synced` and `Healthy`. |
| Application rollout | `kubectl rollout status deployment/local-guide-booking -n lgb-dev --timeout=180s` reported `successfully rolled out`. |
| Metrics endpoint | From the Prometheus pod, `wget` of the in-cluster `/metrics` endpoint returned `lgb_http_requests_total` and `lgb_http_request_duration_seconds` samples. |
| Prometheus scrape | `up{job="local-guide-booking"}` returned the target with value `1`. |
| Grafana dashboard | The Local Guide Booking dashboard loaded through a local port-forward and showed request rate, p95 latency, HTTP 5xx rate, and booking-transition panels. |

## Deployment Defect Found and Repaired

Prometheus initially reported the application target as down. The scrape log
showed `/metrics` failing with `sqlite3.OperationalError: no such table:
bookings`. The GitOps chart started Gunicorn without applying migrations.

GitOps pull request 2 added a non-root `database-migrations` init container
that runs `python -m flask --app wsgi db upgrade`. The init and application
containers share `/app/instance` through an `emptyDir` volume, so the current
SQLite demonstration database is available after startup. Argo CD reconciled
the merged change and the subsequent Prometheus scrape returned `up = 1`.

## Repeatable Verification

```bash
ansible-playbook -i ansible/inventory.ini ansible/gitops.yml --ask-become-pass

sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml \
  get application -n argocd

sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml \
  -n monitoring port-forward service/lgb-prometheus-server 9090:80

curl -fsS 'http://127.0.0.1:9090/api/v1/query?query=up%7Bjob%3D%22local-guide-booking%22%7D'
```

For Grafana, port-forward `service/lgb-grafana` from `3000:80`, retrieve the
password locally from `lgb-grafana-admin`, and open `http://127.0.0.1:3000`.

## Limitations and Next Steps

- This is a single-node WSL2 lab, not a highly available production cluster.
- SQLite is stored in a pod `emptyDir`, so booking data is lost when the pod is
  recreated. Use managed PostgreSQL and backups before production use.
- Prometheus data is ephemeral and retained for 24 hours; Grafana persistence
  is disabled to fit the local 8 GB lab budget.
- There are no Alertmanager rules, ingress, TLS, or remote monitoring yet.
- Record a timed commit-to-deployment run before claiming the SC6 target of 20
  minutes or less, and capture the dashboard's measured p95 before claiming
  the SC9 target of under 500 ms.
