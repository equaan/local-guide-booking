# Task 13 Target Configuration

`bootstrap.yml` prepares the local Ubuntu 24.04 WSL2 target used as the
zero-cost Task 13 node. It installs native Docker, configures a single-node
K3s server, and starts a separate Jenkins container.

## Prerequisites

- Ubuntu 24.04 WSL2 with systemd enabled.
- Ansible installed in Ubuntu.
- Docker Desktop's WSL integration disabled for `Ubuntu-24.04`.
  The Windows Docker Desktop workloads remain separate. This avoids the
  `/Docker/host` mount format that prevents K3s kubelet startup.
- Docker Desktop Kubernetes keeps port `6443`; K3s is configured for `6444`.

## Services

| Service | Scope | Port |
| --- | --- | --- |
| Native Docker Engine | Ubuntu target | Docker socket |
| K3s API | Ubuntu target | `6444` |
| Jenkins | Ubuntu target, loopback only | `8081` |

Jenkins uses the named Docker volume `lgb-jenkins_home` and is bound only to
`127.0.0.1`. This keeps it distinct from the existing Docker Desktop Jenkins
instance on port `8080`.

## Run and verify

```bash
ansible-playbook -i ansible/inventory.ini ansible/bootstrap.yml --ask-become-pass
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get nodes
sudo /usr/local/bin/k3s kubectl --kubeconfig /etc/rancher/k3s/k3s.yaml get pods -A
docker ps --filter name=lgb-jenkins
curl -I http://127.0.0.1:8081/login
```

Run the playbook twice. The second run should report no changes except an
initial Jenkins image pull or a service restart caused by a changed K3s config.
