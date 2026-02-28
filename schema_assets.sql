-- File: cat/sql/schema_assets.sql
-- Minimal schema for Farah's "Asset Creation" page.
-- Run in phpMyAdmin against a database named `cat`.

CREATE TABLE IF NOT EXISTS categories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS locations (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(150) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS assets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  asset_tag VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(150) NOT NULL,
  serial_number VARCHAR(150) NULL,
  category_id INT NOT NULL,
  location_id INT NOT NULL,
  status ENUM('AVAILABLE','IN_USE','MAINTENANCE','RETIRED') NOT NULL DEFAULT 'AVAILABLE',
  notes TEXT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (category_id) REFERENCES categories(id),
  FOREIGN KEY (location_id) REFERENCES locations(id)
);

INSERT IGNORE INTO categories (name) VALUES ('IT Equipment'), ('AV Equipment'), ('Lab Equipment');
INSERT IGNORE INTO locations (name) VALUES ('IT Lab - Building A Room 201'), ('Library Front Desk'), ('Engineering Storage');
