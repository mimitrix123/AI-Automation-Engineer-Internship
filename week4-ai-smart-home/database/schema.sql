CREATE TABLE IF NOT EXISTS telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    temperature REAL,
    motion INTEGER,
    light REAL,
    sound REAL,
    occupied INTEGER,
    occupancy_confidence REAL,
    energy_action TEXT
);

CREATE INDEX IF NOT EXISTS idx_telemetry_device_time
ON telemetry(device_id, recorded_at);
