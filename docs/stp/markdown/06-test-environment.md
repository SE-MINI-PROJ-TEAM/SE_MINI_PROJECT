# 6. Test Environment

## Hardware

* **Application & DB Server:** Docker Compose stack (MySQL 8, the Flask API on gunicorn, and the nginx web tier) running on developer laptops with Docker Desktop and on GitHub-hosted Linux runners in CI.
* **Client Devices:** Workstations and mobile screens (viewport widths 375px to 1920px).

## Software

* **Application Stack:** Python 3.12 (Flask, SQLAlchemy) served by gunicorn, React frontend served by nginx, MySQL 8.
* **OS Environment:** Linux containers (`python:3.12-slim` for the API, `nginx:1.27-alpine` for the web tier, `mysql:8.0` for the database); Ubuntu on the CI runners.

## Tools

* **Unit & Integration Testing:** PyTest against a real MySQL 8 database (backend) and Vitest (frontend logic).
* **API Testing:** Newman CLI test collection runner.
* **Performance Testing:** Apache k6 load testing framework.
* **Security Scanning:** OWASP ZAP vulnerability scanner (API scan, API baseline and UI baseline), Bandit (static analysis of the Python source), pip-audit and npm audit (known-vulnerable dependencies).
* **UI & E2E Testing:** Playwright automation framework, with axe-core for WCAG 2.1 A/AA accessibility checks.
* **Automation:** every tool runs in Docker through the `qa.sh` stages, and GitHub Actions runs them on every pull request and on every push to `main`.

## Test Data

* Synthetic database seed containing 500 student accounts, 50 faculty accounts, 10 admin accounts, 50 course offerings, and 1,000 scheduled session records. The database is re-seeded before each black-box stage, so every stage starts from identical data.
