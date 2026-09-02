# Major Project — Week 4: AI Business Automation Platform

A cloud-ready AI business assistant that monitors email, extracts action items, drafts responses, schedules meetings, stores tasks/logs, and generates weekly reports through a web dashboard.

## Architecture

```text
Email inbox (IMAP)
      ↓
AI analysis (OpenAI Responses API)
      ├── action item → task/log
      ├── draft reply → optional auto-send
      └── explicit meeting → Google Calendar
      ↓
SQLite activity store
      ↓
FastAPI dashboard + health endpoint
      ↓
Weekly AI report → Markdown / optional email
```

## Features

- Unread email polling on a configurable interval.
- AI extraction of action items, priority, draft response, and explicit meeting details.
- Safe default: responses are drafted but **not auto-sent** unless `AUTO_SEND_RESPONSES=true`.
- Google Calendar scheduling only when an explicit meeting time is present.
- SQLite persistence for emails, tasks, and automation logs.
- Web dashboard with status metrics, recent emails, tasks, and logs.
- Weekly AI-generated report with optional email delivery.
- Dockerfile for cloud/container deployment.
- `/health` endpoint for deployment health checks.

## Setup

1. Create an OpenAI API key.
2. Create Google Calendar OAuth desktop credentials and save them as `credentials.json` in this folder.
3. Configure an email account with IMAP/SMTP access. For Gmail, use an App Password rather than your normal password.
4. Copy `.env.example` to `.env` and fill in the values.
5. Install dependencies:

```bash
pip install -r requirements.txt
```

6. Start locally:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Cloud deployment

Build and run the container on a service such as Cloud Run, Azure Container Apps, Render, Railway, or another container host. Provide the environment variables through the platform's secret manager and mount/provide the Google OAuth credentials securely. Persist `assistant.db` and `token.json` if you need state across container restarts; alternatively replace SQLite with managed Postgres for a multi-instance production deployment.

## Security

- Never commit `.env`, `credentials.json`, `token.json`, or real passwords/API keys.
- Keep `AUTO_SEND_RESPONSES=false` until the workflow has been tested with representative emails.
- Treat AI output as untrusted: the assistant is instructed not to invent dates, policies, prices, or commitments.
- For production, add authentication/SSO to the dashboard before exposing it publicly.
