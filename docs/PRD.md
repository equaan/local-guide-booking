# Product Requirements Document: Local Guide Booking System

Version 1.0 (scope frozen) | Owner: Mohammad Equaan Kacchi | Section numbers below are referenced by docs/PROMPTS.md. Do not renumber.

## 1. Overview

The Local Guide Booking System (LGBS) lets travelers find a local guide's availability slots and request a booking. Guides confirm or cancel requests. Both sides can see the status history of every booking.

The application is intentionally small. The graded and portfolio value is the DevSecOps delivery pipeline around it (Jenkins, SonarQube, Trivy, Selenium, Docker Hub, ArgoCD, Kubernetes, Prometheus/Grafana). Build the app to be simple, correct, testable and observable. Do not gold-plate features.

## 2. Roles

| Role | Description | Can do |
|---|---|---|
| Visitor | Not logged in | View landing page, browse slots, register, log in |
| Traveler | Registered user | Everything a visitor can, plus request bookings, cancel own bookings, view own bookings |
| Guide | Registered user with a city | Create and deactivate own slots, view bookings on own slots, confirm or cancel them |

- A user has exactly one role, chosen at registration. It cannot be changed.
- There is no admin role in the MVP.

## 3. Scope

In scope: FR-01 to FR-18 in section 4.

Out of scope (do not build, do not stub): payments, ratings and reviews, chat or messaging, email or SMS notifications, maps, guide identity verification, admin panel, password reset, social login, multi-language support, timezone handling, image uploads, recurring slots.

## 4. Functional requirements

Accounts
- FR-01 A visitor can register with name, email, password and role (traveler or guide). Guides must also give a city. Bio is optional.
- FR-02 Email is unique (case-insensitive, stored lowercase). Password is at least 8 characters.
- FR-03 Users can log in and log out. A failed login shows one generic error message that does not reveal whether the email exists.
- FR-04 The navigation bar reflects login state and role (section 9).

Slots (guide)
- FR-05 A guide can create a slot with title, start time, end time and price in INR (integer, zero or more).
- FR-06 A guide can list their own slots with a derived status: available, booked, inactive or past.
- FR-07 A guide can deactivate a slot that has no CONFIRMED booking. Deactivating auto-cancels its PENDING bookings (actor: system, reason: slot deactivated).

Browsing (public)
- FR-08 Anyone can list available slots (active, in the future, no CONFIRMED booking), ordered by start time ascending. Filters: city (case-insensitive exact match) and date.
- FR-09 Anyone can open a slot detail page showing guide name, city, bio, time range, price and availability.

Bookings
- FR-10 A traveler can request a booking for an available slot with an optional note (max 300 characters). The booking starts as PENDING.
- FR-11 The guide who owns the slot can confirm a PENDING booking. It becomes CONFIRMED and every other PENDING booking on that slot is auto-cancelled (actor: system, reason: slot taken).
- FR-12 The booking's traveler or the slot's guide can cancel a PENDING or CONFIRMED booking before the slot starts. Optional reason (max 200 characters).
- FR-13 My Bookings: a traveler sees their own bookings; a guide sees bookings on their own slots. Newest first.
- FR-14 Booking detail shows a status timeline: every transition with from-status, to-status, actor and time.
- FR-15 Cancelling a CONFIRMED booking makes the slot available again.

Operations and quality
- FR-16 The app exposes /health, /ready and /metrics (section 10).
- FR-17 `scripts/seed.py` creates demo data (2 guides, 2 travelers, about 6 future slots) and is idempotent: running it twice creates no duplicates.
- FR-18 Custom 403, 404 and 500 pages with safe messages (no stack traces, no internals).

## 5. Business rules

- BR-01 A slot's start time must be in the future when created.
- BR-02 A slot's end time must be after its start time; duration between 30 minutes and 12 hours.
- BR-03 A guide's active slots must not overlap each other.
- BR-04 At most one CONFIRMED booking per slot. This must be enforced by the database, not only by code.
- BR-05 A traveler cannot hold two active (PENDING or CONFIRMED) bookings for the same slot.
- BR-06 No booking action (request, confirm, cancel) is allowed once the slot has started.
- BR-07 Authorization: wrong role gets 403. Another user's booking or a guide-only resource owned by someone else gets 404 (do not leak existence).
- BR-08 All datetimes are stored naive and interpreted as India Standard Time (Asia/Kolkata). "Now" comes from one helper, `now_ist()` in `app/timeutils.py`, built on `zoneinfo`. Never call `datetime.now()` or `datetime.utcnow()` elsewhere. Reason: containers run in UTC, which would silently shift past/future checks by 5.5 hours.

## 6. Booking state machine

