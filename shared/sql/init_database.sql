CREATE DATABASE IF NOT EXISTS parking_system;
USE parking_system;

CREATE TABLE IF NOT EXISTS license_plates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_number VARCHAR(20) NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    camera_id VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS parking_events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    plate_number VARCHAR(20),
    event_type ENUM('entry', 'exit'),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parking_spots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    spot_number INT NOT NULL,
    is_occupied BOOLEAN DEFAULT FALSE,
    plate_number VARCHAR(20),
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);