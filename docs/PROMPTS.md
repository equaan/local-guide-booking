# Prompts

How to use this file: run the prompts in order, one at a time. Read the agent's PR yourself before merging. Never paste the next prompt until the previous PR is reviewed and merged into `develop`.

## Part 0: Pre-flight (you do this, not the agent)

Tools on your machine: Git, Python 3.11 or newer, the GitHub CLI (`gh`), Chrome (for Selenium later), and a coding agent that can run shell commands (for example Codex CLI or the Codex IDE extension). If the agent cannot run commands, you must run `pip install`, `pytest` and `ruff` yourself and paste the output back to it.

1. On GitHub create an empty public repository named `local-guide-booking` (no README, no .gitignore, no license). Public keeps branch protection available and shows the project in your portfolio.
2. Unzip this kit into a folder named `local-guide-booking`, then:

```bash
cd local-guide-booking
git init -b main
git add .
git commit -m "docs: add project kit (PRD, tasks, prompts, task 1 and 2 reports)"
git remote add origin https://github.com/equaan/local-guide-booking.git
git push -u origin main
git switch -c develop
git push -u origin develop
gh auth login
```

3. On GitHub: Settings, Branches, add a protection rule for `main` and `develop` that requires a pull request before merging. Set the default branch to `develop`.
4. Create labels (`task`, `bug`, `enabler`, `docs`, `P1-must`, `P2-should`, `P3-could`), one issue per work item in docs/TASKS.md Part B, and a GitHub Projects board (Task 2 explains the columns). Screenshot each step into `docs/evidence/`.
5. Optional but wise: create the second repository `local-guide-gitops` now (empty README only). It is used from Task 12.
6. Start the agent inside the `local-guide-booking` folder on branch `develop` and paste prompt P0.

## Part 1: Application prompts for the coding agent

Each prompt is self-contained. The agent auto-reads AGENTS.md; the prompts still tell it to read the docs so nothing depends on that.

### P0: App skeleton (work item B-00, Task 4)

```
Read AGENTS.md, docs/PRD.md and docs/TASKS.md completely before writing any code.

Work item: B-00 (app skeleton). Create branch feature/b00-app-skeleton from develop.

Do:
- Create the layout in AGENTS.md section 4 that B-00 needs: application factory, config classes (PRD section 12), extensions, wsgi.py, timeutils.py with now_ist(), ops blueprint with /health and /ready, landing page, base.html with the navigation contract from PRD section 9, pyproject.toml (ruff, pytest with an "e2e" marker excluded by default, coverage).
- Write 3 smoke tests (health 200, ready 200, home 200) and one test that ProdConfig refuses the default SECRET_KEY.

Do not implement models, auth, slots or bookings. Do not add any dependency that is not in requirements*.txt. Do not create Docker, Jenkins, Kubernetes, Terraform or Ansible files.

Run: pip install -r requirements-dev.txt, then ruff check ., ruff format --check ., pytest. Paste the real output.
After the first successful install run pip freeze into requirements.lock and commit it.
Make small Conventional Commits, push, open a PR into develop using the PR template, print the report from AGENTS.md section 9, then stop.
```

Human check before merging: run the app yourself (`flask --app wsgi run`), open /health in a browser, read every file the agent created, and leave at least one real review comment on the PR (a question or a defect). Copy the PR link into docs/evidence/.

### P1: Models, migrations, seed (B-01, Task 5)

```
Read AGENTS.md, docs/PRD.md (sections 5 and 7, FR-17) and docs/TASKS.md item B-01.
Work item: B-01. Create branch feature/b01-models from the latest develop.

Implement the four models exactly as PRD section 7, including the two partial unique indexes, using SQLAlchemy 2.0 style. Create the first Flask-Migrate migration and commit the migrations folder. Verify "flask --app wsgi db upgrade" works on a fresh SQLite file. Write scripts/seed.py (idempotent: running it twice must not create duplicates).

Tests must prove: a second CONFIRMED booking on the same slot is rejected by the database itself (not just by code); the same traveler cannot hold two active bookings on one slot; seed twice gives identical row counts.

Do not build routes or forms. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

Human check: open the migration file and read the partial index definitions. If the where-clauses are missing, do not merge; ask the agent to fix and prove it with a test.

### P2: Authentication (B-02, Task 5)

```
Read AGENTS.md, docs/PRD.md (FR-01 to FR-04, sections 8 and 9) and docs/TASKS.md item B-02.
Work item: B-02. Create branch feature/b02-auth from the latest develop.

Implement register, login and logout with Flask-Login and Flask-WTF. Use the exact element ids and data-testid values from PRD section 9. Enforce: unique case-insensitive email, password of at least 8 characters, city required for guides, one generic error for failed login, logout as a CSRF-protected POST. The navigation must change with login state and role.

