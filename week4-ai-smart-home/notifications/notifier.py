"""Generic notification webhook adapter."""
import os
import requests


def send_notification(title: str, message: str, snapshot_url: str | None = None) -> bool:
    url = os.getenv("NOTIFICATION_WEBHOOK_URL")
    if not url:
        return False
    payload = {"title": title, "message": message, "snapshot_url": snapshot_url}
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return True
