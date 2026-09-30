# Task 1: Problem Definition and Scope

Student: Mohammad Equaan Kacchi | Roll No: 67 | ID: 23102A0073 | BE-VII Division A

Project: Local Guide Booking System, DevSecOps CI/CD on Kubernetes

Date completed: TODO(student): fill in after the validation work in section 4.5 is finished. Draft v0.1 prepared 28-09-2026.

## 1. Objective

Original task text from the course sheet:

> Problem Definition and Scope: Study the real-time need for the Local Guide Booking System. Identify target users, existing pain points, stakeholders, constraints and measurable success criteria. Freeze a small 15-Task MVP scope.
>
> Deliverable: Problem statement, stakeholder list, objectives, constraints and approved MVP scope.

## 2. Changes from the original spec

| Original | What I did instead | Why |
|-----------|-----------|-----------|
| Study the need, identify users and pain points | Same. Pain points are written as hypotheses and checked through short interviews and a scan of existing platforms (section 4.5) | A need statement without evidence is only an opinion |
| Freeze a small MVP scope | Same. The scope is frozen in section 4.10 with a change-control rule | Keeps the 15-task workload realistic |
| (not in the sheet) | Success criteria include pipeline metrics (lead time, vulnerabilities, rollback time) as well as product metrics | The delivery pipeline is the main subject of this project (Deviations Register, D3, D6, D7) |

## 3. Tools and versions

| Tool | Version | Purpose |
|---|---|---|
| Markdown in a Git repository | not applicable | Documents kept next to the code with history |
| Pandoc | 3.x | Converts Markdown to the Word report |
| Microsoft Word | current | Review copy and PDF export for submission |
| GitHub | not applicable | Hosts the repository, issues and project board |

## 4. Implementation steps

### 4.1 Approach

1. Wrote the problem in one paragraph and split the pain points into testable hypotheses (H1 to H6).
2. Defined the users and stakeholders.
3. Planned the validation: five short interviews and a scan of three existing platforms (section 4.5). The results table must be filled in with real answers.
4. Set objectives, constraints and measurable success criteria.
5. Cut the scope to what six required functions and a full delivery pipeline can support in about three weeks, and froze it.

### 4.2 Problem statement

Independent local guides usually take bookings through informal channels such as phone calls, chat messages and social media messages. Travelers who want a guide for a few hours must ask about availability one guide at a time, wait for replies, and have no reliable way to see whether a request was accepted or cancelled. Guides can lose track of who asked for which time and can accept overlapping requests.

The Local Guide Booking System (LGBS) gives a guide one place to publish availability slots and gives a traveler one place to see open slots, request a booking and track its status until it is confirmed or cancelled.

Scope of the academic project: a small web application, deliberately limited, delivered through a full DevSecOps pipeline that builds, tests, scans, packages, deploys and monitors it. The pipeline is the main learning and assessment subject.

Note: the statements above are working assumptions until section 4.5 is completed with real findings.

### 4.3 Target users (working personas)

These personas are assumptions used to design the MVP. They are replaced or confirmed by the interview results.

| Persona | Goal | Frustration to remove |
|---|---|---|
| Traveler (for example a student or tourist planning a day in a new city) | Find an available local guide for a specific time and know quickly whether the request is accepted | Asking many guides one by one; unclear status |
| Local guide (independent, part-time or full-time) | Publish when they are free and control which requests they accept | Missed messages; overlapping or forgotten commitments; no single schedule view |

### 4.4 Pain points (hypotheses to validate)

| ID | Hypothesis | Affects | Validation status |
|---|---|---|---|
| H1 | Travelers cannot see a guide's real availability without messaging them | Traveler | TODO(student) |
| H2 | Travelers do not get a clear, quick confirmation or cancellation status | Traveler | TODO(student) |
| H3 | Guides receive requests across several apps and lose track of them | Guide | TODO(student) |
| H4 | Guides risk double-booking the same time | Guide | TODO(student) |
| H5 | Cancelling or changing a booking is done informally and creates confusion | Both | TODO(student) |
| H6 | Neither side has a history of what happened to a booking | Both | TODO(student) |

### 4.5 Need validation (what I actually did)

Method (about two hours in total):

