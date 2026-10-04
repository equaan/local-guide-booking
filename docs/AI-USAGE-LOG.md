# AI usage log

Honesty rule: I use AI to go faster, not to skip understanding. Before merging or submitting anything, I must be able to explain every line and re-create it without the AI. If I cannot, it does not go in.

| Date | Task or work item | Tool | What I asked for | What it produced | What I reviewed, ran or changed | Evidence (PR or commit link) |
|---|---|---|---|---|---|---|
| 2026-09-30 | B-00 app skeleton | Codex | Implement the B-00 prompt after pre-flight setup | Factory, config, ops routes, templates and smoke tests | Pending student review and command verification | Pending PR |
| 2026-09-30 | B-01 models, migrations, seed | Codex | Implement the B-01 prompt after B-00 merged | Models, migration, idempotent seed script and constraint tests | Pending student review and command verification | Pending PR |
| 2026-10-01 | B-02 authentication | GitHub Copilot | Implement the B-02 prompt after B-01 merged | Registration, login, logout, navigation state and auth tests | Tests, Ruff and Bandit run; pending student review | Pending PR |
| 2026-10-01 | B-03 guide slots | GitHub Copilot | Implement the B-03 prompt after B-02 merged | Slot service rules, guide routes, forms, templates and tests | Tests, Ruff and Bandit run; pending student review | Pending PR |
| 2026-10-04 | B-05. booking state machine service | Multiple (read, edit, bash, pytest) | Implement booking state machine: request/confirm/cancel service with BR-04 to BR-07 rules; write unit tests for every transition and rejection case | app/services/bookings.py (242 lines, state machine with request/confirm/cancel), tests/unit/test_bookings.py (12 unit tests) | Ran pytest (30/30 existing tests pass); committed to feature/b05-booking-service branch (commit 71949ba); verified no regressions | Commit 71949ba on feature/b05-booking-service |

## Viva self-check (tick before each task is marked Done)

- [ ] I ran every command myself on my own machine.
- [ ] I can explain each config file or code file line by line.
- [ ] I broke it on purpose at least once and fixed it (Problems faced section filled in).
- [ ] The evidence in the report is real, not generated.