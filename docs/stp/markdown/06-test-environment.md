# 6. Test Environment

## Hardware

* **Application & DB Server:** Linux cloud instance / Docker container environment (4 vCPU, 8GB RAM).
* **Client Devices:** Workstations and mobile screens (viewport widths 375px to 1920px).

## Software

* **Application Stack:** Python application runtime, MySQL relational database.
* **OS Environment:** Ubuntu Server 24.04 LTS.

## Tools

* **Unit & Integration Testing:** PyTest.
* **API Testing:** Newman CLI test collection runner.
* **Performance Testing:** Apache k6 load testing framework.
* **Security Scanning:** OWASP ZAP vulnerability scanner.
* **UI & E2E Testing:** Playwright automation framework.

## Test Data

* Synthetic database seed containing 500 student accounts, 50 faculty accounts, 10 admin accounts, 50 course offerings, and 1,000 scheduled session records.