Write unit and integration tests for every rule. Increment nothing in metrics yet. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

Human check: register in a real browser as both roles, try a duplicate email, and read the password handling code. You must be able to explain how the password is stored.

### P3: Guide slots (B-03, Task 5)

```
Read AGENTS.md, docs/PRD.md (FR-05 to FR-07, BR-01 to BR-03, BR-08) and docs/TASKS.md item B-03.
Work item: B-03. Create branch feature/b03-guide-slots from the latest develop.

Implement create, list and deactivate for a guide's own slots. Put all rules in app/services/slots.py (future start, duration 30 minutes to 12 hours, no overlap with the guide's other active slots) and keep the routes thin. Travelers must get 403 on guide pages; another guide's slot must give 404. Use now_ist() for every time comparison and inject time in tests.

Write unit tests for the service and integration tests for the routes. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

### P4: Browse slots (B-04, Task 5)

```
Read AGENTS.md, docs/PRD.md (FR-08, FR-09, section 9) and docs/TASKS.md item B-04.
Work item: B-04. Create branch feature/b04-browse-slots from the latest develop.

Implement the public /slots list with city and date filters and the slot detail page. Only active, future slots without a CONFIRMED booking may appear, ordered by start time ascending. Show the empty-state element when nothing matches. Also implement GET /api/v1/slots returning JSON with the same filters.

Write tests that cover every filter combination and the exclusion rules. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

Human check after P4 (Task 5 evidence): you now have four merged PRs. Pick the two most interesting ones and document the branch, commits, PR, your review comments and the merge in docs/task-05.md.

### P5: Booking service and actions (B-05, Task 6)

```
Read AGENTS.md, docs/PRD.md (FR-10 to FR-12, FR-15, BR-04 to BR-07, section 6) and docs/TASKS.md item B-05.
Work item: B-05. Create branch feature/b05-booking-service from the latest develop.

First write the unit tests for every row of the state machine in PRD section 6 and every rejected case, then implement app/services/bookings.py so they pass. Each transition must change the status and insert its booking_events row in one transaction. Add the request, confirm and cancel routes with ownership checks: wrong role gives 403, someone else's booking gives 404, any action on a started slot is rejected. Confirming must auto-cancel competing PENDING bookings; cancelling a CONFIRMED booking must free the slot.

Do not build the booking list or detail pages yet. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

Human check: this is the most important PR. Read the service file line by line. Try to break it: book the same slot from two travelers, confirm one, cancel it. You should be able to draw the state machine from memory.

### P6: Booking pages (B-06, Task 6)

```
Read AGENTS.md, docs/PRD.md (FR-13, FR-14, section 9) and docs/TASKS.md item B-06.
Work item: B-06. Create branch feature/b06-booking-pages from the latest develop.

Implement /bookings (traveler sees own bookings, guide sees bookings on own slots, newest first) and /bookings/<id> with confirm and cancel buttons where allowed and the status timeline. Use the exact selectors from PRD section 9; status text must be exactly PENDING, CONFIRMED or CANCELLED. Write integration tests including the 404 case for another user's booking. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

### P7: Metrics and request logging (B-07, Task 6)

```
Read AGENTS.md, docs/PRD.md (section 10) and docs/TASKS.md item B-07.
Work item: B-07. Create branch feature/b07-metrics from the latest develop.

Implement /metrics with prometheus_client and every required metric in PRD section 10. The endpoint label must be the Flask URL rule, never the raw path. Increment lgb_bookings_transitions_total inside the booking service, count registrations by role and slot creations, and add one stdout log line per request (method, path, status, duration in ms). Add the lgb_bookings_current gauge computed at scrape time if it stays simple.

Tests: /metrics returns 200 and contains each metric name after exercising the routes; a test proves that a password submitted to /login never appears in captured logs. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

### P8: UI polish and error pages (B-08, Task 6)

```
Read AGENTS.md, docs/PRD.md (FR-18, NFR-08, section 9) and docs/TASKS.md item B-08.
Work item: B-08. Create branch feature/b08-ui-polish from the latest develop.

Add a clean, minimal, responsive stylesheet in app/static, labelled inputs, page titles, and custom 403, 404 and 500 pages that show no stack traces or internals. Do not use a CSS framework that needs a build step. Do not rename or remove any selector from PRD section 9; add a test that asserts the important ones exist on each page. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

### P9: Test hardening (B-09, Task 6)

