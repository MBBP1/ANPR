import sys
import os
import time
import pytest
from unittest.mock import patch, Mock
import ssl

# Sørg for at src mappen kan findes af Python
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pc-side', 'src')))

from mqtt_publisher import MQTTPublisher

# Fixture: opsætning af en dummy MQTT konfiguration
# Denne bruges af flere tests, så vi slipper for at skrive den flere gange
@pytest.fixture
def mqtt_config():
    return {
        "mqtt": {
            "client_id": "test_client",
            "broker": "localhost",
            "port": 8883,  # TLS port
            "topics": {"available_spots": "parking/available_spots"},
            "tls": {
                "ca_cert": "tests/fake_ca.crt",
                "client_cert": "tests/fake_client.crt",
                "client_key": "tests/fake_client.key"
            }
        }
    }

# Test at TLS bliver opsat korrekt
def test_mqtt_tls_configuration(mqtt_config):
    """Tester at TLS opsætning i MQTTPublisher sker korrekt."""
    # Patch mqtt.Client så vi ikke forbinder til en rigtig broker
    with patch("mqtt_publisher.mqtt.Client") as MockClient:
        mock_client = MockClient.return_value

        # Patch os.path.exists så certifikater "findes" uden rigtige filer
        with patch("os.path.exists", return_value=True):
            publisher = MQTTPublisher(mqtt_config)

            # Tjek at tls_set blev kaldt med rigtige certifikater og TLS version
            mock_client.tls_set.assert_called_once_with(
                ca_certs="tests/fake_ca.crt",
                certfile="tests/fake_client.crt",
                keyfile="tests/fake_client.key",
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLSv1_2
            )

            # Tjek at hostname-verifikation slås fra
            mock_client.tls_insecure_set.assert_called_once_with(True)

            # Tjek at connect blev kaldt til broker med TLS port
            mock_client.connect.assert_called_once_with("localhost", 8883)

            # Tjek at MQTT loop starter
            mock_client.loop_start.assert_called_once()

# Test TLS opsætning når der ikke bruges client cert/key
def test_mqtt_tls_without_certs(mqtt_config):
    """Tester TLS opsætning uden client certifikat og key."""
    mqtt_config["mqtt"]["tls"]["client_cert"] = None
    mqtt_config["mqtt"]["tls"]["client_key"] = None

    with patch("mqtt_publisher.mqtt.Client") as MockClient:
        mock_client = MockClient.return_value
        publisher = MQTTPublisher(mqtt_config)

        # Tjek at tls_set stadig kaldes korrekt med kun CA cert
        mock_client.tls_set.assert_called_once_with(
            ca_certs="tests/fake_ca.crt",
            certfile=None,
            keyfile=None,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2
        )

        # Hostname-verifikation skal stadig slås fra
        mock_client.tls_insecure_set.assert_called_once_with(True)

# Test at flere publish events bliver sendt korrekt
def test_multiple_publish_events(mqtt_config):
    """Tester at flere publiceringer kaldes korrekt."""
    with patch("mqtt_publisher.mqtt.Client") as MockClient:
        mock_client = MockClient.return_value
        publisher = MQTTPublisher(mqtt_config)

        # Publicer tre gange med forskellige værdier
        for spots in [10, 20, 30]:
            publisher.publish_available_spots(spots)

        # Tjek at publish blev kaldt tre gange
        assert mock_client.publish.call_count == 3

        # MQTT loop skal kun startes én gang
        mock_client.loop_start.assert_called_once()

# Test publish med simulated delay
def test_publish_with_delay(mqtt_config):
    """Tester at publish med delay stadig kaldes korrekt."""
    with patch("mqtt_publisher.mqtt.Client") as MockClient:
        mock_client = MockClient.return_value

        # Simuler langsom publish, som tager 0.05 sekunder
        def slow_publish(topic, payload):
            time.sleep(0.05)
            return Mock(rc=0)

        mock_client.publish.side_effect = slow_publish

        publisher = MQTTPublisher(mqtt_config)
        publisher.publish_available_spots(15)

        # Tjek at publish blev kaldt mindst én gang
        assert mock_client.publish.called
