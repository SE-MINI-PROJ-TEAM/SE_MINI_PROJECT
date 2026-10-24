# Software Test Case Specification
## Administrative User Provisioning & Credentials

**Test Module:** SYS-F-001  
**Test Case ID:** TC-ACC-01  
**Test Suite:** TS-AUTH  
**Test Framework:** Python `unittest`  
**Test Environment:** Python 3.12, Flask, Flask-SQLAlchemy, SQLite test database  

### 1. Test Cases

| Test Case ID | Test Objective | Test Input / Procedure | Expected Result | Actual Result |
|---|---|---|---|---|
| TC-ACC-01.1 | Verify valid user account provisioning | Send POST request to `/api/admin/users` with unique ID, email, name, and role | HTTP 201 Created returned with secure `temporaryPassword` and `isTemporaryPassword = true` | Pass |
| TC-ACC-01.2 | Verify duplicate institutional ID conflict | Send POST request with an existing `institutionalId` | HTTP 409 Conflict returned with explicit ID collision error | Pass |
| TC-ACC-01.3 | Verify duplicate email conflict | Send POST request with an existing `personalEmail` | HTTP 409 Conflict returned with explicit email collision error | Pass |
| TC-ACC-01.4 | Verify incomplete payload rejection | Send POST request missing required `role` or `personalEmail` fields | HTTP 400 Bad Request returned | Pass |
| TC-ACC-01.5 | Verify invalid role claim rejection | Send POST request with role outside `['Student', 'Faculty', 'Admin']` | HTTP 400 Bad Request returned | Pass |

### 2. Test Execution Summary

- **Total test cases:** 5
- **Passed:** 5
- **Failed:** 0
- **Execution status:** Successful

### 3. Requirements Traceability

- **SRS ID:** SYS-F-001 (Account provisioning & credential display)
- **RTM Status:** Verified against SQLite isolated context.