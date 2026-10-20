# Software Test Case Specification
## Student Record System: Profile Contact Editing

**Test Module:** SYS-F-003  
**Test Framework:** Python `unittest`  
**Test Environment:** Python 3.12, Flask, Flask-SQLAlchemy, SQLite test database

### 1. Test Cases

| Test Case ID | Test Objective | Test Input / Procedure | Expected Result | Actual Result |
|---|---|---|---|---|
| TC-PROF-001 | Verify valid phone number acceptance | Enter `9876543210` and `+91 9876543210` | Both phone numbers are accepted | Pass |
| TC-PROF-002 | Verify invalid phone number rejection | Enter `abc123` and `123` | Both phone numbers are rejected | Pass |
| TC-PROF-003 | Verify valid email acceptance | Enter `student@example.com` | Email address is accepted | Pass |
| TC-PROF-004 | Verify invalid email rejection | Enter `invalid-email` and `student@` | Both email addresses are rejected | Pass |
| TC-PROF-005 | Verify profile retrieval | Send GET request to `/api/profile/STU001` | HTTP 200 returned with the correct institutional ID | Pass |
| TC-PROF-006 | Verify contact detail update | Send PUT request with valid phone, emergency contact, and personal email | HTTP 200 returned and updated profile details are provided | Pass |
| TC-PROF-007 | Verify invalid phone rejection during update | Send PUT request with phone `not-a-phone` | HTTP 400 returned and update is rejected | Pass |
| TC-PROF-008 | Verify role modification restriction | Send PUT request with `{"role":"Admin"}` | HTTP 400 returned; role cannot be modified through this endpoint | Pass |
| TC-PROF-009 | Verify nonexistent profile handling | Send GET request to `/api/profile/UNKNOWN` | HTTP 404 returned | Pass |

### 2. Test Execution Summary

- **Total test cases:** 9
- **Passed:** 9
- **Failed:** 0
- **Execution status:** Successful

### 3. Test Limitations

The tests use a temporary SQLite database and do not verify the live MySQL connection. Authentication, authorization based on the logged-in user, and integration with the institutional identity system are not covered by these tests.

### 4. Conclusion

All nine automated test cases passed in the test environment. The results verify basic profile retrieval, contact detail validation, profile updates, and rejection of attempts to modify the role through the tested API endpoint. Further integration and security testing is required before production deployment.