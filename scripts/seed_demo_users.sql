-- DEMO USER DATA ONLY - for local development and manual testing.
-- Safe to re-run: existing profile records are left unchanged.

USE student_records;

INSERT INTO profiles (
    institutional_id,
    role,
    name,
    phone,
    emergency_contact,
    personal_email,
    password_hash,
    is_temporary_password,
    is_active
)
VALUES
    -- Administrative Staff (2)
    ('ADM001', 'Admin',   'System Administrator', '9876500001', '9876500000', 'admin@university.edu', NULL, 0, 1),
    ('ADM002', 'Admin',   'Sarah Jenkins',        '9876500002', '9876500000', 's.jenkins@university.edu', NULL, 0, 1),

    -- Faculty Members (5)
    ('FAC001', 'Faculty', 'Dr. Alan Turing',      '9876510001', '9876510000', 'a.turing@university.edu', NULL, 0, 1),
    ('FAC002', 'Faculty', 'Dr. E.F. Codd',        '9876510002', '9876510000', 'e.codd@university.edu', NULL, 0, 1),
    ('FAC003', 'Faculty', 'Prof. Margaret Hamilton', '9876510003', '9876510000', 'm.hamilton@university.edu', NULL, 0, 1),
    ('FAC004', 'Faculty', 'Dr. Vint Cerf',        '9876510004', '9876510000', 'v.cerf@university.edu', NULL, 0, 1),
    ('FAC005', 'Faculty', 'Prof. Linus Torvalds', '9876510005', '9876510000', 'l.torvalds@university.edu', NULL, 0, 1),

    -- Student Body (13)
    ('STU001', 'Student', 'Demo Student',         '9876543210', '9876501234', 'student@example.com', NULL, 1, 1),
    ('STU002', 'Student', 'Alice Johnson',        '9876520002', '9876520000', 'alice.j@student.edu', NULL, 0, 1),
    ('STU003', 'Student', 'Bob Smith',            '9876520003', '9876520000', 'bob.s@student.edu', NULL, 0, 1),
    ('STU004', 'Student', 'Charlie Brown',        '9876520004', '9876520000', 'charlie.b@student.edu', NULL, 0, 1),
    ('STU005', 'Student', 'Diana Prince',         '9876520005', '9876520000', 'diana.p@student.edu', NULL, 0, 1),
    ('STU006', 'Student', 'Ethan Hunt',           '9876520006', '9876520000', 'ethan.h@student.edu', NULL, 0, 1),
    ('STU007', 'Student', 'Fiona Gallagher',      '9876520007', '9876520000', 'fiona.g@student.edu', NULL, 0, 1),
    ('STU008', 'Student', 'George Clark',         '9876520008', '9876520000', 'george.c@student.edu', NULL, 0, 1),
    ('STU009', 'Student', 'Hannah Abbott',        '9876520009', '9876520000', 'hannah.a@student.edu', NULL, 0, 1),
    ('STU010', 'Student', 'Ian Malcolm',          '9876520010', '9876520000', 'ian.m@student.edu', NULL, 0, 1),
    ('STU011', 'Student', 'Julia Roberts',        '9876520011', '9876520000', 'julia.r@student.edu', NULL, 0, 1),
    ('STU012', 'Student', 'Kevin Bacon',          '9876520012', '9876520000', 'kevin.b@student.edu', NULL, 0, 1),
    ('STU013', 'Student', 'Laura Croft',          '9876520013', '9876520000', 'laura.c@student.edu', NULL, 0, 1)
ON DUPLICATE KEY UPDATE institutional_id = institutional_id;