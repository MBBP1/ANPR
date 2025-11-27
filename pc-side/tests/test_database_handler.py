import sys
import os
import pytest
from unittest.mock import Mock

# Tilføj src til Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from database_handler import DatabaseHandler

# Fixture til config
@pytest.fixture
def db_config():
    return {
        "database": {
            "host": "localhost",
            "port": 3306,
            "user": "parking_user",
            "password": "parking_password123",
            "database": "parking_system"
        }
    }

# Fixture til DatabaseHandler med mock connection
@pytest.fixture
def db_handler(db_config):
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor

    handler = DatabaseHandler(db_config)  # <--- pass config
    handler.connection = mock_conn
    return handler

def test_insert_license_plate(db_handler):
    plate = "ABC123"
    db_handler.insert_license_plate(plate)

    cursor = db_handler.connection.cursor()
    cursor.execute.assert_called_with(
        "INSERT INTO license_plates (plate_number) VALUES (%s)", (plate,)
    )
    db_handler.connection.commit.assert_called_once()
    cursor.close.assert_called_once()

def test_insert_parking_event(db_handler):
    plate = "XYZ789"
    event_type = "entry"
    db_handler.insert_parking_event(plate, event_type)

    cursor = db_handler.connection.cursor()
    cursor.execute.assert_called_with(
        "INSERT INTO parking_events (plate_number, event_type) VALUES (%s, %s)",
        (plate, event_type)
    )
    db_handler.connection.commit.assert_called_once()
    cursor.close.assert_called_once()

def test_update_parking_spots(db_handler):
    available_spots = 5
    db_handler.update_parking_spots(available_spots)

    cursor = db_handler.connection.cursor()
    assert cursor.execute.call_count > 0
    db_handler.connection.commit.assert_called_once()
    cursor.close.assert_called_once()
