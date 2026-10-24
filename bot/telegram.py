"""Format stories and send them through the Telegram Bot API."""
import html
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import requests

from . import config
from .sources import Story

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _link(label: str, url: str) -> str:
    return f'<a href="{html.escape(url, quote=True)}">{label}</a>'


def _tz():
    try:
        return ZoneInfo(config.TIMEZONE)
    except ZoneInfoNotFoundError:  # e.g. Windows without the tzdata package
        return timezone.utc


def _ago(dt: datetime) -> str:
    secs = int((datetime.now(timezone.utc) - dt).total_seconds())
    if secs < 60:
        return "just now"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h ago"
    return f"{hours // 24}d ago"


def _when(dt: datetime) -> str:
    local = dt.astimezone(_tz())
    return f"{local.strftime('%b %d, %H:%M %Z')} · {_ago(dt)}"


def format_story(s: Story) -> str:
    icon = "🟠" if s.source == "HN" else "📰"
    lines = [f"{icon} <b>{html.escape(s.title)}</b>"]

    if s.points is not None:
        stats = f"▲ {s.points}"
        if s.comments is not None:
            stats += f" · 💬 {s.comments}"
        lines.append(stats)

    links = []
    if s.url != s.discussion_url:
        links.append(_link("Article", s.url))
    if s.discussion_url:
        label = "Comments" if s.source == "HN" else "Techmeme"
        links.append(_link(label, s.discussion_url))
    if links:
        lines.append(" · ".join(links))

    footer = s.source
    if s.published:
        footer += f" · {_when(s.published)}"
    lines.append(f"<i>{footer}</i>")
    return "\n".join(lines)


def send_message(text: str) -> None:
    url = API_URL.format(token=config.TELEGRAM_TOKEN)
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    for _ in range(3):
        r = requests.post(url, json=payload, timeout=config.REQUEST_TIMEOUT)
        if r.status_code == 429:  # rate limited: wait as told, then retry
            wait = r.json().get("parameters", {}).get("retry_after", 5)
            time.sleep(wait + 1)
            continue
        r.raise_for_status()
        return
    raise RuntimeError("Telegram rate limit: gave up after 3 attempts")
