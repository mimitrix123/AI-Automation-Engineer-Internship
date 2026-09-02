"""AI customer-support chatbot with KB retrieval, escalation, email and Sheets logging."""
from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path

import gspread
from openai import OpenAI
from oauth2client.service_account import ServiceAccountCredentials

BASE = Path(__file__).parent


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing environment variable: {name}")
    return value


def load_kb() -> list[dict[str, str]]:
    return json.loads((BASE / "knowledge_base.json").read_text(encoding="utf-8"))["faqs"]


def retrieve(query: str, kb: list[dict[str, str]], limit: int = 3) -> list[dict[str, str]]:
    words = {w.lower().strip(".,?!") for w in query.split() if len(w) > 2}
    scored = []
    for item in kb:
        text = f"{item['question']} {item['answer']}".lower()
        score = sum(1 for word in words if word in text)
        scored.append((score, item))
    return [item for score, item in sorted(scored, key=lambda x: x[0], reverse=True)[:limit] if score > 0]


def log_to_sheet(user: str, message: str, answer: str, escalated: bool) -> None:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(env("GOOGLE_SERVICE_ACCOUNT_FILE"), scope)
    sheet = gspread.authorize(creds).open(env("GOOGLE_SHEET_NAME")).sheet1
    sheet.append_row([datetime.now(timezone.utc).isoformat(), user, message, answer, "Yes" if escalated else "No"])


def send_email(subject: str, body: str, recipient: str) -> None:
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = env("EMAIL_FROM")
    msg["To"] = recipient
    with smtplib.SMTP(env("SMTP_HOST"), int(env("SMTP_PORT")), timeout=30) as server:
        server.starttls()
        server.login(env("SMTP_USERNAME"), env("SMTP_PASSWORD"))
        server.sendmail(env("EMAIL_FROM"), [recipient], msg.as_string())


def answer_query(client: OpenAI, query: str, kb: list[dict[str, str]]) -> tuple[str, bool]:
    matches = retrieve(query, kb)
    context = "\n\n".join(f"Q: {x['question']}\nA: {x['answer']}" for x in matches)
    prompt = f"""You are a customer support assistant. Answer only from the supplied knowledge base.
If the KB does not contain enough information, say you need a human agent and set escalate=true.
Return JSON only: {{\"answer\": \"...\", \"escalate\": true/false}}

KNOWLEDGE BASE:
{context or 'No relevant knowledge-base entry found.'}

CUSTOMER: {query}"""
    response = client.responses.create(model=env("OPENAI_MODEL", "gpt-5.6-luna"), input=prompt)
    data = json.loads(response.output_text)
    return str(data["answer"]), bool(data["escalate"])


def main() -> None:
    user = os.getenv("SUPPORT_USER", "Customer")
    client = OpenAI(api_key=env("OPENAI_API_KEY"))
    kb = load_kb()
    print("Customer Support Bot — type 'exit' to quit.")
    while True:
        query = input("You: ").strip()
        if query.lower() == "exit":
            break
        if not query:
            continue
        try:
            answer, escalated = answer_query(client, query, kb)
            if escalated:
                send_email("Customer Support Escalation", f"Customer: {user}\n\nIssue:\n{query}\n\nBot response:\n{answer}", env("ESCALATION_EMAIL"))
                answer += "\n\nI've escalated this to our support team."
            log_to_sheet(user, query, answer, escalated)
            print(f"Bot: {answer}")
        except Exception as exc:
            print(f"System error: {exc}")


if __name__ == "__main__":
    main()
