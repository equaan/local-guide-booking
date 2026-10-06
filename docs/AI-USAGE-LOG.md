# AI usage log

Honesty rule: I use AI to go faster, not to skip understanding. Before merging or submitting anything, I must be able to explain every line and re-create it without the AI. If I cannot, it does not go in.

| Date | Task or work item | Tool | What I asked for | What it produced | What I reviewed, ran or changed | Evidence (PR or commit link) |
|---|---|---|---|---|---|---|
| 2026-09-30 | B-00 app skeleton | Codex | Implement the B-00 prompt after pre-flight setup | Factory, config, ops routes, templates and smoke tests | Pending student review and command verification | Pending PR |
| 2026-09-30 | B-01 models, migrations, seed | Codex | Implement the B-01 prompt after B-00 merged | Models, migration, idempotent seed script and constraint tests | Pending student review and command verification | Pending PR |
| 2026-10-01 | B-02 authentication | GitHub Copilot | Implement the B-02 prompt after B-01 merged | Registration, login, logout, navigation state and auth tests | Tests, Ruff and Bandit run; pending student review | Pending PR |
| 2026-10-01 | B-03 guide slots | GitHub Copilot | Implement the B-03 prompt after B-02 merged | Slot service rules, guide routes, forms, templates and tests | Tests, Ruff and Bandit run; pending student review | Pending PR |
| 2026-10-06 | B-05 booking service | Codex | Repair and complete the existing B-05 state-machine branch | Atomic request, confirm, cancel service; action routes; forms; unit and integration tests | Ran pytest (39 passed), Ruff, coverage (90%), and Bandit; pending student review | Pending PR |
| 2026-10-07 | B-06 booking pages | Codex | Rebuild B-06 from the merged B-05 baseline | Role-scoped booking list and detail pages with a status timeline and action controls | Ran pytest (44 passed), Ruff, coverage (91%), and Bandit; pending student review | Pending PR |
| 2026-10-07 | B-07 metrics and logging | Codex | Implement observability metrics and request logging from the merged B-06 baseline | Prometheus endpoint, lifecycle counters and password-safe request logs | Ran pytest (46 passed), Ruff, coverage (92%), and Bandit; pending student review | Pending PR |
| 2026-10-07 | B-08 UI polish and error pages | Codex | Apply the workspace design system while preserving the PRD selector contract | Responsive CSS, accessible labels, custom safe errors, and selector contract tests | Ran pytest (48 passed), Ruff, coverage (92%), Bandit, and a local live-page check; pending student review | Pending PR |
| 2026-10-07 | B-09 test hardening | Codex | Audit section 13 negative checks and add meaningful failure-path coverage | Booking action validation, missing-resource, started-slot cancellation, and readiness failure tests | Ran pytest (51 passed), Ruff, coverage (94%), and Bandit; pending student review | Pending PR |

## Viva self-check (tick before each task is marked Done)

- [ ] I ran every command myself on my own machine.
- [ ] I can explain each config file or code file line by line.
- [ ] I broke it on purpose at least once and fixed it (Problems faced section filled in).
- [ ] The evidence in the report is real, not generated.