```
Read AGENTS.md, docs/PRD.md (NFR-06 and the negative checks at the end of section 13) and docs/TASKS.md item B-09.
Work item: B-09. Create branch feature/b09-test-hardening from the latest develop.

Make sure every negative check in PRD section 13 has a test. Run pytest --cov=app --cov-report=term-missing, then add meaningful tests for the important uncovered lines (do not write empty tests just to move a number). Target: at least 80 percent coverage of app/. Run bandit -r app -q and fix or explain every finding. Do not weaken production code to make tests easier. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report with the real coverage table, then stop.
```

After P9 merges: tag `v0.1.0` yourself and complete the Task 6 conflict exercise (see docs/TASKS.md, human-only steps).

### P10: Selenium suite (B-10, Task 9)

```
Read AGENTS.md, docs/PRD.md (sections 9 and 13) and docs/TASKS.md item B-10.
Work item: B-10. Create branch feature/b10-selenium from the latest develop.

Implement journeys J1 to J5 from PRD section 13 in tests/e2e using pytest and Selenium WebDriver (Python). Rules: mark every test with the e2e marker so the default pytest run skips them; BASE_URL from the environment (default http://localhost:8000); E2E_HEADLESS defaults to 1; use SELENIUM_REMOTE_URL when it is set (for a Selenium Grid) and local Chrome otherwise; explicit waits only (WebDriverWait), never time.sleep; each journey creates its own uniquely named users; on any failure save a screenshot into test-artifacts/. Use only the selectors from PRD section 9.

Put a README section in the PR description explaining exactly how to run them against a live instance. Commit in small steps, push, open a PR into develop, print the AGENTS.md section 9 report, then stop.
```

Human check: run the suite yourself against `flask run` on your laptop, then deliberately break a selector and watch a failure screenshot appear. That failure is Task 10 evidence.

## Part 2: Coach prompts for Tasks 7 to 15 (do not ask the agent to write these for you)

Tasks 7 to 15 (Jenkins, Docker, Kubernetes, ArgoCD, Ansible, Sonar, Trivy, Prometheus) are the part you will be asked about in the viva and in interviews. If an AI writes them, you cannot defend them. Use the agent as a tutor, reviewer and examiner instead. Replace the placeholders in angle brackets before pasting.

### C1: Explain before I build

```
I am about to do course Task <number>: <title>. Do not write the solution or any config file. In 10 lines explain the concept and why it exists. Then list the exact steps in the order I should do them, five things that commonly break for beginners, and ask me three questions to check my understanding. Wait for my answers before saying anything else.
```

### C2: Review what I wrote

```
Act as a strict senior DevOps engineer. Below is the file I wrote for Task <number>. List defects and risks by severity (blocker, major, minor), explain why each matters, and tell me what to search or read to fix it. Do not rewrite the file and do not paste corrected code.
<paste your file>
```

### C3: Break it on purpose

```
My pipeline or cluster for Task <number> works. Give me three realistic faults I can inject (for example a wrong image tag, a failing quality gate, a missing secret, a bad readiness probe) and the symptoms I should see. Do not tell me the fixes until I ask. After I fix each one, ask me to explain the root cause.
```

The faults you inject and fix become the "Problems faced" section of the task report. That section is real evidence and earns viva marks.

### C4: Viva drill

```
You are the examiner for course Task <number>: <title>. My project is described in AGENTS.md and docs/PRD.md. Ask me one question at a time, getting harder each time. After each answer give a score out of 10, tell me exactly what I missed, then ask the next question. Stop after ten questions and summarise my weak areas.
```

### C5: Turn my notes into the task report

```
Use docs/templates/task-template.md. Below are my raw notes, commands and log excerpts for Task <number>. Write the report sections from them. Do not invent commands, outputs, versions, screenshots or results. Where evidence is missing, write TODO(student) and say what I should capture.
<paste notes and logs>
```

## Part 3: Recovery prompts

If the agent commits or pushes to `main` or `develop`:

```
Stop. Do not run any git command that rewrites history and do not force-push. Show me the output of git status, git log --oneline --graph -15 and git branch -vv. Then explain what went wrong and propose a fix that only adds new commits or new branches. Wait for my approval.
```

If the agent starts the next work item or creates DevOps files you did not ask for:

```
Stop. You created files outside the current work item (list them). Revert those files on this branch, keep only what the current work item needs, and re-run the tests. Read AGENTS.md sections 7 and 8 again and confirm you will follow them.
```

If tests fail and the agent wants to weaken them:

```
Do not delete, skip or loosen any test to make it pass. Explain the root cause of the failure, show the failing assertion, and fix the production code, or tell me which PRD requirement the test contradicts so I can decide.
```

Log every AI-assisted step in docs/AI-USAGE-LOG.md as you go.
