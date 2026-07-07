-- Quiz Database Schema
-- Create database
CREATE DATABASE IF NOT EXISTS quiz_db;
USE quiz_db;

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lotname VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    quiz_status_tech VARCHAR(50) DEFAULT 'not_attempted',
    quiz_status_software VARCHAR(50) DEFAULT 'not_attempted'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quiz_type VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    option4 TEXT NOT NULL,
    answer TEXT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Quiz entries table (for entry codes)
CREATE TABLE IF NOT EXISTS quiz_entries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    entry_code VARCHAR(255) NOT NULL,
    quiz_type VARCHAR(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Results table
CREATE TABLE IF NOT EXISTS results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lotname VARCHAR(255) NOT NULL,
    score INT NOT NULL,
    duration INT NOT NULL,
    quiz_type VARCHAR(50) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Admins table
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin
INSERT IGNORE INTO admins (username, password) VALUES ('admin', '$2b$12$abcdefghijklmnopqrstuvwxyz');
