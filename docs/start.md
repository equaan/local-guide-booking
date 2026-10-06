How to Run the App
Based on the AGENTS.md documentation, here are the commands to run the app:
1. Set up the environment
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env    # Windows: copy .env.example .env
2. Apply migrations
flask --app wsgi db upgrade
3. Seed the database (creates 2 guides, 2 travelers, ~6 slots)
python scripts/seed.py
4. Run the app
flask --app wsgi run --debug
The app will start at http://localhost:5000 (default port).
5. Run tests
pytest                                    # unit + integration (e2e excluded by default)
pytest --cov=app --cov-report=term-missing
ruff check . && ruff format --check .
bandit -r app -q
6. Selenium E2E tests (Task 9 only)
pytest -m e2e                        # needs a running app and Chrome
7. Visual review (B-08)
python scripts/screenshot_review.py    # needs a running app and Playwright
Navigation Quick Start:
1. Register as a traveler or guide via /register
2. Login via /login
3. Browse slots at /slots - filter by city/date
4. Request a booking on a slot detail page
5. Guide confirms/cancels bookings via /guide/slots/<id>/deactivate or the booking detail page
6. View your bookings at /bookings
Default Credits (from seed):
- Guides: 2 guides registered with city "Mumbai"
- Travelers: 2 travelers registered
- Slots: ~6 future slots available for booking
The app follows the DevSecOps CI/CD pipeline pattern (Jenkins, SonarQube, Trivy, Selenium, Docker Hub, ArgoCD, Kubernetes, Prometheus/Grafana) as described in the project overview.