# Introduction

## Purpose
This document provides a comprehensive Software Architecture and Design (SAD) specification for the Student Record System. It details the high-level system decomposition, architectural styles, constituent components, data persistence strategies, sequence models, API interfaces, security threat models (STRIDE), and error handling mechanisms.

## Scope
This specification covers the system's software architecture for:

* **Account Provisioning & Profile Services:** Administrative user provisioning and self-service profile management.
* **Course & Self-Enrollment Module:** Offering registration, capacity management, weighted rubric scheme normalization, and student self-enrollment (max 6 courses).
* **Schedule & Roll-Call Attendance:** Class schedule creation, digitized roll-call entry, hard 48-hour automated attendance freeze, and administrative override.
* **Weighted Rubric Grading Workflow:** Rubric-based evaluation, grade state transitions (`Draft` $\rightarrow$ `Submitted` $\rightarrow$ `Under Review` $\rightarrow$ `Published`), and regrade dispute workflows.
* **Analytics & Summary Reporting:** Student GPA calculation, class grade distributions, and institution-level summary metrics.

Out of scope: Mail automation/SMTP delivery services, hardware infrastructure and maintainance, and payment gateway infrastructure.

## Audience
This document is intended for software developers, system architects, QA engineers, security auditors, and course evaluators responsible for implementing, testing, and assessing the system.

## Definitions and Acronyms

| Term / Acronym | Definition |
| :--- | :--- |
| **ADR** | Architecture Decision Record |
| **API** | Application Programming Interface |
| **JWT** | JSON Web Token (HTTP-only bearer authorization) |
| **ORM** | Object-Relational Mapping |
| **RBAC** | Role-Based Access Control |
| **SAD** | Software Architecture and Design Specification |
| **SRS** | Software Requirements Specification |
| **STRIDE** | Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| **TLS** | Transport Layer Security (version 1.3) |
