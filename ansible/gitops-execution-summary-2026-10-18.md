# Task 14 GitOps And Reliability Evidence

Date: 2026-10-18

## Provisioning

The Ubuntu 24.04 WSL target ran `ansible/gitops.yml` against the native K3s
cluster. The playbook installed checksum-pinned Helm `v3.22.0`, installed
Argo CD chart `10.10.3`, and created the `local-guide-booking` Argo CD
Application.

Initial successful run:

```text
localhost : ok=15 changed=2 unreachable=0 failed=0 skipped=1 rescued=0 ignored=0
```

The only changes were the Argo CD Helm release and the Application resource.

Idempotency rerun:

```text
localhost : ok=13 changed=0 unreachable=0 failed=0 skipped=3 rescued=0 ignored=0
```

## GitOps Deployment

The GitOps repository deploys `apps/local-guide-booking` as a Helm chart. The
Jenkins delivery pipeline builds an immutable image, scans it, pushes it to
Docker Hub, and commits the resulting image tag to the chart's `values.yaml`.

Jenkins release commit in the GitOps repository:

```text
51f31b4e4cd9cb1921242a6ccf5f67bcf0b0a35d
deploy: local-guide-booking v0.1.0-21-3bfd7ff46b56
```

Argo CD and K3s evidence for that release:

```text
Application: Synced, Healthy
Revision: 51f31b4e4cd9cb1921242a6ccf5f67bcf0b0a35d
Deployment rollout: successfully rolled out
Image: equaan/local-guide-booking:v0.1.0-21-3bfd7ff46b56
```

## Rollback Rehearsal

The release commit was reverted on the GitOps repository's `main` branch with
`git revert --no-edit`. This adds a corrective commit instead of rewriting
history. Argo CD detected the Git change and reconciled the previous stable
image automatically.

```text
Argo CD revision after revert: 81eac98e91fe9a19eeda2c904667d26d1c725773
Application: Synced, Healthy
Restored image: equaan/local-guide-booking:v0.1.0-20-aa7328f3395e
```

## Post-Rollback Health Check

The service was port-forwarded from K3s and both operational endpoints passed:

```json
{"git_sha":"local","status":"ok","version":"dev"}
{"status":"ready"}
```

Commands used:

```bash
sudo /usr/local/bin/k3s kubectl \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  -n lgb-dev port-forward service/local-guide-booking 8000:8000

curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8000/ready
```
