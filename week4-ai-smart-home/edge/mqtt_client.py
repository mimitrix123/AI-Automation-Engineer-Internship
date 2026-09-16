"""Secure MQTT telemetry client for the smart-home edge gateway."""
import os
import ssl
import json
import paho.mqtt.client as mqtt


def build_client() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="smart-home-gateway")
    client.username_pw_set(os.environ["MQTT_USERNAME"], os.environ["MQTT_PASSWORD"])
    client.tls_set(
        ca_certs=os.environ["MQTT_CA_CERT"],
        certfile=os.environ.get("MQTT_CLIENT_CERT"),
        keyfile=os.environ.get("MQTT_CLIENT_KEY"),
        tls_version=ssl.PROTOCOL_TLS_CLIENT,
    )
    client.tls_insecure_set(False)
    return client


def publish_telemetry(client: mqtt.Client, device_id: str, payload: dict) -> None:
    topic = f"home/{device_id}/telemetry"
    client.publish(topic, json.dumps(payload), qos=1)
