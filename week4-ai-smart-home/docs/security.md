# Security Checklist

- Use TLS certificates rather than plaintext MQTT.
- Validate server certificates on ESP32 and Raspberry Pi clients.
- Use unique credentials per device.
- Restrict MQTT topics with ACLs.
- Keep `.env` and private keys out of Git.
- Require authentication for remote dashboard access.
- Encrypt sensitive stored data where appropriate.
- Avoid retaining raw audio or images unless explicitly required.
- Apply OS updates and firewall rules on the Raspberry Pi.
- Provide manual emergency/off controls for actuators.
