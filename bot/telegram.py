"""Format stories and send them through the Telegram Bot API."""
import html
import time

import requests

from . import config
from .sources import Story

API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _link(label: str, url: str) -> str:
    return f'<a href="{html.escape(url, quote=True)}">{label}</a>'


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

    lines.append(f"<i>{s.source}</i>")
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
