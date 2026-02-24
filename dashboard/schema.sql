-- ═══════════════════════════════════════════════════════════
--  Campus Asset Tracker – Database Setup
--  Run this in phpMyAdmin or MySQL CLI on your XAMPP install
-- ═══════════════════════════════════════════════════════════

-- Create (or select) the shared database
CREATE DATABASE IF NOT EXISTS campus_asset_tracker
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE campus_asset_tracker;

-- ── Users table (PHP team manages auth) ─────────────────────
CREATE TABLE IF NOT EXISTS users (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    email        VARCHAR(255) NOT NULL UNIQUE,
    password     VARCHAR(255) NOT NULL,          -- bcrypt hash
    full_name    VARCHAR(255) NOT NULL,
    role         ENUM('admin','staff','student') NOT NULL DEFAULT 'student',
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ── Shared session table: PHP writes, Python reads ──────────
--    This is the auth bridge between PHP (login) and Python (dashboard)
CREATE TABLE IF NOT EXISTS php_sessions (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    token        VARCHAR(255) NOT NULL UNIQUE,   -- random_bytes(32) hex in PHP
    user_id      INT NOT NULL,
    user_email   VARCHAR(255),
    user_name    VARCHAR(255),
    role         VARCHAR(50) DEFAULT 'admin',
    expires_at   DATETIME NOT NULL,              -- e.g. NOW() + INTERVAL 8 HOUR
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Auto-clean expired sessions (optional, run as scheduled event)
-- CREATE EVENT IF NOT EXISTS clean_expired_sessions
--   ON SCHEDULE EVERY 1 HOUR
--   DO DELETE FROM php_sessions WHERE expires_at < NOW();

-- ── Assets table (placeholder – expand as needed) ───────────
CREATE TABLE IF NOT EXISTS assets (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    asset_id      VARCHAR(20)  NOT NULL UNIQUE,  -- e.g. A001
    name          VARCHAR(255) NOT NULL,
    category      VARCHAR(100),
    serial_number VARCHAR(100) UNIQUE,
    status        ENUM('Available','In Use','Under Maintenance','Retired')
                  NOT NULL DEFAULT 'Available',
    location      VARCHAR(255),
    assigned_to   VARCHAR(255),                  -- or FK to users later
    notes         TEXT,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Sample data (matches Python placeholder data)
INSERT IGNORE INTO assets (asset_id, name, category, serial_number, status, location, assigned_to) VALUES
  ('A001','Dell Latitude 5520 Laptop',    'IT Equipment',    'DL5520-2024-001',  'Available',        'IT Lab – Building A, Room 201',         NULL),
  ('A002','HP ProDesk 600 Desktop',       'IT Equipment',    'HP600-2023-045',   'In Use',           'Computer Lab – Building B, Room 105',   'Dr. Sarah Johnson'),
  ('A003','Epson PowerLite Projector',    'AV Equipment',    'EP-PL-2022-012',   'Available',        'Media Room – Building C',               NULL),
  ('A004','iPad Pro 12.9" (6th Gen)',     'IT Equipment',    'IPAD-2024-008',    'In Use',           'Library – Main Floor',                  'Marcus Lee'),
  ('A005','Logitech Conference Camera',   'AV Equipment',    'LGT-CAM-2023-003', 'Under Maintenance','Conference Room 2A',                    NULL),
  ('A006','Canon EOS R50 Camera',         'Media Equipment', 'CNON-R50-2024-002','Available',        'Media Checkout – Building D',           NULL);