| From | Action | Actor | To | Side effects |
|---|---|---|---|---|
| (none) | request | traveler | PENDING | event recorded |
| PENDING | confirm | slot's guide | CONFIRMED | other PENDING bookings on the slot become CANCELLED (actor system) |
| PENDING | cancel | traveler or slot's guide | CANCELLED | event recorded |
| CONFIRMED | cancel | traveler or slot's guide | CANCELLED | slot becomes available again |
| CANCELLED | any | any | rejected | 409 Conflict / flash error |

All transitions live in one service module (`app/services/bookings.py`). Routes call the service and never change status directly. Every transition writes one row to `booking_events` in the same database transaction as the status change.

## 7. Data model

users
- id (PK), name (str 80, required), email (str 254, unique, lowercase), password_hash (str 255), role (traveler or guide), city (str 80, null), bio (str 500, null), created_at.

slots
- id (PK), guide_id (FK users), title (str 120), start_at (datetime), end_at (datetime), price_inr (int, default 0), is_active (bool, default true), created_at.
- Index on (guide_id, start_at).

bookings
- id (PK), slot_id (FK slots), traveler_id (FK users), status (PENDING, CONFIRMED or CANCELLED), note (str 300, null), created_at, updated_at.
- Partial unique index on (slot_id) where status = 'CONFIRMED' (BR-04).
- Partial unique index on (slot_id, traveler_id) where status in ('PENDING', 'CONFIRMED') (BR-05).

booking_events
- id (PK), booking_id (FK bookings), from_status (null for the first event), to_status, actor_id (FK users, null means system), reason (str 200, null), created_at.

Implementation notes
- SQLAlchemy 2.0 style (`Mapped`, `mapped_column`, `select()`), Flask-SQLAlchemy 3.x.
- Schema changes go through Flask-Migrate (Alembic). Commit the `migrations/` folder. `db.create_all()` is allowed only in tests.
- Partial unique indexes: use `Index(..., unique=True, sqlite_where=text(...), postgresql_where=text(...))`. If Alembic autogenerate drops the where-clause, edit the migration by hand and add a test that proves the constraint rejects a violation.
- Default database is SQLite (dev and test). PostgreSQL must also work via `DATABASE_URL` (used later in Kubernetes).

## 8. Routes

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | / | public | Landing page with links |
| GET, POST | /register | visitor | FR-01, FR-02 |
| GET, POST | /login | visitor | FR-03 |
| POST | /logout | logged in | FR-03 |
| GET | /slots | public | FR-08 (query: city, date) |
| GET | /slots/`<int:slot_id>` | public | FR-09 |
| POST | /slots/`<int:slot_id>`/book | traveler | FR-10 |
| GET | /bookings | logged in | FR-13 |
| GET | /bookings/`<int:booking_id>` | traveler owner or slot's guide | FR-14 |
| POST | /bookings/`<int:booking_id>`/confirm | slot's guide | FR-11 |
| POST | /bookings/`<int:booking_id>`/cancel | traveler owner or slot's guide | FR-12 |
| GET | /guide/slots | guide | FR-06 |
| GET, POST | /guide/slots/new | guide | FR-05 |
| POST | /guide/slots/`<int:slot_id>`/deactivate | slot's guide | FR-07 |
| GET | /health | public | FR-16 |
| GET | /ready | public | FR-16 |
| GET | /metrics | public | FR-16 |
| GET | /api/v1/slots | public | Should have: JSON version of FR-08 |

- Every POST is CSRF-protected with Flask-WTF. There are no CSRF exemptions. Logout is a POST form button.
- After a successful POST, redirect (Post/Redirect/Get) and show a flash message.
- Server-rendered Jinja2 templates. No JavaScript framework. Minimal JavaScript is allowed only if a requirement cannot be met without it.

## 9. UI contract (stable selectors)

Selenium tests (Task 9) depend on these exact attributes. Do not rename them without updating this table and the tests.

Global
- Flash message container: `data-testid="flash"` with class `flash-success` or `flash-error`.
- Navigation links (rendered only when applicable): `data-testid="nav-slots"`, `nav-bookings`, `nav-guide-slots` (guides only), `nav-login`, `nav-register`, `nav-logout` (a button in a POST form).
- Greeting when logged in: `data-testid="nav-user"` containing the user's name.

Forms (element ids)
- Register: `#name`, `#email`, `#password`, `#role` (select with values `traveler` and `guide`), `#city`, `#bio`, `#submit-register`. City and bio are always rendered; city is required only for guides.
- Login: `#email`, `#password`, `#submit-login`.
- New slot: `#title`, `#start_at` (input type datetime-local), `#end_at`, `#price_inr`, `#submit-slot`.
- Slot filters: `#filter-city`, `#filter-date`, `#apply-filter`.
- Booking request on slot detail: `#note`, `#book-btn`.

