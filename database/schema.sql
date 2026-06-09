-- MedQuery Database Schema Blueprint
-- Raw MySQL definitions to replicate standard DB models

CREATE DATABASE IF NOT EXISTS medquery_db;
USE medquery_db;

-- 1. Table for tracking medical documents uploads & vector ingestion states
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(512) NOT NULL,
    file_size INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Table for logged user queries, chat histories, citations, and interaction warning tags
CREATE TABLE IF NOT EXISTS queries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(100),
    user_query TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    citations TEXT, -- JSON array of source documents or paragraphs
    has_interaction_warnings BOOLEAN DEFAULT FALSE,
    severity_level VARCHAR(50) DEFAULT 'none', -- 'none', 'minor', 'moderate', 'major'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Table for structured drug interaction catalogues
CREATE TABLE IF NOT EXISTS drug_interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    drug_a VARCHAR(100) NOT NULL,
    drug_b VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL, -- 'minor', 'moderate', 'major'
    mechanism TEXT,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_drug_pair (drug_a, drug_b)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
