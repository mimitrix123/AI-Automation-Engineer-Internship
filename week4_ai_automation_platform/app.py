import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler

from automation import BusinessAssistant

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "assistant.db"))
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Business Automation Platform", version="1.0.0")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            metadata TEXT
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            received_at TEXT NOT NULL,
            sender TEXT,
            subject TEXT,
            body TEXT,
            action_item TEXT,
            draft_response TEXT,
            status TEXT NOT NULL DEFAULT 'new'
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            owner TEXT,
            due_date TEXT,
            status TEXT NOT NULL DEFAULT 'open'
        )""")
        db.commit()


@contextmanager
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def log_event(event_type: str, status: str, message: str, metadata: Optional[dict] = None) -> None:
    with db_conn() as db:
        db.execute(
            "INSERT INTO logs(created_at,event_type,status,message,metadata) VALUES(?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), event_type, status, message, json.dumps(metadata or {})),
        )


assistant = BusinessAssistant(log_event=log_event)
scheduler = BackgroundScheduler(timezone="UTC")


def scheduled_email_monitor() -> None:
    try:
        assistant.process_inbox()
    except Exception as exc:
        logger.exception("Email monitor failed")
        log_event("email_monitor", "error", str(exc))


def scheduled_weekly_report() -> None:
    try:
        assistant.generate_weekly_report()
    except Exception as exc:
        logger.exception("Weekly report failed")
        log_event("weekly_report", "error", str(exc))


@app.on_event("startup")
def startup() -> None:
    init_db()
    scheduler.add_job(scheduled_email_monitor, "interval", minutes=int(os.getenv("EMAIL_POLL_MINUTES", "10")), id="email_monitor", replace_existing=True)
    scheduler.add_job(scheduled_weekly_report, "cron", day_of_week="mon", hour=int(os.getenv("REPORT_HOUR_UTC", "3")), minute=0, id="weekly_report", replace_existing=True)
    scheduler.start()
    log_event("platform", "started", "AI automation platform started")


@app.on_event("shutdown")
def shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    with db_conn() as db:
        logs = db.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 30").fetchall()
        emails = db.execute("SELECT * FROM emails ORDER BY id DESC LIMIT 10").fetchall()
        tasks = db.execute("SELECT * FROM tasks ORDER BY id DESC LIMIT 10").fetchall()
        stats = {
            "logs": db.execute("SELECT COUNT(*) FROM logs").fetchone()[0],
            "emails": db.execute("SELECT COUNT(*) FROM emails").fetchone()[0],
            "tasks": db.execute("SELECT COUNT(*) FROM tasks WHERE status='open'").fetchone()[0],
            "errors": db.execute("SELECT COUNT(*) FROM logs WHERE status='error'").fetchone()[0],
        }
    return templates.TemplateResponse("dashboard.html", {"request": request, "logs": logs, "emails": emails, "tasks": tasks, "stats": stats})


@app.post("/run/inbox")
def run_inbox():
    scheduled_email_monitor()
    return RedirectResponse("/", status_code=303)


@app.post("/run/report")
def run_report():
    scheduled_weekly_report()
    return RedirectResponse("/", status_code=303)


@app.post("/tasks")
def create_task(title: str = Form(...), owner: str = Form(""), due_date: str = Form("")):
    with db_conn() as db:
        db.execute("INSERT INTO tasks(created_at,title,owner,due_date) VALUES(?,?,?,?)", (datetime.now(timezone.utc).isoformat(), title, owner, due_date))
    log_event("task", "success", f"Created task: {title}")
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-business-assistant"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
