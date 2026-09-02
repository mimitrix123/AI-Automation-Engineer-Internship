"""AI-powered customer support chatbot with knowledge-base lookup, escalation, logging and daily summaries."""

from __future__ import annotations

import argparse
import json
import os
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import gspread
from openai import OpenAI
from oauth2client.service_account import ServiceAccountCredentials


KB_PATH = Path(__file__).with_name("knowledge_base.json")
SHEET_HEADERS = ["timestamp", "customer", "user_message", "bot_response", "intent", "escalated"]


def load_config() -> dict[str, str]:
    required = [
        "OPENAI_API_KEY", "GOOGLE_SHEET_ID", "GOOGLE_SERVICE_ACCOUNT_FILE",
        "SUPPORT_EMAIL", "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD",
    ]
    missing = [x for x in required if not os.getenv(x)]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")
    return {x: os.environ[x] for x in required}


def load_knowledge_base() -> list[dict[str, Any]]:
    with KB_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def find_kb_matches(message: str, kb: list[dict[str, Any]]) -> list[dict[str, Any]]:
    words = {w.lower() for w in message.split() if len(w) > 2}
    scored = []
    for item in kb:
        haystack = (item["question"] + " " + item["answer"] + " " + " ".join(item.get("keywords", []))).lower()
        score = sum(word in haystack for word in words)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:3]]


def answer_customer(client: OpenAI, message: str, matches: list[dict[str, Any]]) -> tuple[str, str, bool]:
    context = "\n\n".join(f"Q: {x['question']}\nA: {x['answer']}" for x in matches)
    prompt = f"""You are a helpful customer support agent. Answer the customer using the knowledge base below.

Knowledge base:
{context or 'No relevant knowledge-base entry was found.'}

Customer: {message}

Return ONLY JSON with keys: response, intent, escalate.
Set escalate=true when the issue is account-specific, sensitive, unresolved, a complaint requiring a human, or outside the knowledge base. Never invent policies, refunds, prices, account data, or guarantees.
Keep the response concise and helpful."""
    result = client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"), input=prompt)
    data = json.loads(result.output_text.strip().replace("```json", "").replace("```", "").strip())
    return str(data["response"]), str(data.get("intent", "general")), bool(data.get("escalate", False))


def get_sheet(config: dict[str, str]):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(config["GOOGLE_SERVICE_ACCOUNT_FILE"], scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(config["GOOGLE_SHEET_ID"]).sheet1
    if not sheet.get_all_values():
        sheet.append_row(SHEET_HEADERS)
    return sheet


def log_conversation(sheet, customer: str, message: str, response: str, intent: str, escalated: bool) -> None:
    sheet.append_row([
        datetime.now(timezone.utc).isoformat(), customer, message, response, intent, str(escalated)
    ])


def send_escalation(config: dict[str, str], customer: str, message: str, response: str) -> None:
    body = f"Customer: {customer}\n\nMessage:\n{message}\n\nBot response:\n{response}\n\nA human review is required."
    email = MIMEText(body)
    email["Subject"] = f"Customer Support Escalation — {customer}"
    email["From"] = config["SMTP_USERNAME"]
    email["To"] = config["SUPPORT_EMAIL"]
    with smtplib.SMTP(config["SMTP_HOST"], int(config["SMTP_PORT"]), timeout=30) as server:
        server.starttls()
        server.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
        server.send_message(email)


def daily_summary(config: dict[str, str], sheet) -> None:
    rows = sheet.get_all_records()
    today = datetime.now(timezone.utc).date().isoformat()
    rows = [r for r in rows if str(r.get("timestamp", "")).startswith(today)]
    escalations = [r for r in rows if str(r.get("escalated", "")).lower() == "true"]
    intents: dict[str, int] = {}
    for row in rows:
        intent = str(row.get("intent", "general"))
        intents[intent] = intents.get(intent, 0) + 1
    body = "Daily Customer Support Summary\n\n"
    body += f"Conversations: {len(rows)}\nEscalations: {len(escalations)}\n"
    body += "Top intents:\n" + "\n".join(f"- {k}: {v}" for k, v in sorted(intents.items(), key=lambda x: -x[1]))
    email = MIMEText(body)
    email["Subject"] = f"Daily Customer Support Summary — {today}"
    email["From"] = config["SMTP_USERNAME"]
    email["To"] = config["SUPPORT_EMAIL"]
    with smtplib.SMTP(config["SMTP_HOST"], int(config["SMTP_PORT"]), timeout=30) as server:
        server.starttls()
        server.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
        server.send_message(email)


def chat() -> None:
    config = load_config()
    client = OpenAI(api_key=config["OPENAI_API_KEY"])
    kb = load_knowledge_base()
    sheet = get_sheet(config)
    print("Customer Support Bot — type 'exit' to quit.")
    customer = input("Customer name/email: ").strip() or "Anonymous"
    while True:
        message = input("You: ").strip()
        if message.lower() in {"exit", "quit"}:
            break
        matches = find_kb_matches(message, kb)
        response, intent, escalated = answer_customer(client, message, matches)
        print(f"Bot: {response}")
        log_conversation(sheet, customer, message, response, intent, escalated)
        if escalated:
            send_escalation(config, customer, message, response)
            print("[Escalated to human support]")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true", help="Send today's support summary")
    args = parser.parse_args()
    config = load_config()
    sheet = get_sheet(config)
    if args.summary:
        daily_summary(config, sheet)
    else:
        chat()


if __name__ == "__main__":
    main()
