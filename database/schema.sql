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

-- 2. Table for tracking medical documents uploads & vector ingestion states
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    filepath VARCHAR(512) NOT NULL,
    file_size INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Table for logged user queries, chat histories, citations, and interaction warning tags
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
