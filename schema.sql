CREATE DATABASE IF NOT EXISTS hospital_analytics
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hospital_analytics;

CREATE TABLE IF NOT EXISTS patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    age_band ENUM('0-17','18-29','30-44','45-59','60+') NOT NULL,
    gender_optional ENUM('Female','Male','Other','Prefer not to say') NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS departments (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS visits (
    visit_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    department_id INT NOT NULL,
    visit_date DATE NOT NULL,
    visit_type ENUM('Routine','Follow-up','Emergency','Other') NOT NULL DEFAULT 'Routine',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_visits_patient FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id) ON DELETE RESTRICT,
    CONSTRAINT fk_visits_department FOREIGN KEY (department_id)
        REFERENCES departments(department_id) ON DELETE RESTRICT,
    INDEX idx_visit_date (visit_date),
    INDEX idx_department_date (department_id, visit_date)
);

INSERT IGNORE INTO departments (department_name) VALUES
('Cardiology'), ('General Medicine'), ('Orthopedics'), ('Pediatrics'),
('Dermatology'), ('ENT'), ('Ophthalmology'), ('Neurology');

-- Synthetic demo data only. These records do not represent real people.
INSERT INTO patients (age_band, gender_optional) VALUES
('18-29','Female'), ('30-44','Male'), ('45-59','Female'), ('60+','Male'),
('0-17','Prefer not to say'), ('30-44','Female'), ('18-29','Male'),
('60+','Female'), ('45-59','Other'), ('0-17','Male'),
('18-29','Female'), ('30-44','Male'), ('45-59','Female'), ('60+','Male'),
('18-29','Other'), ('30-44','Female'), ('0-17','Female'), ('45-59','Male'),
('60+','Prefer not to say'), ('30-44','Other');

-- Seed visit dates relative to the current date, spanning recent months.
INSERT INTO visits (patient_id, department_id, visit_date, visit_type)
SELECT p.patient_id, d.department_id,
       DATE_SUB(CURDATE(), INTERVAL seq.day_offset DAY),
       CASE WHEN seq.day_offset % 5 = 0 THEN 'Follow-up'
            WHEN seq.day_offset % 11 = 0 THEN 'Emergency'
            ELSE 'Routine' END
FROM (
    SELECT 1 AS day_offset UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL
    SELECT 4 UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL
    SELECT 8 UNION ALL SELECT 9 UNION ALL SELECT 10 UNION ALL SELECT 11 UNION ALL
    SELECT 12 UNION ALL SELECT 13 UNION ALL SELECT 14 UNION ALL SELECT 15 UNION ALL
    SELECT 16 UNION ALL SELECT 17 UNION ALL SELECT 18 UNION ALL SELECT 19 UNION ALL
    SELECT 20 UNION ALL SELECT 21 UNION ALL SELECT 22 UNION ALL SELECT 23 UNION ALL
    SELECT 24 UNION ALL SELECT 25 UNION ALL SELECT 26 UNION ALL SELECT 27 UNION ALL
    SELECT 28 UNION ALL SELECT 29 UNION ALL SELECT 30 UNION ALL SELECT 35 UNION ALL
    SELECT 40 UNION ALL SELECT 45 UNION ALL SELECT 50 UNION ALL SELECT 60 UNION ALL
    SELECT 70 UNION ALL SELECT 80 UNION ALL SELECT 90 UNION ALL SELECT 100 UNION ALL
    SELECT 110 UNION ALL SELECT 120 UNION ALL SELECT 130 UNION ALL SELECT 140 UNION ALL
    SELECT 150 UNION ALL SELECT 160 UNION ALL SELECT 170 UNION ALL SELECT 180
) AS seq
JOIN patients p ON p.patient_id = 1 + MOD(seq.day_offset, 20)
JOIN departments d ON d.department_id = 1 + MOD(seq.day_offset, 8);
