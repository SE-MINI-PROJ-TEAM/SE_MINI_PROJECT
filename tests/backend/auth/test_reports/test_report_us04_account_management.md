# Software Test Case Specification
## Admin Account Status & Role Metadata Management

**Test Module:** SYS-F-004  
**Test Case ID:** TC-ACC-04  
**Test Suite:** TS-AUTH  
**Test Framework:** Python `unittest`  
**Test Environment:** Python 3.12, Flask, Flask-SQLAlchemy, In-Memory SQLite  

### 1. Test Cases

| Test Case ID | Test Objective | Test Input / Procedure | Expected Result | Actual Result |
|---|---|---|---|---|
| TC-ACC-04.1 | Verify user search and listing functionality | Send GET request to `/api/admin/users?search=STU301` | HTTP 200 returned matching filtered user record | Pass |
| TC-ACC-04.2 | Verify deactivating account revokes JWT sessions & writes audit log | Send PUT request to `/api/admin/users/STU301/status` with `isActive = false` | HTTP 200 returned with `isActive = false` and audit log entry created | Pass |
| TC-ACC-04.3 | Verify toggling user status back to active | Send PUT request with `isActive = true` for an inactive profile | HTTP 200 returned with `isActive = true` | Pass |
| TC-ACC-04.4 | Verify role claim metadata update | Send PUT request with `role = "Admin"` | HTTP 200 returned with updated role metadata | Pass |
| TC-ACC-04.5 | Verify 404 rejection on unknown user ID | Send PUT request targeting non-existent institutional ID | HTTP 404 Not Found returned | Pass |

### 2. Test Execution Summary

- **Total test cases:** 5
- **Passed:** 5
- **Failed:** 0
- **Execution status:** Successful

### 3. Requirements Traceability

- **SRS ID:** SYS-F-004 (Admin account metadata/status update)[cite: 3, 5]
- **RTM Status:** Fully verified against isolated SQLite test context[cite: 3, 5].