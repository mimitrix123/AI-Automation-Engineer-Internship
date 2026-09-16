# Deployment Guide

## Local

1. Create a virtual environment and install `requirements.txt`.
2. Copy `.env.example` to `.env` and configure MQTT/TLS values.
3. Start the API with `uvicorn dashboard.app:app --host 0.0.0.0 --port 8000`.
4. Send telemetry to `POST /api/telemetry` and read the latest state from `GET /api/status`.

## Docker

From `week4-ai-smart-home/` run:

```bash
docker compose -f deployment/docker-compose.yml up --build -d
```

Before production, provide a real Mosquitto configuration and TLS certificates, add dashboard authentication, persistent database storage, health checks, and secrets through a secret manager.

## Raspberry Pi

Run the gateway as a system service, keep the MQTT broker bound to the local network, enable the firewall, and provision unique device credentials. Keep local automation available when the internet is unavailable.
