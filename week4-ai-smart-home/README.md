# 🏆 Major Project — Week 4: AI-Powered Smart Home

A complete IoT + AI smart-home reference implementation using ESP32/Raspberry Pi sensor nodes, MQTT messaging, AI-based occupancy prediction, energy optimization, real-time monitoring, voice-control integration, mobile notifications, and encrypted communication.

## Architecture

```text
ESP32 Sensor Nodes
 ├─ Temperature
 ├─ PIR Motion
 ├─ LDR Light
 └─ Sound Sensor
        │ MQTT over TLS
        ▼
Raspberry Pi Edge Gateway
 ├─ MQTT Broker
 ├─ Sensor ingestion
 ├─ Occupancy model
 ├─ Energy optimizer
 └─ Automation rules
        │ REST/WebSocket/MQTT
        ▼
Real-Time Dashboard ─── Voice Control
        │
        └── Mobile Notifications

Data → SQLite/TimescaleDB → analytics/history
```

## Features

- 🌡️ Temperature monitoring
- 🚶 Motion/occupancy sensing
- 💡 Ambient-light monitoring
- 🔊 Sound-level monitoring
- 🧠 Tiny/edge ML occupancy prediction
- ⚡ AI-assisted energy optimization
- 📊 Real-time web dashboard
- 🎙️ Voice-control API integration
- 📱 Mobile alert/notification hooks
- 🔐 MQTT TLS, authentication, and secret management
- 📝 Event and telemetry logging
- 🐳 Docker-ready services
- 🧪 Automated tests
- 🚀 Raspberry Pi deployment and systemd guidance

## Project Layout

```text
week4-ai-smart-home/
├── README.md
├── requirements.txt
├── .env.example
├── config/config.example.yaml
├── edge/
│   ├── gateway.py
│   ├── mqtt_client.py
│   ├── sensors.py
│   ├── automation.py
│   └── security.py
├── ml/
│   ├── train_occupancy.py
│   ├── occupancy_predictor.py
│   └── energy_optimizer.py
├── dashboard/
│   ├── app.py
│   └── templates/index.html
├── esp32/
│   └── smart_home_sensor.ino
├── database/
│   └── schema.sql
├── notifications/
│   └── notifier.py
├── voice/
│   └── controller.py
├── tests/
├── deployment/
│   ├── docker-compose.yml
│   └── smart-home.service
└── docs/
    ├── architecture.md
    ├── hardware.md
    ├── security.md
    ├── deployment.md
    └── ai-model.md
```

## AI Workflow

1. Collect timestamped temperature, motion, light, sound, and device-state telemetry.
2. Engineer rolling-window features such as motion counts, light averages, temperature deltas, and time-of-day.
3. Train an occupancy classifier/regressor offline.
4. Export a lightweight model for edge inference where practical.
5. Combine model predictions with explicit safety and user-defined automation rules.
6. Optimize HVAC/lighting/device schedules against comfort and energy constraints.

> AI recommendations should not override physical safety controls. Manual controls remain available.

## Security

- Never commit credentials, private certificates, phone numbers, or personal sensor data.
- Use environment variables for secrets.
- Use MQTT over TLS in deployment.
- Authenticate clients and restrict topic permissions.
- Keep the dashboard behind authentication on non-local networks.
- Rotate certificates and credentials periodically.

## Quick Start

```bash
cd week4-ai-smart-home
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python dashboard/app.py
```

For Raspberry Pi deployment, see `docs/deployment.md`.

## Hardware

Suggested hardware: Raspberry Pi 4/5 as gateway, ESP32 development boards, DHT22/BME280 temperature sensor, PIR motion sensor, LDR/photoresistor module, analog sound sensor, relay modules for low-voltage demonstration loads, and an optional OLED display.

## Responsible AI / Privacy

Occupancy inference is based on environmental telemetry rather than storing identity information. Keep raw sensor data only as long as needed, document retention, and obtain appropriate consent for monitoring shared spaces.

## License

MIT