- Five short interviews (about ten minutes each): two people who have hired a local guide or tour guide, two people who arranged local transport or tours over chat messages, and one person who works as a guide or in local tourism if reachable. Record the date and the person's role only. Do not record names or contact details.
- Scan of three existing booking or experience platforms of my choice, noting how each shows availability, booking status and cancellation.

Interview questions:

1. Describe the last time you booked or offered a local guide. How did it start and how did it end?
2. How did you find out whether the guide was free at the time you wanted?
3. How long did it take to get a clear yes or no? What happened while you waited?
4. Has a booking ever been cancelled, changed or double-booked? What happened?
5. What single thing would have made that experience easier?

Interview results:

| # | Date | Interviewee role | Key answer | Hypotheses supported (H1 to H6) |
|---|---|---|---|---|
| 1 | TODO(student) | TODO(student) | TODO(student) | TODO(student) |
| 2 | TODO(student) | TODO(student) | TODO(student) | TODO(student) |
| 3 | TODO(student) | TODO(student) | TODO(student) | TODO(student) |
| 4 | TODO(student) | TODO(student) | TODO(student) | TODO(student) |
| 5 | TODO(student) | TODO(student) | TODO(student) | TODO(student) |

Platform scan:

| Platform | How availability is shown | How status is shown | Cancellation | Gap LGBS can address |
|---|---|---|---|---|
| TODO(student) | TODO(student) | TODO(student) | TODO(student) | TODO(student) |
| TODO(student) | TODO(student) | TODO(student) | TODO(student) | TODO(student) |
| TODO(student) | TODO(student) | TODO(student) | TODO(student) | TODO(student) |

Summary of what the evidence says (write three to five sentences, and change the problem statement if the evidence disagrees with it): TODO(student).

### 4.6 Stakeholder list

| Stakeholder | Interest | Influence | How engaged |
|---|---|---|---|
| Traveler (primary user) | Fast, clear booking and status | Medium | Interviews; acceptance journeys J1 to J5 |
| Local guide (primary user) | Control of schedule; no double booking | Medium | Interviews; acceptance journeys J2, J4 |
| Course faculty (evaluator) | Complete, correct, well-documented 15 tasks | High | Task list approval; scope approval; viva |
| Student developer (owner) | Finish on time; learn and be able to explain everything | High | Owns all decisions and evidence |
| Portfolio reviewers and future employers | Evidence of real DevOps practice | Low | Public GitHub repositories and report |
| Platform operator (role played by the student in Tasks 13 to 15) | Reliable deployment, rollback and monitoring | Medium | Runbook and dashboards |

### 4.7 Objectives

Product objectives
- O1 Deliver a working MVP with the six required functions: user registration, availability (slot) view, booking request, confirmation, cancellation and status tracking.
- O2 Guarantee that one slot can never have two confirmed bookings.

Delivery (DevOps) objectives
- O3 Every merge to the development branch is built, tested, scanned and packaged automatically.
- O4 Deployment to Kubernetes happens through Git (GitOps) and can be rolled back by reverting a commit.
- O5 The system exposes health checks and metrics that are visible on a dashboard.
- O6 The whole environment can be rebuilt from code and automation.

Learning and portfolio objectives
- O7 Gain practical experience in Kubernetes, ArgoCD, SonarQube, Trivy, Prometheus, Grafana and Selenium Grid.
- O8 Produce a portfolio-ready repository and report that I can explain in a viva or interview.

### 4.8 Constraints

| Type | Constraint | Consequence |
|---|---|---|
| Cost | Zero budget; only free tools and free tiers | Everything runs locally first; cloud only if a legitimate free option exists (Deviations Register D9) |
| Hardware | One student laptop of the 16 GB RAM class | Run one tool group at a time; single-node cluster; SonarQube and Selenium Grid started only when needed |
| Time | About three weeks in total | Small MVP; documentation written on the day each task is finished |
| Team | One student, assisted by AI tools | Every AI-assisted step is logged and reviewed (docs/AI-USAGE-LOG.md) |
| Skills | Kubernetes at minikube level; other tools new | Learning spikes are planned inside the sprints (Task 2) |
| Academic | Must keep the 15 tasks, document each, submit one PDF | Task list, Deviations Register and one report per task |
| Data | No real payments and no real personal data | Demo data only; passwords hashed; no card or ID collection |

