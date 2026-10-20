
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
