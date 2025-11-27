import sys
import os
import pytest
from unittest.mock import Mock

# Tilføj pc-side/src til Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pc-side', 'src')))
from database_handler import DatabaseHandler

# Fixture: DatabaseHandler med mock connection
@pytest.fixture
def db_handler():
    config = {
        "database": {
            "host": "localhost",
            "port": 3306,
            "user": "parking_user",
            "password": "parking_password123",
            "database": "parking_system"
        }
    }
    mock_conn = Mock()
    mock_conn.cursor.return_value = Mock()
    handler = DatabaseHandler(config)
    handler.connection = mock_conn
    return handler

def test_insert_license_plate(db_handler):
    db_handler.insert_license_plate("ABC123")
    db_handler.connection.cursor().execute.assert_called_with(
        "INSERT INTO license_plates (plate_number) VALUES (%s)", ("ABC123",)
    )
    db_handler.connection.commit.assert_called_once()
    db_handler.connection.cursor().close.assert_called_once()

def test_insert_parking_event(db_handler):
    db_handler.insert_parking_event("XYZ789", "entry")
    db_handler.connection.cursor().execute.assert_called_with(
        "INSERT INTO parking_events (plate_number, event_type) VALUES (%s, %s)",
        ("XYZ789", "entry")
    )
    db_handler.connection.commit.assert_called_once()
    db_handler.connection.cursor().close.assert_called_once()

def test_update_parking_spots(db_handler):
    db_handler.update_parking_spots(5)
    assert db_handler.connection.cursor().execute.call_count > 0
    db_handler.connection.commit.assert_called_once()
    db_handler.connection.cursor().close.assert_called_once()
