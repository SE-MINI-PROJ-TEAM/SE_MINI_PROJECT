# 1. Introduction

## Purpose
This document defines the Software Test Plan (STP) for the Student Record System v1.0. It outlines test objectives, scope, strategy, target resources, execution schedule, and responsibilities required to verify system quality and functional compliance prior to production release.

## Scope
Testing covers core software modules of the Student Record System:

* **Account Provisioning & Profile Services:** Administrative user provisioning, temporary credential display, mandatory password reset, and contact info self-service updates.
* **Course Setup, Self-Enrollment & Schedules:** Course registration, section capacity limits, rubric scheme weight auto-normalization, student self-enrollment (capped at 6 active courses), and class schedule publishing.
* **Digitized Attendance Marking:** Instructor binary roll-call entry, aggregate percentage tracking, 48-hour automated attendance edit freeze, and administrative overrides.
* **Weighted Rubric Grading Workflow:** Rubric score evaluation, grade state transitions (`Draft` $\rightarrow$ `Submitted` $\rightarrow$ `Under Review` $\rightarrow$ `Published`), and regrade dispute workflows.
* **Analytics & Summary Reporting:** Consolidated student GPA calculation, class grade distributions, and executive administrative metrics export.
* **System Non-Functional & Security Attributes:** API latency ($95\% < 800\text{ ms}$), 200 concurrent transactions, 99.0% operational availability, TLS 1.3 transit encryption, bcrypt password hashing, 48-hour JWT expiration, and RBAC endpoint middleware.

Hardware maintenance and third-party email/SMTP delivery infrastructure are excluded.

## References

* **SRS:** Software Requirements Specification for Student Record System v1.0.
* **SAD:** Software Architecture and Design Specification for Student Record System v1.0.
* **IEEE Std 829-2008:** IEEE Standard for Software and System Test Documentation.
* **OWASP Top 10:** Web Application Security Verification Standard.

## Definitions

* **API:** Application Programming Interface.
* **GPA:** Grade Point Average.
* **JWT:** JSON Web Token (HTTP-only bearer session authorization).
* **RBAC:** Role-Based Access Control.
* **RTM:** Requirements Traceability Matrix.
* **SRS:** Software Requirements Specification.
* **STP:** Software Test Plan.
