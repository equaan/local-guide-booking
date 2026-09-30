# Contributing and branch policy

This is a solo academic project, but it follows a real team workflow so the git history shows how the work was done.

## Branches

| Branch | Purpose | Rules |
|---|---|---|
| `main` | Released, tagged, always deployable | Only receives release pull requests from `develop`. Protected. |
| `develop` | Integration branch | Only receives pull requests from feature, fix, docs and chore branches. Protected. |
| `feature/<id>-<slug>` | New behaviour, for example `feature/b02-auth` | Branch from `develop`. Delete never (keep history visible). |
| `fix/<id>-<slug>` | Bug fixes | Same as feature. |
| `docs/<slug>` | Documentation only | Same as feature. |
| `chore/<slug>` | Tooling, config, dependencies | Same as feature. |
| `release/vX.Y.Z` | Optional release preparation | Merged to `main` and tagged. |

## Commits (Conventional Commits)

Format: `type(scope): short imperative summary`. Types: feat, fix, docs, test, refactor, chore, ci, build. Keep commits small and logical. Explain the why in the body when it is not obvious.

## Pull requests

- Target `develop`. Fill in the PR template. Link the issue with `Closes #NN`.
- Every PR gets a self-review with at least one real review comment (a question, a defect found, or a justified approval note) before merging. Review comments are graded evidence.
- Merge with a merge commit (no squash) so branch history stays visible.
- CI must be green once Jenkins exists (Task 7 onwards).

## Issues and labels

- Labels: `task`, `bug`, `enabler`, `docs`, `P1-must`, `P2-should`, `P3-could`.
- Every work item in docs/TASKS.md gets one issue. The board lives in GitHub Projects (columns: Backlog, Ready, In Progress, In Review, Done).

## Releases

- Semantic versioning. `v0.1.0` is the MVP baseline (Task 6). Later tags come from the pipeline.
- Release flow: open a PR `develop` to `main`, merge, then tag `main`.

## Definition of Done (per work item)

- Behaviour matches the PRD and passes acceptance checks in docs/TASKS.md.
- Tests, lint and security lint pass.
- PR reviewed and merged into `develop`.
- Task document updated with evidence (screenshots or logs) the same day.
