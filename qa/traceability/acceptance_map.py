"""Which automated checks prove each acceptance criterion in qa/traceability/stories.md.

The list for a story is ordered exactly like the checkboxes under "### Acceptance Criteria" in qa/traceability/stories.md.
`qa/traceability/acceptance.py` verifies that (a) every criterion has at least one reference and (b) every reference
still exists, so the matrix cannot silently rot when tests are renamed or criteria change.

Reference constructors:  py(file, test)  nm(folder)  e2e(file, title)  vt(file)  k6(scenario)  zap()
"""


def py(path, name):
    return ("py", f"backend/tests/{path}", name)


def nm(folder):
    return ("newman", folder, "")


def e2e(file, title):
    return ("e2e", f"qa/e2e/tests/{file}", title)


def vt(path):
    return ("vitest", f"frontend/src/{path}", "")


def k6(scenario):
    return ("k6", scenario, "")


def zap():
    return ("zap", "OWASP ZAP API scan", "")


UP = "user_provisioning/test_user_provisioning.py"
PW = "password_reset/test_password_reset.py"
PR = "profile/test_profile.py"
AM = "account_management/test_account_management.py"
CS = "course_setup/test_course_setup.py"
CE = "course_enrollment/test_course_enrollment.py"
SC = "schedule/test_schedule.py"
AT = "attendance_marking/test_attendance_marking.py"
AO = "attendance_override/test_attendance_override.py"
AD = "attendance_dashboard/test_attendance_dashboard.py"
GE = "grade_entry/test_grade_entry.py"
GP = "grade_publication/test_grade_publication.py"
RD = "regrade_disputes/test_regrade_disputes.py"
AN = "analytics/test_analytics.py"
MT = "admin_metrics/test_admin_metrics.py"
SE = "admin_metrics/test_security.py"
PF = "admin_metrics/test_performance.py"
WF = "04-end-to-end-workflows.spec.js"
UX = "02-usability.spec.js"

