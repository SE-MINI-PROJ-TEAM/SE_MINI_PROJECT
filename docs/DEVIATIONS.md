# Deviations from the Initial SRS, SAD and STP

This document records the deviation between the initially submitted SRS, SAD and Test Plan and the system as delivered.
The SRS, SAD and STP in this repository have already been updated to match it.

| # | Area | Initial documents | Delivered system | Affected requirements |
| --- | --- | --- | --- | --- |
| 1 | Regrade dispute lifecycle | A grade could be disputed repeatedly: `Published` → `Under Review` → `Published` → `Under Review` … | A grade can be disputed **only once**. After the dispute is resolved and the grade is re-published, it is final. | `SYS-F-016`, `SYS-F-017` (US-13) |

## 1. Regrade dispute lifecycle: one dispute per grade

### What the initial documents said
The grade state machine allowed `Published → Under Review` whenever a student requested a review, and
`Under Review → Published` when faculty or an administrator resolved it. Nothing limited how many times a student could
repeat the cycle on the same grade.

### What was delivered
```
Draft → Submitted → Published → Under Review → Published (final)
                       │                           │
                       └── only if never disputed ─┘   a re-published grade cannot return to Under Review
```

* A student may file a regrade request for a `Published` grade **once**. The request needs a written explanation.
* When faculty or an administrator resolves it, the revised marks are published again and that grade is **final**.
* A further request for the same grade is rejected (`409 ALREADY_DISPUTED`). The student's dashboard no longer offers the
  Dispute button for it and shows a "Regrade used" badge instead.
* The rule is enforced in the service layer and by a unique constraint on `grade_disputes.enrollment_id`, so it also holds
  when two requests arrive at the same moment.

### Why
Without a limit, a published grade could be reopened indefinitely. That makes a published grade provisional, and each
repeat request adds to faculty workload. One regrade gives the student a fair challenge while keeping published results
final. The change was decided while smoke-testing the finished application.

### What did not change
* The four acceptance criteria of US-13 are the same (dispute button, mandatory justification, `Under Review`, faculty
  re-evaluation and re-publication).
* The `Draft → Submitted → Published` part of the lifecycle and all other user stories are unaffected.

### Where it is reflected
| Artifact | Update |
| --- | --- |
| SRS | `SYS-F-016` / `SYS-F-017` reworded; grade lifecycle state diagram and its description updated |
| SAD | Grade lifecycle sequence diagram and the design text updated |
| STP | Features to be tested and the traceability table (`SYS-F-016`, `TC-GRD-04`, `TC-GRD-05`) updated |
| Tests | `backend/tests/regrade_disputes` covers the once-only rule; the UAT (US-13.4) and the E2E suite check the "Regrade used" state |
| Code | `backend/app/features/regrade_disputes`, `backend/app/models/grade.py`, `frontend/src/features/regrade_disputes` |
