# Task tracker and build work items

Two lists live here. Part A tracks the 15 course tasks (what gets graded). Part B lists the work items the coding agent builds for the web application. Sprint dates and story details are in docs/task-02.md.

## Part A: the 15 course tasks

| # | Task | Who builds it | Depends on | Sprint | Status |
|---|---|---|---|---|---|
| 1 | Problem Definition and Scope | Student (drafted in the kit, needs validation) | none | 1 | Drafted |
| 2 | Agile Planning and DevOps Workflow | Student (drafted in the kit, needs board) | 1 | 1 | Drafted |
| 3 | Requirements, Architecture and Technology Setup | Student with Claude | 1, 2 | 1 | Todo |
| 4 | Git and GitHub Repository Initialization | Student (repos), agent (skeleton, B-00) | 3 | 1 | Todo |
| 5 | Feature Development with Branching | Agent builds B-01 to B-04, student reviews and merges | 4 | 1 | Todo |
| 6 | MVP Completion and Git Collaboration | Agent builds B-05 to B-07, student creates conflict and tag | 5 | 1 | Todo |
| 7 | Jenkins Installation and Continuous Integration Job | Student (coach prompts only) | 6 | 2 | Todo |
| 8 | Pipeline as Code and Deployment | Student (coach prompts only) | 7 | 2 | Todo |
| 9 | Selenium Test Design and Local Execution | Agent writes tests B-10, student runs and explains | 6 | 2 | Todo |
| 10 | Continuous Testing and Quality Gates in Jenkins | Student | 8, 9 | 2 | Todo |
| 11 | Docker Image and Container Lifecycle | Student | 6 | 2 | Todo |
| 12 | Jenkins-Docker Continuous Delivery | Student | 10, 11 | 2 | Todo |
| 13 | Configuration Management and Cluster Setup | Student | 8 | 3 | Todo |
| 14 | Automated Provisioning, GitOps and Reliability Validation | Student | 12, 13 | 3 | Todo |
| 15 | Final End-to-End Release, Observability, Documentation and Viva | Student | all | 3 | Todo |

Status values: Todo, Drafted, In progress, Done (evidence captured and documented).

## Part B: build work items for the coding agent

Rules for every item: follow AGENTS.md; branch `feature/<id>-<slug>` from `develop`; PR into `develop`; stop after opening the PR. Prompts for each item are in docs/PROMPTS.md.

### B-00 App skeleton (Task 4)
Branch: `feature/b00-app-skeleton` | PRD: sections 8 (ops routes only), 9 (nav), 11, 12
- [ ] Application factory, config classes, extensions, `wsgi.py`, `pyproject.toml` (ruff, pytest with `e2e` marker, coverage).
- [ ] `/health` and `/ready` working; base template with navigation from PRD section 9; landing page `/`.
- [ ] Three smoke tests pass; ruff clean; app starts with `flask --app wsgi run`.
- [ ] Prod config refuses the default SECRET_KEY (test proves it).

### B-01 Models, migrations, seed (Task 5)
Branch: `feature/b01-models` | PRD: sections 5, 7, 4 (FR-17)
- [ ] Models for users, slots, bookings, booking_events exactly as PRD section 7.
- [ ] First migration committed; `flask --app wsgi db upgrade` works on a fresh SQLite file.
- [ ] Partial unique indexes present and proven by tests (second CONFIRMED on a slot is rejected by the database).
- [ ] `scripts/seed.py` is idempotent (run twice, same row counts). `now_ist()` exists in `app/timeutils.py`.

### B-02 Authentication (Task 5)
Branch: `feature/b02-auth` | PRD: FR-01 to FR-04, sections 8, 9
- [ ] Register, login, logout with Flask-Login and Flask-WTF; selectors exactly as PRD section 9.
- [ ] Duplicate email rejected (case-insensitive); guide without city rejected; short password rejected.
- [ ] Generic login error message; logout is a CSRF-protected POST.
- [ ] Tests for each rule above plus the nav changing with role.

### B-03 Guide slots (Task 5)
Branch: `feature/b03-guide-slots` | PRD: FR-05 to FR-07, BR-01 to BR-03
- [ ] Guide can create, list and deactivate own slots; travelers get 403 on guide pages.
- [ ] Past start, bad duration and overlap are rejected with a clear message.
- [ ] Rules live in `app/services/slots.py` with unit tests; routes stay thin.

### B-04 Browse slots (Task 5)
Branch: `feature/b04-browse-slots` | PRD: FR-08, FR-09
- [ ] Public `/slots` with city and date filters; only active, future, not-confirmed slots appear; ascending by start time.
- [ ] Slot detail page; empty-state element when nothing matches.
- [ ] Should have: `/api/v1/slots` JSON with the same filters.

### B-05 Booking service and actions (Task 6)
Branch: `feature/b05-booking-service` | PRD: FR-10 to FR-12, FR-15, BR-04 to BR-07, section 6
- [ ] `app/services/bookings.py` implements every row of the state machine; one transaction per transition including the event row.
- [ ] Request, confirm and cancel routes with ownership checks (403 wrong role, 404 other user's resource).
- [ ] Unit tests for every transition and every rejected case; integration tests for the three routes.
- [ ] Auto-cancel of competing PENDING bookings on confirm; slot becomes available again on cancel of CONFIRMED.

### B-06 Booking pages (Task 6)
Branch: `feature/b06-booking-pages` | PRD: FR-13, FR-14, section 9
- [ ] `/bookings` list (traveler and guide views) and `/bookings/<id>` detail with timeline.
- [ ] Selectors exactly as PRD section 9; status text exactly PENDING, CONFIRMED or CANCELLED.

### B-07 Metrics and request logging (Task 6, also feeds Task 15)
Branch: `feature/b07-metrics` | PRD: section 10
- [ ] `/metrics` exposes every required metric; endpoint label uses the URL rule, not the raw path.
- [ ] Booking transitions increment `lgb_bookings_transitions_total`; registrations and slot creations are counted.
- [ ] One log line per request to stdout; a test proves no password appears in logs.

### B-08 UI polish and error pages (Task 6)
Branch: `feature/b08-ui-polish` | PRD: FR-18, NFR-08
- [ ] Clean minimal CSS in `app/static/`, responsive layout, labelled inputs, page titles.
- [ ] Custom 403, 404, 500 pages; no stack traces in prod mode.
- [ ] All selectors from PRD section 9 still present (a test checks the important ones).

### B-09 Test hardening (Task 6)
Branch: `feature/b09-test-hardening` | PRD: NFR-06, section 13 negative checks
- [ ] Every negative check in PRD section 13 has a test. Coverage of `app/` at least 80 percent.
- [ ] `bandit -r app -q` reports no high-severity findings.

### B-10 Selenium suite (Task 9)
Branch: `feature/b10-selenium` | PRD: section 13
- [ ] `tests/e2e/` implements journeys J1 to J5 with pytest and Selenium WebDriver, marked `e2e`, excluded from default `pytest`.
- [ ] Explicit waits only; unique users per journey; `BASE_URL` and `E2E_HEADLESS` from environment; failure screenshot to `test-artifacts/`.
- [ ] `docs` section in the PR describing how to run against a live instance and against a Selenium Grid via `SELENIUM_REMOTE_URL`.

## Human-only steps (agent must not do these)

- Create the GitHub repositories, branch protection, labels, issues and the Projects board (Tasks 2 and 4).
- Review every agent PR with real comments, then merge (Task 5).
- Create a deliberate merge conflict and resolve it; create tag `v0.1.0` (Task 6).
- Everything in Tasks 7 to 15 (use the coach prompts in docs/PROMPTS.md).