ACCEPTANCE = {
    "US-01": [
        [e2e(WF, "admin provisions a user"), py(UP, "test_admin_creates_user_and_sees_temporary_password")],
        [py(UP, "test_admin_creates_user_and_sees_temporary_password"), nm("02 Admin provisioning")],
        [py(UP, "test_admin_creates_user_and_sees_temporary_password")],
        [py(UP, "test_duplicate_institutional_id_returns_409"), py(UP, "test_duplicate_email_returns_409"), nm("02 Admin provisioning")],
    ],
    "US-02": [
        [py(PW, "test_temp_password_user_is_gated_until_reset"), nm("03 Forced password reset"), e2e(WF, "admin provisions a user")],
        [py(PW, "test_weak_passwords_are_rejected_with_reasons"), py(PW, "test_complexity_rules"), vt("features/password_reset/passwordPolicy.test.js")],
        [py(PW, "test_stored_password_is_bcrypt_with_work_factor_12")],
        [py(PW, "test_successful_reset_clears_flag_and_unblocks"), e2e(WF, "admin provisions a user")],
    ],
    "US-03": [
        [py(PR, "test_profile_shows_contact_info_and_institutional_id")],
        [py(PR, "test_update_persists_and_is_returned"), nm("04 Profile")],
        [py(PR, "test_invalid_formats_rejected"), vt("features/profile/validation.test.js")],
        [py(PR, "test_admin_managed_fields_cannot_be_modified"), nm("04 Profile")],
    ],
    "US-04": [
        [py(AM, "test_search_filters_by_name_role_and_status"), e2e(WF, "deactivating a user")],
        [py(AM, "test_deactivation_revokes_active_session_immediately_and_is_audited"), nm("12 Deactivation"), e2e(WF, "deactivating a user")],
        [py(AM, "test_deactivation_revokes_active_session_immediately_and_is_audited"), py(AM, "test_audit_log_listing_and_immutability")],
    ],
    "US-05": [
        [py(CS, "test_create_course_normalizes_rubric_on_save"), py(CS, "test_edit_capacity_but_not_below_enrolled"), nm("05 Course setup")],
        [py(CS, "test_create_course_normalizes_rubric_on_save")],
        [py(CS, "test_weights_always_sum_to_exactly_100"), py(CS, "test_random_weight_sets_sum_to_100"), vt("features/course_setup/normalize.test.js"), nm("05 Course setup")],
    ],
    "US-06": [
        [py(CE, "test_catalog_shows_open_sections_with_real_time_capacity"), nm("06 Enrollment")],
        [py(CE, "test_enrollment_decrements_available_seats_immediately"), e2e(WF, "admin provisions a user")],
        [py(CE, "test_seventh_course_is_blocked_with_an_error"), nm("06 Enrollment"), e2e(WF, "the 6-course cap")],
        [py(CE, "test_enrollment_decrements_available_seats_immediately"), py(CE, "test_concurrent_enrollments_never_exceed_capacity")],
    ],
    "US-07": [
        [py(SC, "test_admin_schedules_session_and_it_populates_student_and_faculty_calendars"), nm("05 Course setup")],
        [py(SC, "test_admin_schedules_session_and_it_populates_student_and_faculty_calendars"), e2e(UX, "student pages fit the screen")],
        [py(SC, "test_faculty_sees_roster_only_for_assigned_sections"), py(SE, "test_faculty_cannot_read_another_faculty_roster_or_grades"), nm("07 Roster isolation")],
    ],
    "US-08": [
        [py(AT, "test_roster_lists_enrolled_students_with_current_marks")],
        [py(AT, "test_save_persists_records_and_confirms"), e2e(UX, "roll-call is completed within 3 clicks")],
        [py(AT, "test_save_persists_records_and_confirms"), nm("07 Roster isolation"), e2e(UX, "roll-call is completed within 3 clicks")],
        [py(AT, "test_edits_after_48_hours_are_rejected_by_the_backend"), py(AT, "test_freeze_boundary_is_exactly_48_hours_after_start"), nm("07 Roster isolation")],
    ],
    "US-09": [
        [py(AO, "test_admin_overrides_frozen_record_and_audit_entry_is_created"), nm("08 Admin override")],
        [py(AO, "test_justification_is_mandatory"), nm("08 Admin override")],
        [py(AO, "test_admin_overrides_frozen_record_and_audit_entry_is_created"), py(AM, "test_audit_log_listing_and_immutability"), nm("08 Admin override")],
    ],
    "US-10": [
        [py(AD, "test_percentage_per_course_with_totals"), nm("09 Student attendance view")],
        [py(AD, "test_course_view_breaks_down_sessions"), nm("09 Student attendance view")],
        [py(AD, "test_alert_flag_only_below_75_percent"), py(AD, "test_exactly_75_percent_is_not_flagged"), nm("09 Student attendance view")],
    ],
    "US-11": [
        [py(GE, "test_grid_renders_rubric_components_for_each_enrolled_student"), e2e(WF, "grade lifecycle")],
        [py(GE, "test_partial_scores_save_as_draft"), nm("10 Grade lifecycle")],
        [py(GE, "test_students_cannot_view_marks_while_draft"), nm("10 Grade lifecycle"), e2e(WF, "grade lifecycle")],
    ],
    "US-12": [
        [py(GP, "test_submit_calculates_weighted_total_and_moves_to_submitted"), py(GP, "test_weighted_total_applies_normalized_weights"), nm("10 Grade lifecycle")],
        [py(GP, "test_admin_publishes_and_students_see_grades_immediately"), nm("10 Grade lifecycle"), e2e(WF, "grade lifecycle")],
        [py(GP, "test_admin_publishes_and_students_see_grades_immediately"), e2e(WF, "grade lifecycle")],
    ],
    "US-13": [
        [py(RD, "test_student_view_tells_the_ui_whether_a_regrade_is_still_available"), e2e(WF, "grade lifecycle")],
        [py(RD, "test_explanation_is_required"), e2e(WF, "grade lifecycle")],
        [py(RD, "test_filing_moves_published_grade_to_under_review"), nm("10 Grade lifecycle")],
        [py(RD, "test_faculty_sees_notification_count_reevaluates_and_republishes"), nm("10 Grade lifecycle"), e2e(WF, "grade lifecycle")],
    ],
    "US-14": [
        [py(AN, "test_student_gpa_uses_published_grades_only"), py(AN, "test_gpa_is_credit_weighted"), nm("11 Analytics"), e2e(UX, "the GPA is visible")],
        [py(AN, "test_faculty_distribution_buckets_mean_median"), nm("11 Analytics")],
        [py(AN, "test_student_dashboard_query_is_fast"), k6("sessions"), nm("11 Analytics")],
    ],
    "US-15": [
        [py(MT, "test_csv_export_contains_attendance_and_grade_metrics"), nm("11 Analytics")],
        [py(SE, "test_plain_http_redirects_to_https_with_hsts"), py(SE, "test_session_cookie_is_http_only_with_48h_lifetime"),
         py(SE, "test_sql_injection_payloads_are_inert"), nm("14 Injection"), zap()],
        [py(PF, "test_200_simultaneous_attendance_and_grade_submissions_without_deadlock"), k6("burst")],
    ],
}