Lists and details
- Slot list rows: `data-testid="slot-row"` with attribute `data-slot-id`. Each row has a link `data-testid="slot-link"`.
- Guide slot list rows: `data-testid="guide-slot-row"` with `data-slot-id` and a `data-testid="slot-status"` element whose text is one of available, booked, inactive, past.
- Booking list rows: `data-testid="booking-row"` with `data-booking-id`, containing `data-testid="booking-status"` whose text is exactly PENDING, CONFIRMED or CANCELLED.
- Booking detail: buttons `#confirm-btn` (guide, PENDING only) and `#cancel-btn` (when allowed); optional `#reason` input for cancel; timeline items `data-testid="timeline-item"`.
- Empty states use `data-testid="empty-state"`.

## 10. Operational endpoints and metrics

- GET /health: liveness. Always HTTP 200 with JSON `{"status": "ok", "version": "<APP_VERSION>", "git_sha": "<GIT_SHA>"}`. Must not touch the database.
- GET /ready: readiness. Runs `SELECT 1`. HTTP 200 `{"status": "ready"}` or HTTP 503 `{"status": "not ready"}`.
- GET /metrics: Prometheus text format via `prometheus_client`. Required metrics:
  - `lgb_http_requests_total{method, endpoint, status}` counter. `endpoint` is the Flask URL rule (for example `/slots/<int:slot_id>`), never the raw path, to keep label cardinality bounded.
  - `lgb_http_request_duration_seconds{endpoint}` histogram.
  - `lgb_bookings_transitions_total{from_status, to_status}` counter, incremented by the booking service.
  - `lgb_users_registered_total{role}` counter.
  - `lgb_slots_created_total` counter.
  - Should have: `lgb_bookings_current{status}` gauge, computed at scrape time.
- Logging: standard `logging` to stdout, one line per request (method, path, status, duration ms) plus errors with tracebacks. Never log passwords, session cookies or the SECRET_KEY.

## 11. Non-functional requirements

- NFR-01 Security: passwords hashed with Werkzeug `generate_password_hash`; CSRF on all POSTs; session cookie HttpOnly and SameSite=Lax (Secure when APP_ENV is prod); SECRET_KEY only from environment; app refuses to start in prod with the default SECRET_KEY; every booking action checks ownership (BR-07); SQLAlchemy parameterised queries only (no string-built SQL); user-supplied text is escaped by Jinja autoescape.
- NFR-02 Performance: p95 latency under 500 ms for page routes on a laptop-class machine with 20 concurrent users (measured later from the histogram).
- NFR-03 Reliability: graceful start and stop under gunicorn; /ready reflects database health.
- NFR-04 Observability: section 10.
- NFR-05 Portability (12-factor): all configuration from environment variables; logs to stdout; app is stateless apart from the database; listens on 0.0.0.0 at `$PORT` (default 8000); writes no files outside the database and the temp directory.
- NFR-06 Testability: at least 80 percent line coverage on `app/`; tests are deterministic (no sleeps; inject time through `now_ist()`); no network access in unit and integration tests.
- NFR-07 Maintainability: `ruff check` and `ruff format --check` clean; type hints on service-layer functions; business rules only in `app/services/`.
- NFR-08 Accessibility (basic): every form input has a `<label>`; semantic HTML; page titles set.
- NFR-09 Compatibility: Python 3.11 or newer (target 3.12). Code must run on Windows, Linux and macOS (use `pathlib`, no OS-specific calls).

## 12. Configuration

| Variable | Default | Notes |
|---|---|---|
| APP_ENV | dev | dev, test or prod |
| SECRET_KEY | (none in prod) | Required when APP_ENV is prod |
| DATABASE_URL | sqlite:///app.db | PostgreSQL URL later in Kubernetes |
| LOG_LEVEL | INFO | |
| APP_VERSION | dev | Set by the image build later |
| GIT_SHA | local | Set by the pipeline later |
| PORT | 8000 | |

## 13. Acceptance journeys

These five journeys are the end-to-end acceptance tests. Task 9 automates them with Selenium. Each journey must create its own uniquely named users (random email suffix) so journeys never depend on each other or on seed data.

- J1 Registration and login: a visitor registers as a traveler, is logged in, sees their name in the nav, logs out, logs back in.
- J2 Guide publishes availability: a guide registers with a city, creates a future slot, and the slot appears in the public slot list filtered by that city.
- J3 Booking request: a traveler opens the slot, submits a request with a note, and My Bookings shows the booking with status PENDING.
- J4 Confirmation: the guide opens the booking and confirms it. The traveler sees CONFIRMED and the slot no longer appears in the public list.
- J5 Cancellation: the traveler cancels the CONFIRMED booking. Status shows CANCELLED, the timeline has three items (requested, confirmed, cancelled) and the slot appears in the public list again.

Negative checks that must also be covered by tests (unit or integration): duplicate email is rejected; overlapping slots are rejected; a second CONFIRMED booking on the same slot is rejected by the database; a traveler cannot open another traveler's booking (404); a traveler cannot open guide pages (403); actions on a started slot are rejected.
