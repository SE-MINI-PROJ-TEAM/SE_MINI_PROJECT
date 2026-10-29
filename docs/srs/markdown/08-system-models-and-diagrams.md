# System Models & Diagrams

## Architectural Model
The application follows a standard 3-tier architecture separating user interface presentation, server-side business logic, and database persistence.

![Three-Tier Architecture Model](images/three-tier-architecture.png){width=80%}

\clearpage

## Data Entity-Relationship Model
The entity-relationship model defines user accounts, course offerings, class schedules, roll-call attendance logs, and weighted rubric grades.

![Entity Relationship Diagram](images/er-attendance-grading.png){width=100%}

\clearpage

## Grade Lifecycle State Machine
Grades progress through a controlled state machine ensuring visibility restrictions and dispute tracking. A grade can be disputed at most once: after a dispute is resolved and the grade is re-published, it cannot return to `Under Review`.

![Grade Lifecycle State Machine](images/state-grade-lifecycle.png){width=100%}

## UML Use-Case Diagrams

### Academic Operations Use-Case Diagram
Covers primary operational interactions executed by Students and Faculty.

![Academic Operations Use Case Diagram](images/use-case-academic-operations.png){width=75%}

\clearpage

### System Administration Use-Case Diagram
Covers administrative provisioning, course setup, schedule creation, and grade publication.

![System Administration Use Case Diagram](images/use-case-admin-management.png){width=75%}
