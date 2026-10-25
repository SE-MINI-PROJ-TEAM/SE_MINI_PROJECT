-- DEMO DATA ONLY - for local development and manual acceptance testing.
-- Do not run against a production database. Real sections are created by
-- Administrators under SYS-F-005 (not implemented yet).
-- Safe to re-run: existing sections are left unchanged.

USE student_records;

INSERT INTO courses (code, title, section_code, term, capacity_limit, status)
VALUES
    ('CS101', 'Introduction to Programming', 'A', '2026-ODD', 30, 'Open'),
    ('CS102', 'Data Structures',             'A', '2026-ODD', 30, 'Open'),
    ('CS201', 'Database Systems',            'A', '2026-ODD', 25, 'Open'),
    ('CS202', 'Operating Systems',           'A', '2026-ODD', 25, 'Open'),
    ('MA101', 'Linear Algebra',              'A', '2026-ODD', 40, 'Open'),
    ('MA102', 'Discrete Mathematics',        'A', '2026-ODD', 40, 'Open'),
    ('PH101', 'Engineering Physics',         'A', '2026-ODD', 35, 'Open'),
    ('EN101', 'Technical Writing',           'A', '2026-ODD', 1,  'Open'),
    ('CS301', 'Machine Learning',            'A', '2026-ODD', 20, 'Closed')
ON DUPLICATE KEY UPDATE code = code;
