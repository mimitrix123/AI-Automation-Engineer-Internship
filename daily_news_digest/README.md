# Daily News & Weather Digest

An automated Python email digest that fetches top news headlines, current weather, and a motivational quote, then sends a clean HTML email using `smtplib`.

## APIs

- NewsAPI: top headlines
- WeatherAPI: current weather
- Quotable: random motivational quote

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Set the environment variables in `.env` (or export them in your shell). Never commit real API keys or SMTP passwords.

For Gmail SMTP, use an App Password rather than your normal account password when required by your account security settings.

## Run

```bash
python daily_news_digest/digest.py
```

## Automation

Run the command daily with Windows Task Scheduler, cron, or GitHub Actions. The script itself is intentionally stateless so the scheduler controls the daily cadence.

## Configuration

`NEWS_COUNTRY`, `NEWS_CATEGORY`, and `NEWS_LIMIT` are optional. `WEATHER_CITY` controls the weather location.
