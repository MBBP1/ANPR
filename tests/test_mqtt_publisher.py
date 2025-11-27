import sys
import os
import pytest
from unittest.mock import Mock
import json
from datetime import datetime

# Tilføj pc-side/src til Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pc-side', 'src')))
from mqtt_publisher import MQTTPublisher

@pytest.fixture
def mqtt_config():
    return {
        "mqtt": {
            "broker": "localhost",
            "port": 1883,
            "client_id": "pc_camera",
            "topics": {
                "available_spots": "parking/available_spots"
            }
        }
    }

@pytest.fixture
def mock_mqtt_client(monkeypatch):
    mock_client = Mock()
    monkeypatch.setattr("mqtt_publisher.mqtt.Client", lambda client_id: mock_client)
    return mock_client

def test_connect(mqtt_config, mock_mqtt_client):
    publisher = MQTTPublisher(mqtt_config)
    mock_mqtt_client.connect.assert_called_with(
        mqtt_config['mqtt']['broker'],
        mqtt_config['mqtt']['port']
    )
    mock_mqtt_client.loop_start.assert_called_once()

def test_publish_available_spots(mqtt_config, mock_mqtt_client):
    publisher = MQTTPublisher(mqtt_config)
    publisher.publish_available_spots(42)
    topic = mqtt_config['mqtt']['topics']['available_spots']
    args, kwargs = mock_mqtt_client.publish.call_args
    published_topic, payload = args
    assert published_topic == topic
    message = json.loads(payload)
    assert message['available_spots'] == 42
    assert message['total_spots'] == 200
    assert 'timestamp' in message

def test_parking_event(mqtt_config, mock_mqtt_client):
    publisher = MQTTPublisher(mqtt_config)
    publisher.parking_event("ABC123", "entry")
    args, kwargs = mock_mqtt_client.publish.call_args
    published_topic, payload = args
    assert published_topic == "parking/events"
    message = json.loads(payload)
    assert message['plate_number'] == "ABC123"
    assert message['event_type'] == "entry"
    assert 'timestamp' in message
