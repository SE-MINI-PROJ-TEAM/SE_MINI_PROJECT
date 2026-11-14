# Revision History {-}

| Version | Date | Author | Change Summary | Approval |
| :--- | :--- | :--- | :--- | :--- |
| **0.1** | 13-09-2026 | Tanmay T A | Initial SRS draft containing legacy extended requirements, initial analysis models, and appendices A–D. | Draft |
| **0.2** | 27-09-2026 | Uttam B S | Restructured SRS to align with standard SE template; removed out-of-scope appendices, streamlined NFR targets, eliminated complex OTP/geolocation constraints, and introduced the 48-hour attendance freeze rule. | Reviewed |
| **0.3** | 06-10-2026 | Vibha Vasisht | Refined functional requirements: introduced student self-enrollment (max 6 courses), administrative user provisioning, restricted administrative editing of personal contact data, and defined the 4-stage grade lifecycle (`Draft` $\rightarrow$ `Submitted` $\rightarrow$ `Under Review` $\rightarrow$ `Published`). | Reviewed |
| **1.0** | 09-10-2026 | Tanmay T A | Finalized requirement specifications (20 FRs, 5 NFRs, 2 PRJ-SO, 5 PRJ-SR), added dynamic rubric weight auto-normalization, and structured split UML Use-Case models for Academic Operations and System Administration. | Reviewed |
| **1.1** | 28-10-2026 | Tanmay T A | Updated the grade challenge lifecycle: a grade can be disputed only once and a re-published grade is final (`Under Review` can be entered from `Published` only for a grade that has never been disputed). Revised `SYS-F-016`, `SYS-F-017`, the grade lifecycle state diagram and its description. Requirements traceability statuses updated to Verified (`SYS-NF-003` Waived). | Approved |

# Approvals {-}

| Role | Name | Signature / Email | Date |
| :--- | :--- | :--- | :--- |
| Course Instructor | Dr. Adithya Balasubramanyam | adithyab@pes.edu | 28-10-2026 |
