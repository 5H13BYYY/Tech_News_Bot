"""Daily morning digest: a short recap of what's on each source right now."""
import html
import logging
from datetime import datetime

from . import config
from .sources import Story, fetch_hacker_news, fetch_lobsters, fetch_techmeme
from .telegram import get_tz, link, send_message

log = logging.getLogger("news-bot")


def _top_hn() -> list[Story]:
    stories = fetch_hacker_news(min_points=0)
    stories.sort(key=lambda s: s.points or 0, reverse=True)
    return stories[: config.DIGEST_HN_ITEMS]


def _top_techmeme() -> list[Story]:
    return fetch_techmeme()[: config.DIGEST_TECHMEME_ITEMS]


def _top_lobsters() -> list[Story]:
    return fetch_lobsters(min_score=0)[: config.DIGEST_LOBSTERS_ITEMS]


SECTIONS = [("🟠", "Hacker News", _top_hn), ("📰", "Techmeme", _top_techmeme)]
if config.LOBSTERS_ENABLED:
    SECTIONS.append(("🦞", "Lobsters", _top_lobsters))


def _line(i: int, s: Story) -> str:
    title = s.title if len(s.title) <= 110 else s.title[:109] + "…"
    line = f"{i}. {link(html.escape(title), s.url)}"
    if s.points is not None and s.discussion_url:
        comments = f"💬 {s.comments}" if s.comments is not None else "💬"
        line += f" (▲ {s.points} · {link(comments, s.discussion_url)})"
    return line


def build_digest() -> str | None:
    today = datetime.now(get_tz()).strftime("%a, %b %d")
    blocks = [f"☀️ <b>Morning digest · {today}</b>"]
    for icon, name, fetch in SECTIONS:
        try:
            items = fetch()
        except Exception as exc:
            log.warning("Digest: %s failed: %s", name, exc)
            continue
        if items:
            lines = [f"{icon} <b>{name}</b>"]
            lines += [_line(i, s) for i, s in enumerate(items, 1)]
            blocks.append("\n".join(lines))
    return "\n\n".join(blocks) if len(blocks) > 1 else None


def send_digest_now(dry_run: bool = False) -> bool:
    text = build_digest()
    if not text:
        log.warning("Digest is empty (all sources failed).")
        return False
    if dry_run:
        print(text)
        return True
    send_message(text, preview=False)
    return True


def maybe_send_digest(store, dry_run: bool = False) -> None:
    """Send once per local day, on the first run at/after DIGEST_HOUR."""
    if not config.DIGEST_ENABLED:
        return
    now = datetime.now(get_tz())
    key = f"digest:{now.date().isoformat()}"
    if now.hour < config.DIGEST_HOUR or key in store:
        return
    try:
        if not send_digest_now(dry_run):
            return
    except Exception as exc:
        log.error("Digest send failed (%s); will retry next run.", exc)
        return
    store.add(key)
    log.info("Digest %s.", "shown" if dry_run else "sent")
