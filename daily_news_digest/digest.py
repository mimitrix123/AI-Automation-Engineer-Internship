"""Automated daily news, weather and motivational quote email digest."""

from __future__ import annotations

import html
import os
import smtplib
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import requests


@dataclass(frozen=True)
class Config:
    news_api_key: str
    weather_api_key: str
    weather_city: str
    news_country: str
    news_category: str
    news_limit: int
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from: str
    email_to: str

    @classmethod
    def from_env(cls) -> "Config":
        required = ["NEWS_API_KEY", "WEATHER_API_KEY", "WEATHER_CITY", "SMTP_HOST", "SMTP_PORT", "SMTP_USERNAME", "SMTP_PASSWORD", "EMAIL_FROM", "EMAIL_TO"]
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise ValueError(f"Missing environment variables: {', '.join(missing)}")
        return cls(
            news_api_key=os.environ["NEWS_API_KEY"], weather_api_key=os.environ["WEATHER_API_KEY"],
            weather_city=os.environ["WEATHER_CITY"], news_country=os.getenv("NEWS_COUNTRY", "us"),
            news_category=os.getenv("NEWS_CATEGORY", "general"), news_limit=int(os.getenv("NEWS_LIMIT", "5")),
            smtp_host=os.environ["SMTP_HOST"], smtp_port=int(os.environ["SMTP_PORT"]),
            smtp_username=os.environ["SMTP_USERNAME"], smtp_password=os.environ["SMTP_PASSWORD"],
            email_from=os.environ["EMAIL_FROM"], email_to=os.environ["EMAIL_TO"],
        )


def get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def fetch_news(config: Config) -> list[dict[str, str]]:
    data = get_json("https://newsapi.org/v2/top-headlines", {
        "apiKey": config.news_api_key, "country": config.news_country,
        "category": config.news_category, "pageSize": config.news_limit,
    })
    if data.get("status") != "ok":
        raise RuntimeError(data.get("message", "News API error"))
    return [
        {"title": a.get("title") or "Untitled article", "url": a.get("url") or "#",
         "source": (a.get("source") or {}).get("name") or "Unknown source"}
        for a in data.get("articles", [])[:config.news_limit]
    ]


def fetch_weather(config: Config) -> dict[str, str]:
    data = get_json("https://api.weatherapi.com/v1/current.json", {
        "key": config.weather_api_key, "q": config.weather_city, "aqi": "no"
    })
    current = data["current"]
    return {
        "location": f"{data['location']['name']}, {data['location']['country']}",
        "condition": current["condition"]["text"], "temperature": f"{current['temp_c']}°C",
        "feels_like": f"{current['feelslike_c']}°C", "humidity": f"{current['humidity']}%",
        "wind": f"{current['wind_kph']} km/h",
    }


def fetch_quote() -> dict[str, str]:
    data = get_json("https://api.quotable.io/random")
    return {"content": data["content"], "author": data.get("author", "Unknown")}


def build_html(news: list[dict[str, str]], weather: dict[str, str], quote: dict[str, str]) -> str:
    items = "".join(
        f'<li style="margin-bottom:16px"><a href="{html.escape(x["url"], quote=True)}" style="color:#2563eb;text-decoration:none;font-weight:bold">{html.escape(x["title"])}</a><div style="color:#64748b;font-size:13px">{html.escape(x["source"])}</div></li>'
        for x in news
    ) or "<li>No headlines available today.</li>"
    return f'''<!doctype html><html><body style="margin:0;background:#f1f5f9;font-family:Arial;color:#0f172a"><table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 12px"><tr><td align="center"><table width="600" style="max-width:600px;width:100%;background:white;border-radius:16px;overflow:hidden"><tr><td style="padding:28px 32px;background:#0f172a;color:white"><h1 style="margin:0">Your Daily Digest</h1><p style="color:#cbd5e1">News, weather, and one good thought for today.</p></td></tr><tr><td style="padding:28px 32px"><h2>Top Headlines</h2><ol>{items}</ol><div style="margin-top:28px;padding:20px;border-radius:12px;background:#eff6ff"><h2>Weather</h2><strong>{html.escape(weather['location'])}</strong><p>{html.escape(weather['condition'])} · {html.escape(weather['temperature'])} · feels like {html.escape(weather['feels_like'])}</p><small>Humidity {html.escape(weather['humidity'])} · Wind {html.escape(weather['wind'])}</small></div><div style="margin-top:28px;padding:24px;border-left:4px solid #2563eb;background:#f8fafc"><h2>Motivation</h2><p style="font-size:17px;font-style:italic;line-height:1.6">“{html.escape(quote['content'])}”</p><span style="color:#64748b">— {html.escape(quote['author'])}</span></div></td></tr><tr><td style="padding:20px;text-align:center;color:#94a3b8;font-size:12px">Automated daily digest · Python + APIs + smtplib</td></tr></table></td></tr></table></body></html>'''


def send_email(config: Config, body: str) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Daily Digest"
    message["From"] = config.email_from
    message["To"] = config.email_to
    message.attach(MIMEText("Your Daily Digest is available in HTML format.", "plain"))
    message.attach(MIMEText(body, "html"))
    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(config.smtp_username, config.smtp_password)
        server.sendmail(config.email_from, [config.email_to], message.as_string())


def main() -> None:
    config = Config.from_env()
    body = build_html(fetch_news(config), fetch_weather(config), fetch_quote())
    send_email(config, body)
    print("Daily digest sent successfully.")


if __name__ == "__main__":
    main()
