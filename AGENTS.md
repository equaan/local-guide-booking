# AGENTS.md: instructions for coding agents (Codex and similar)

Read this file, `docs/PRD.md` and `docs/TASKS.md` completely before writing code. If they conflict, the order of authority is: PRD, then TASKS, then this file. If something is ambiguous, ask or write the question in the PR description. Do not guess silently.

## 1. Project in one paragraph

Local Guide Booking System: a small Flask web app where travelers request bookings on guides' availability slots and guides confirm or cancel. It is the demo application for a DevSecOps CI/CD project (Jenkins, SonarQube, Trivy, Selenium, Docker Hub, ArgoCD, Kubernetes, Prometheus/Grafana). The student is graded on understanding and on the git history, so the process rules below matter as much as the code.

## 2. Stack

- Python 3.11 or newer (target 3.12), Flask 3, Flask-SQLAlchemy 3 (SQLAlchemy 2.0 style), Flask-Migrate, Flask-Login, Flask-WTF, Jinja2 templates, prometheus_client, gunicorn.
- SQLite for dev and test, PostgreSQL must also work through `DATABASE_URL`.
- pytest and pytest-cov, Selenium (Python bindings) for end-to-end tests, Ruff for lint and format, Bandit for security lint.
- The developer machine may be Windows (possibly with WSL2). Keep Python code OS-agnostic. Do not assume bash in Python code.

## 3. Commands

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                 # Windows: copy .env.example .env
flask --app wsgi db upgrade          # apply migrations
python scripts/seed.py               # demo data (idempotent)
flask --app wsgi run --debug         # http://localhost:5000
pytest                               # unit + integration (e2e excluded by default)
pytest --cov=app --cov-report=term-missing
ruff check . && ruff format --check .
bandit -r app -q
pytest -m e2e                        # needs a running app and Chrome (Task 9 only)
```

If a command cannot run in your environment, say so explicitly. Never claim tests passed unless you ran them and can paste the output.

## 4. Target layout

```
app/
  __init__.py          # create_app() application factory
  config.py            # DevConfig, TestConfig, ProdConfig (see PRD section 12)
  extensions.py        # db, migrate, login_manager, csrf
  timeutils.py         # now_ist() and nothing else may call datetime.now()
  models.py
  forms.py
  metrics.py           # prometheus counters and histogram
  services/
    bookings.py        # ALL booking state transitions and rules
    slots.py           # slot creation, overlap check, availability queries
  blueprints/
    auth.py  slots.py  bookings.py  guide.py  ops.py
  templates/           # base.html plus one folder per blueprint
  static/
migrations/
scripts/seed.py
tests/
  unit/  integration/  e2e/
wsgi.py
pyproject.toml         # ruff, pytest (markers: e2e), coverage config
```

## 5. Coding rules

- Application factory pattern. No global app object. No import-time side effects.
- Routes are thin: parse input, call a service function, choose response. Business rules (PRD sections 5 and 6) live only in `app/services/`.
- Use `db.session.execute(select(...))` style. Wrap every state change plus its `booking_events` row in one transaction.
- Time: only `now_ist()` (PRD BR-08). Tests inject time by monkeypatching that helper.
- Type hints on service functions. Short docstrings that explain why, not what.
- Config only from environment. No secrets in code, tests or docs. No `print()` for logging.
- HTML: follow the selector contract in PRD section 9 exactly. Every input has a label.
- Security rules in PRD NFR-01 are mandatory, including ownership checks on every booking route.
- Keep it simple. No extra frameworks, no JavaScript build step, no ORM abstractions beyond what is needed.

## 6. Testing rules

- Every work item ships with tests. Put pure rule tests in `tests/unit`, request-level tests with the Flask test client in `tests/integration`, browser tests in `tests/e2e` marked `@pytest.mark.e2e`.
- Test config: in-memory SQLite, `WTF_CSRF_ENABLED = False`.
- Tests must not sleep, must not need the network (except e2e) and must not share state.
- Overall coverage of `app/` must be at least 80 percent by the end of work item B-09.
- Selenium tests: explicit waits only (`WebDriverWait`), headless Chrome by default, read `BASE_URL` from the environment, save a screenshot to `test-artifacts/` on failure, never depend on seed data.

## 7. Git workflow (CRITICAL: the history is graded evidence)

1. Never commit or push directly to `main` or `develop`.
2. One work item per branch. Branch from an up-to-date `develop`. Name: `feature/<item-id>-<slug>`, for example `feature/b02-auth`.
3. Make several small commits, each one logical change. Use Conventional Commits: `feat(auth): add registration form`, `test(slots): cover overlap rule`, `fix(bookings): ...`, `docs: ...`, `chore: ...`.
4. Push the branch and open a pull request into `develop` using `.github/PULL_REQUEST_TEMPLATE.md`. Use `gh pr create` if the GitHub CLI is available; otherwise print the PR title and body for the student to paste.
5. Do not merge your own pull request. The student reviews, comments and merges.
6. Do not squash, rebase published branches or force-push. Do not delete branches.
7. After opening the PR, stop. Print the summary (section 9) and wait for the next instruction. Do not start the next work item.
8. Never create the merge-conflict exercise or release tags. The student does those by hand (Task 6).

## 8. Do NOT

- Do not create or edit: `Dockerfile`, `docker-compose*`, `Jenkinsfile`, Kubernetes or Helm files, Terraform, Ansible, GitHub Actions. These are the student's graded learning tasks (Tasks 7 to 14) unless a prompt explicitly asks for one.
- Do not edit `docs/task-*.md`, `docs/00-*.md` or `docs/evidence/`. Propose changes to `docs/PRD.md` in the PR description instead of editing it silently.
- Do not add a dependency that is not in `requirements*.txt`. If one is truly needed, stop and ask, explaining why.
- Do not fabricate evidence: no invented test output, coverage numbers, screenshots, commit hashes or URLs.
- Do not commit `.env`, databases, virtual environments, coverage output or screenshots of failures.
- Do not silence a failing test or a lint rule to get green. Fix the cause or report it.

## 9. Definition of done and reporting format

A work item is done when all of these are true:
- Behaviour matches the referenced PRD sections and every acceptance check in `docs/TASKS.md` for that item.
- `pytest`, `ruff check .`, `ruff format --check .` and `bandit -r app -q` pass, and you pasted the real output.
- New behaviour has tests; coverage did not go down.
- The PR description is filled in from the template.

Finish every work item with this report in your final message:
1. What changed (files and behaviour, five lines maximum).
2. How to run and verify (exact commands).
3. Real test, lint and coverage output.
4. Decisions you made that the PRD did not specify.
5. Open questions or risks.
