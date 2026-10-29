# User Acceptance Test plan

## 1. Purpose
Confirm with the customer that the Student Record System delivers what the 15 user stories promise, in the environment they will actually use, before sign-off. UAT is the only level in the STP executed by the customer rather than the development team; everything else is automated (see `docs/qa/TEST-STRATEGY.md`).

## 2. Scope
* In scope: all 15 user stories (51 acceptance criteria in `qa/traceability/stories.md`), all three roles, the responsive layout and keyboard operation.
* Out of scope: infrastructure/hosting, e-mail delivery, SSO (see STP section 4), long-term availability (TC-OPS-01).

## 3. Participants
| Role | Person | Responsibility |
| --- | --- | --- |
| Customer / evaluator | Dr. Adithya Balasubramanyam | Executes or witnesses the script, decides acceptance |
| QA Lead | Vibha Vasisht | Prepares the environment, records results, triages defects |
| Test Engineer | Uttam B S | Assists the customer, runs the exploratory sessions |
| Developer | Tanmay T A | On call for defect fixes, never executes the script |

## 4. Entry criteria
* The `main` branch build is green in CI (all gates in `TEST-EXECUTION-REPORT.md` pass).
* Environment prepared with a freshly seeded database (`python manage.py seed --reset`), because seeded session times are relative to the moment of seeding.
* `docs/uat/UAT-SCRIPT.md` and a blank `UAT-RESULTS.md` are available; the acceptance matrix shows no uncovered criterion.

## 5. Execution
1. Walk through `UAT-SCRIPT.md` story by story using the listed accounts (about 60-90 minutes).
2. Record PASS / FAIL / BLOCKED for each criterion ID in `UAT-RESULTS.md`; add a comment for anything other than a clean PASS.
3. Raise a GitHub issue (label `uat`) for each FAIL and write its number in the sheet.
4. Run the five time-boxed exploratory charters listed in the results sheet (15 minutes each).
5. Developers fix, CI re-verifies, the QA Lead re-tests only the failed criteria and the neighbouring ones.

### Severity
| Level | Meaning | Effect on acceptance |
| --- | --- | --- |
| Critical | Security issue, data loss or corruption, blocks further testing | Reject until fixed |
| High | An acceptance criterion is not met | Reject until fixed |
| Medium | Works, but wrong or confusing | Accept with conditions if a fix is scheduled |
| Low | Cosmetic | May be accepted as is |

## 6. Exit criteria
* 100 % of criteria executed; 100 % PASS (or the remaining items explicitly accepted by the customer as conditions);
* no open Critical or High defects;
* the sign-off table in `UAT-RESULTS.md` is completed.

## 7. Evidence to attach to the final report
`UAT-RESULTS.md` (completed), the defect list, the sprint demo videos, and `TEST-EXECUTION-REPORT.md` from the build under test.

## 8. Further ideas to strengthen acceptance (optional)
* **Task-based usability observation:** ask a faculty member who has never seen the app to take attendance, and a student to find their GPA and dispute a grade, without help. Record time and hesitation; the targets are the SRS's "3 clicks" and "within 800 ms".
* **Persona walkthroughs:** each tester stays in one role (student, faculty, administrator) and tries to accomplish a real goal from login to outcome rather than checking screens in isolation.
* **Two-person concurrency session:** two testers edit the same attendance sheet or grade sheet at once to see how conflicts behave.
* **Accessibility spot check:** operate one workflow with the keyboard only and with a screen reader; automated scans cover only part of WCAG.
