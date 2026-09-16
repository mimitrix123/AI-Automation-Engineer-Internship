"""Minimal real-time dashboard API."""
from datetime import datetime, timezone
from fastapi import FastAPI

app = FastAPI(title="AI Smart Home Dashboard", version="1.0.0")

latest = {
    "temperature": None,
    "motion": False,
    "light": None,
    "sound": None,
    "occupied": None,
    "updated_at": None,
}

@app.get("/api/status")
def status():
    return latest

@app.post("/api/telemetry")
def telemetry(data: dict):
    latest.update(data)
    latest["updated_at"] = datetime.now(timezone.utc).isoformat()
    return {"ok": True, "status": latest}
