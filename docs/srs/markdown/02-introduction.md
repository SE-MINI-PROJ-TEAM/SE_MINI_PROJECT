# Introduction

## Purpose
This document specifies the Software Requirements Specification (SRS) for the Student Record System. It details the functional requirements, non-functional constraints, security objectives, and system models necessary for university-level deployment. This document serves as the primary technical reference for software developers, system evaluators, and academic instructors during project implementation and acceptance testing.

## Scope
The system provides digitized academic management capabilities covering administrative account provisioning, course section registration with weighted evaluation rubrics, student self-enrollment, digitized roll-call attendance marking with a strict 48-hour freeze constraint, and a multi-stage grade evaluation workflow (`Draft` $\rightarrow$ `Submitted` $\rightarrow$ `Under Review` $\rightarrow$ `Published`).

The scope explicitly excludes automated mail distribution (credentials are displayed on-screen during administrative account creation), physical hardware card integration, and external payment gateway processing.

## Audience
This document is targeted toward:

* **Software Engineering Faculty & Evaluators:** To review architecture compliance, constraint satisfaction, and acceptance criteria.
* **Development Team (3 Students):** To guide API schema design, backend logic, and frontend role-based workflows during 2 one-week Agile sprints.
* **System Administrators & Users:** To understand user role capabilities, system boundaries, and operational constraints.

## Definitions and Acronyms

| Term / Acronym | Definition |
| :--- | :--- |
| **API** | Application Programming Interface |
| **GPA** | Grade Point Average |
| **JWT** | JSON Web Token (used for secure session authorization) |
| **NFR** | Non-Functional Requirement |
| **ORM** | Object-Relational Mapping |
| **RBAC** | Role-Based Access Control |
| **RTM** | Requirements Traceability Matrix |
| **SMART** | Specific, Measurable, Achievable, Relevant, Time-bound criteria |
| **SRS** | Software Requirements Specification |
| **TLS** | Transport Layer Security (version 1.3) |
