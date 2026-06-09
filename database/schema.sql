-- MedQuery Database Schema DDL
-- Optimised for MySQL 8.0+

CREATE DATABASE IF NOT EXISTS medquery;
USE medquery;

-- 1. Table for structured drug interactions catalog
CREATE TABLE IF NOT EXISTS drug_interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drug_a VARCHAR(100) NOT NULL,
    drug_b VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL, -- 'Low', 'Moderate', 'High'
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Enforce lexicographical ordering at database level to prevent duplicate pair variations (e.g. A+B and B+A)
    CONSTRAINT chk_drug_name_order CHECK (drug_a < drug_b),
    
    -- Unique pair index for duplicate prevention
    UNIQUE KEY unique_drug_pair (drug_a, drug_b),
    
    -- Standard lookup indexes for performance
    INDEX idx_drug_a (drug_a),
    INDEX idx_drug_b (drug_b)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Table for tracking ingested medical reference documents
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(10) NOT NULL, -- 'pdf', 'txt', 'csv'
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Table for logged user queries and AI answers
CREATE TABLE IF NOT EXISTS queries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
