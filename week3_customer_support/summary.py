"""Send a daily support activity summary from Google Sheets."""
from __future__ import annotations

import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing environment variable: {name}")
    return value


def main() -> None:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(env("GOOGLE_SERVICE_ACCOUNT_FILE"), scope)
    rows = gspread.authorize(creds).open(env("GOOGLE_SHEET_NAME")).sheet1.get_all_records()
    cutoff = datetime.now(timezone.utc) - timedelta(days=1)
    recent = []
    for row in rows:
        try:
            timestamp = datetime.fromisoformat(str(row.get("timestamp", "")).replace("Z", "+00:00"))
            if timestamp >= cutoff:
                recent.append(row)
        except ValueError:
            continue
    escalations = sum(str(r.get("escalated", "")).lower() == "yes" for r in recent)
    body = (f"Daily Customer Support Summary\n\nConversations: {len(recent)}\n"
            f"Escalations: {escalations}\n\nGenerated: {datetime.now(timezone.utc).isoformat()}")
    msg = MIMEText(body, "plain")
    msg["Subject"] = "Daily Customer Support Summary"
    msg["From"] = env("EMAIL_FROM")
    msg["To"] = env("SUMMARY_EMAIL")
    with smtplib.SMTP(env("SMTP_HOST"), int(env("SMTP_PORT")), timeout=30) as server:
        server.starttls()
        server.login(env("SMTP_USERNAME"), env("SMTP_PASSWORD"))
        server.sendmail(env("EMAIL_FROM"), [env("SUMMARY_EMAIL")], msg.as_string())
    print(body)


if __name__ == "__main__":
    main()
