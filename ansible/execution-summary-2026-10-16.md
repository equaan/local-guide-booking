# Task 13 Execution Summary

Target: Ubuntu 24.04 WSL2 with systemd, using the local Ansible inventory.

## First run

Command:

```bash
ansible-playbook -i ansible/inventory.ini ansible/bootstrap.yml --ask-become-pass
```

Real recap:

```text
localhost : ok=18 changed=2 unreachable=0 failed=0 skipped=2 rescued=0 ignored=0
```

The two changes created the native-Docker Jenkins volume and container. Direct
verification confirmed Docker and K3s were active, the K3s node was Ready, all
long-running system pods were Running, and Jenkins returned HTTP 200 on
`http://127.0.0.1:8081/login`.

## Idempotency run

The same command was run again without changing the target.

```text
localhost : ok=17 changed=0 unreachable=0 failed=0 skipped=3 rescued=0 ignored=0
```

This demonstrates that the playbook converges without creating additional
resources or changing already-correct configuration.
