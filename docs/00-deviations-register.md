# Deviations Register

This project keeps the intent of all 15 tasks in the course sheet. Where the implementation differs from the sheet, the change and the reason are recorded here. Ma'am has confirmed that the approach in the sheet is not the only valid one, and that the stack may change as long as the changes are mentioned and the 15 tasks are rewritten and shown to her.

| # | Course sheet says | This project uses | Reason |
|---|------------|------------|------------|
| D1 | Java with Maven, Gradle or Ant | Python 3.12 with Flask, pip and pytest | Same build-and-test intent with faster iteration; one language across app, tests, Selenium and metrics |
| D2 | Tomcat or Nginx as the deployment target | Kubernetes (k3s or k3d) using Helm | Industry-standard declarative deployment target |
| D3 | Jenkins builds the image and deploys the container directly | Jenkins performs CI; ArgoCD performs CD from a separate GitOps repository | Separates build from delivery and gives an auditable Git-based rollback |
| D4 | Puppet or Ansible configures a node | Ansible; Terraform only if a free cloud VM is available | Configuration management plus reproducible infrastructure |
| D5 | Selenium suite run through Maven | Selenium WebDriver in Python through pytest; headless Chrome or Selenium Grid | Follows from D1; same test-design intent |
| D6 | Not in the sheet | SonarQube and Trivy as quality and security gates | Adds DevSecOps checks to the pipeline |
| D7 | Not in the sheet | Prometheus and Grafana | Adds observability to the reliability validation in Task 14 |
| D8 | Docker Hub or a local registry | Docker Hub | Free, simple, works with Jenkins and ArgoCD |
| D9 | A target server or node | Contingency: a local VM or WSL2 stands in for the remote node in Tasks 13 and 14 if no free cloud VM is available | Project has a zero-cost constraint |

## Approval record

| Item | Evidence | Date |
|---|---|---|
| Python stack and custom approach accepted by ma'am (verbal) | TODO(student): message or email screenshot saved in docs/evidence/approvals/ | TODO |
| Rewritten 15-task list shown to ma'am | TODO(student): confirmation screenshot | TODO |
