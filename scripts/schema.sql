CREATE DATABASE IF NOT EXISTS student_records;

USE student_records;

CREATE TABLE IF NOT EXISTS profiles (
    institutional_id VARCHAR(50) PRIMARY KEY,
    role VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL DEFAULT '',
    phone VARCHAR(20) NOT NULL DEFAULT '',
    emergency_contact VARCHAR(20) NOT NULL DEFAULT '',
    personal_email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NULL,
    is_temporary_password TINYINT(1) NOT NULL DEFAULT 1,
    is_active TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id VARCHAR(50) NOT NULL,
    target_user_id VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details VARCHAR(255) NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

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