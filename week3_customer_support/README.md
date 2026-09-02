# Week 3 — Automated Customer Support System

An AI-assisted customer support chatbot that answers common questions from a local knowledge base, escalates complex or uncertain issues by email, logs conversations to Google Sheets, and sends a daily summary report.

## Architecture

```text
Customer message
      ↓
Knowledge-base search
      ↓
AI response generation
      ↓
Confidence / escalation check
   ↙           ↘
Answer       Escalate → Email support
   ↓
Google Sheets conversation log

Daily scheduler → summary.py → email report
```

## Features

- Knowledge-base retrieval from `knowledge_base.json`
- OpenAI-powered answer generation grounded in retrieved KB entries
- Automatic escalation for low-confidence or complex requests
- SMTP email escalation
- Google Sheets logging via a service account
- Daily support summary email with conversation and escalation counts
- Environment-variable configuration; no secrets stored in source control

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Create a Google Cloud service account, enable the Google Sheets API, download its JSON credentials, and share your target spreadsheet with the service account email. Set `GOOGLE_SERVICE_ACCOUNT_FILE` to the credentials path and `GOOGLE_SHEET_NAME` to the spreadsheet name.

Set `OPENAI_API_KEY` and the SMTP settings in `.env`. Never commit real credentials.

## Run the chatbot

```bash
python week3_customer_support/support_bot.py
```

The chatbot runs interactively in the terminal. Type `exit` to stop.

## Send the daily report

```bash
python week3_customer_support/summary.py
```

Schedule that command with cron, Windows Task Scheduler, or GitHub Actions. The daily report reads the Google Sheet and emails the previous day's support activity.

## Knowledge base

Edit `knowledge_base.json` to add company-specific FAQs, policies, support hours, and troubleshooting information.
