
CREATE DATABASE IF NOT EXISTS student_records;

USE student_records;

CREATE TABLE IF NOT EXISTS profiles (
    institutional_id VARCHAR(50) PRIMARY KEY,
    role VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL DEFAULT '',
    phone VARCHAR(20) NOT NULL,
    emergency_contact VARCHAR(20) NOT NULL,
    personal_email VARCHAR(255) NOT NULL
);

INSERT INTO profiles (
    institutional_id,
    role,
    name,
    phone,
    emergency_contact,
    personal_email
)
VALUES (
    'STU001',
    'Student',
    'Demo Student',
    '9876543210',
    '9876501234',
    'student@example.com'
)
ON DUPLICATE KEY UPDATE
    institutional_id = institutional_id;


-- ---------------------------------------------------------------------------
-- US-06 / SYS-F-006: course sections and student self-enrollment.
-- Additive only: existing tables and rows are not touched.
-- Available seats are derived (capacity_limit - Active enrollments); there is
-- deliberately no "seats_left" column that could drift out of sync.
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS courses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(20) NOT NULL,
    title VARCHAR(150) NOT NULL,
    section_code VARCHAR(10) NOT NULL DEFAULT 'A',
    term VARCHAR(30) NOT NULL,
    capacity_limit INT NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'Open',
    CONSTRAINT uq_course_section_term UNIQUE (code, section_code, term),
    CONSTRAINT ck_courses_capacity CHECK (capacity_limit >= 0),
    CONSTRAINT ck_courses_status CHECK (status IN ('Open', 'Closed')),
    INDEX ix_courses_term (term)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS enrollments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id VARCHAR(50) NOT NULL,
    course_id INT NOT NULL,
    status VARCHAR(10) NOT NULL DEFAULT 'Active',
    enrolled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_enrollment_student_course UNIQUE (student_id, course_id),
    CONSTRAINT fk_enrollments_student
        FOREIGN KEY (student_id) REFERENCES profiles (institutional_id),
    CONSTRAINT fk_enrollments_course
        FOREIGN KEY (course_id) REFERENCES courses (id),
    INDEX ix_enrollments_course (course_id)
) ENGINE=InnoDB;
