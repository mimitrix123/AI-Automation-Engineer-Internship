# System Architecture

## Edge layer
ESP32 nodes sample temperature, motion, light, and sound. A Raspberry Pi acts as the local gateway and can continue core automation when the internet is unavailable.

## Messaging
Telemetry uses MQTT topics under `home/<device>/telemetry`. Production deployments should use MQTT over TLS with per-device credentials and least-privilege topic ACLs.

## AI layer
The occupancy model consumes engineered environmental features and returns an occupancy class with confidence. The energy optimizer converts occupancy and comfort context into suggested device actions. Hard safety limits and manual overrides remain authoritative.

## Application layer
FastAPI exposes current state and control APIs. A browser dashboard consumes these APIs and can be extended with WebSockets for push updates.

## Notifications
Automation events are sent through a webhook adapter. A production implementation can connect that adapter to a mobile push provider without storing provider secrets in source control.

## Data flow
`Sensors → MQTT/TLS → Raspberry Pi → database + AI inference → automation → dashboard/voice/notifications`