### 4.9 Measurable success criteria

Targets are set now and will be revised once real measurements exist (after Task 10).

| ID | Metric | Target | How it is measured | When checked |
|---|---|---|---|---|
| SC1 | Acceptance journeys J1 to J5 pass | 5 of 5 | Selenium suite in Jenkins | Tasks 9, 10 |
| SC2 | Double-booking incidents | 0 | Database constraint test plus negative test | Task 6 |
| SC3 | Automated test coverage of application code | at least 80 percent | pytest-cov report and SonarQube | Tasks 6, 10 |
| SC4 | SonarQube quality gate | Passed | Sonar dashboard | Task 10 |
| SC5 | High or critical vulnerabilities in the final image | 0 | Trivy report | Tasks 11, 12 |
| SC6 | Commit-to-running-deployment lead time | 20 minutes or less | Jenkins build time plus ArgoCD sync time | Task 15 |
| SC7 | Rollback to the previous stable release | 5 minutes or less | Timed Git revert and ArgoCD sync | Task 14 |
| SC8 | Second Ansible run reports no changes (idempotency) | 0 changed tasks | Ansible play recap | Task 14 |
| SC9 | Page response time (95th percentile) | under 500 ms | Prometheus histogram on a dashboard | Task 15 |
| SC10 | Every one of the 15 tasks has a report with real evidence | 15 of 15 | Deliverables checklists | Task 15 |

### 4.10 MVP scope (frozen)

Must have
- Register and log in as traveler or guide.
- Guide creates and deactivates availability slots; travelers browse slots (filter by city and date).
- Traveler requests a booking; guide confirms; traveler or guide cancels.
- Booking status tracking with a timeline of every change.
- Health, readiness and metrics endpoints; seed script for demo data.

Should have
- JSON endpoint listing slots.
- Gauge metric of bookings by status.

Out of scope (will not be built in this project)
- Payments, reviews and ratings, chat, email or SMS notifications, maps, guide identity verification, admin panel, password reset, social login, multiple languages, timezone handling, image uploads, recurring slots.

Scope freeze rule: after approval the scope changes only through a written change request that states the reason and the effect on the sprint plan. The full requirement set is in docs/PRD.md (version 1.0).

Top risks

| Risk | Impact | Mitigation |
|---|---|---|
| Too many new tools in three weeks | Half-finished pipeline | Cut order: Selenium Grid, then Grafana dashboards; never drop Kubernetes or ArgoCD |
| 16 GB RAM is not enough for every tool at once | Slow or crashing environment | Cap WSL memory; start heavy tools only when needed; single-node cluster |
| No free cloud option | Tasks 13 and 14 lose the remote-node story | Contingency D9: local VM or WSL2 as the target node, documented |
| AI-generated work I cannot explain | Weak viva | Coach prompts for Tasks 7 to 15; AI usage log; break-it-on-purpose exercises |
| Documentation left to the end | Vague report | Write each task report the day the task is done |

### 4.11 Approval record

| Item | Approved by | Date | Evidence |
|---|---|---|---|
| Problem statement, objectives and frozen MVP scope | TODO(student): ma'am | TODO(student) | TODO(student): screenshot in docs/evidence/task-01/ |

## 5. Evidence

- Screenshot or notes of the interviews (roles and dates only): TODO(student), docs/evidence/task-01/interviews.png
- Screenshot of the platform scan notes: TODO(student), docs/evidence/task-01/platform-scan.png
- Link to docs/PRD.md at the commit that froze the scope: TODO(student)
- Approval screenshot: TODO(student), docs/evidence/task-01/approval.png

## 6. Problems faced and how I fixed them

| Problem | Root cause | Fix |
|---|---|---|
| TODO(student) | TODO(student) | TODO(student) |

## 7. Deliverables checklist

- [x] Problem statement (section 4.2)
- [x] Stakeholder list (section 4.6)
- [x] Objectives (section 4.7)
- [x] Constraints (section 4.8)
- [ ] Approved MVP scope (section 4.10 is frozen; approval record in 4.11 still to be filled)
- [ ] Need validation evidence (section 4.5 still to be filled)

## 8. Learnings and improvements

- What I learned: TODO(student)
- What I would do differently: TODO(student)
