import json
import os
import re
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from imaplib import IMAP4_SSL
from smtplib import SMTP

from openai import OpenAI

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
except ImportError:
    Credentials = None

SCOPES = ["https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/gmail.readonly"]


class BusinessAssistant:
    def __init__(self, log_event):
        self.log_event = log_event
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    def ai_json(self, prompt: str) -> dict:
        response = self.client.responses.create(model=self.model, input=prompt)
        text = response.output_text.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("AI did not return valid JSON")
        return json.loads(match.group(0))

    def analyze_email(self, sender: str, subject: str, body: str) -> dict:
        prompt = f"""Analyze this business email. Return ONLY JSON with keys: action_required (boolean), action_item (string), priority (low|medium|high), draft_response (string), meeting_requested (boolean), meeting_title (string), meeting_start (ISO-8601 or empty), meeting_duration_minutes (integer). Never invent dates, times, commitments, prices, or policies. If a meeting time is not explicit, leave meeting_start empty.\nSender: {sender}\nSubject: {subject}\nBody: {body[:10000]}"""
        return self.ai_json(prompt)

    def _imap(self):
        host = os.environ["IMAP_HOST"]
        port = int(os.getenv("IMAP_PORT", "993"))
        mail = IMAP4_SSL(host, port)
        mail.login(os.environ["EMAIL_USERNAME"], os.environ["EMAIL_PASSWORD"])
        mail.select(os.getenv("IMAP_FOLDER", "INBOX"))
        return mail

    def fetch_unread(self):
        mail = self._imap()
        status, data = mail.search(None, "UNSEEN")
        emails = []
        for num in data[0].split()[-int(os.getenv("MAX_EMAILS_PER_RUN", "20")):]:
            status, msg_data = mail.fetch(num, "(RFC822)")
            raw = msg_data[0][1]
            from email import message_from_bytes
            msg = message_from_bytes(raw)
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain" and not part.get_filename():
                        body += part.get_payload(decode=True).decode(errors="replace")
            else:
                body = msg.get_payload(decode=True).decode(errors="replace") if msg.get_payload(decode=True) else str(msg.get_payload())
            emails.append({"external_id": num.decode(), "sender": msg.get("From", ""), "subject": msg.get("Subject", ""), "body": body})
        mail.logout()
        return emails

    def send_email(self, recipient: str, subject: str, body: str):
        msg = EmailMessage()
        msg["From"] = os.environ["EMAIL_USERNAME"]
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)
        with SMTP(os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587"))) as smtp:
            smtp.starttls()
            smtp.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
            smtp.send_message(msg)

    def calendar_service(self):
        if Credentials is None:
            raise RuntimeError("Install Google Calendar dependencies")
        token_file = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
        creds = Credentials.from_authorized_user_file(token_file, SCOPES) if os.path.exists(token_file) else None
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(os.environ["GOOGLE_CREDENTIALS_FILE"], SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_file, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)

    def schedule_meeting(self, title: str, start_iso: str, duration_minutes: int, attendees=None):
        start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        end = start + timedelta(minutes=duration_minutes or 30)
        service = self.calendar_service()
        event = {"summary": title, "start": {"dateTime": start.isoformat()}, "end": {"dateTime": end.isoformat()}}
        if attendees:
            event["attendees"] = [{"email": x.strip()} for x in attendees if x.strip()]
        created = service.events().insert(calendarId="primary", body=event, sendUpdates="all").execute()
        self.log_event("calendar", "success", f"Meeting scheduled: {title}", {"event_id": created.get("id")})
        return created

    def process_inbox(self):
        processed = 0
        for item in self.fetch_unread():
            try:
                analysis = self.analyze_email(item["sender"], item["subject"], item["body"])
                with __import__("sqlite3").connect(os.getenv("DB_PATH", "assistant.db")) as db:
                    db.execute("INSERT OR IGNORE INTO emails(external_id,received_at,sender,subject,body,action_item,draft_response,status) VALUES(?,?,?,?,?,?,?,?)", (item["external_id"], datetime.now(timezone.utc).isoformat(), item["sender"], item["subject"], item["body"], analysis.get("action_item", ""), analysis.get("draft_response", ""), "analyzed"))
                if analysis.get("meeting_requested") and analysis.get("meeting_start"):
                    self.schedule_meeting(analysis.get("meeting_title") or item["subject"], analysis["meeting_start"], int(analysis.get("meeting_duration_minutes") or 30), [item["sender"]])
                if analysis.get("action_required") and analysis.get("draft_response"):
                    if os.getenv("AUTO_SEND_RESPONSES", "false").lower() == "true":
                        self.send_email(item["sender"], f"Re: {item['subject']}", analysis["draft_response"])
                        status = "responded"
                    else:
                        status = "drafted"
                    with __import__("sqlite3").connect(os.getenv("DB_PATH", "assistant.db")) as db:
                        db.execute("UPDATE emails SET status=? WHERE external_id=?", (status, item["external_id"]))
                self.log_event("email", "success", f"Processed: {item['subject']}")
                processed += 1
            except Exception as exc:
                self.log_event("email", "error", str(exc), {"subject": item["subject"]})
        return processed

    def generate_weekly_report(self):
        import sqlite3
        since = datetime.now(timezone.utc) - timedelta(days=7)
        with sqlite3.connect(os.getenv("DB_PATH", "assistant.db")) as db:
            logs = db.execute("SELECT event_type,status,message FROM logs WHERE created_at >= ? ORDER BY id", (since.isoformat(),)).fetchall()
            tasks = db.execute("SELECT title,owner,due_date,status FROM tasks WHERE created_at >= ?", (since.isoformat(),)).fetchall()
        prompt = f"Create a concise weekly business automation report in Markdown. Include highlights, email activity, task summary, failures/risks, and next actions. Data: {json.dumps({'logs': logs, 'tasks': tasks}, default=str)}"
        report = self.client.responses.create(model=self.model, input=prompt).output_text
        out = os.getenv("REPORT_FILE", "weekly_report.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(f"# Weekly Business Automation Report\n\n{report}\n")
        if os.getenv("SEND_WEEKLY_REPORT", "false").lower() == "true":
            self.send_email(os.environ["REPORT_RECIPIENT"], "Weekly AI Automation Report", report)
        self.log_event("weekly_report", "success", "Weekly report generated", {"file": out})
        return report
