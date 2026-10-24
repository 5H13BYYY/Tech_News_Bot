"""Fetch stories from Hacker News, Techmeme and Lobsters."""
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlparse

import feedparser
import requests

from . import config

HEADERS = {"User-Agent": config.USER_AGENT}


@dataclass
class Story:
    source: str                 # "HN", "Techmeme" or "Lobsters"
    title: str
    url: str
    discussion_url: str | None = None
    points: int | None = None
    comments: int | None = None
    hn_id: str | None = None
    published: datetime | None = None  # timezone-aware, UTC

    @property
    def key(self) -> str:
        """Dedup key. Same article from different sources -> same key."""
        if self.url.startswith("https://news.ycombinator.com/item"):
            return f"hn:{self.hn_id}"
        return normalize_url(self.url)


def normalize_url(url: str) -> str:
    p = urlparse(url.strip())
    host = p.netloc.lower().removeprefix("www.")
    drop = {"ref", "fbclid", "gclid", "source"}
    query = [
        (k, v)
        for k, v in parse_qsl(p.query)
        if not k.lower().startswith("utm_") and k.lower() not in drop
    ]
    path = p.path.rstrip("/")
    return f"{host}{path}" + (f"?{urlencode(query)}" if query else "")


def _from_unix(ts) -> datetime | None:
    return datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None


def _from_struct(t) -> datetime | None:
    """feedparser gives a UTC time.struct_time."""
    return datetime(*t[:6], tzinfo=timezone.utc) if t else None


def _from_iso(value) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def fetch_hacker_news(min_points: int | None = None) -> list[Story]:
    threshold = config.HN_MIN_POINTS if min_points is None else min_points
    r = requests.get(
        config.HN_API,
        params={"tags": "front_page", "hitsPerPage": config.HN_MAX_ITEMS},
        headers=HEADERS,
        timeout=config.REQUEST_TIMEOUT,
    )
    r.raise_for_status()

    stories = []
    for hit in r.json().get("hits", []):
        points = hit.get("points") or 0
        if points < threshold or not hit.get("title"):
            continue
        hn_url = f"https://news.ycombinator.com/item?id={hit['objectID']}"
        stories.append(
            Story(
                source="HN",
                title=hit["title"],
                url=hit.get("url") or hn_url,  # Ask HN etc. have no external URL
                discussion_url=hn_url,
                points=points,
                comments=hit.get("num_comments"),
                hn_id=str(hit["objectID"]),
                published=_from_unix(hit.get("created_at_i")),
            )
        )
    return stories


def fetch_techmeme() -> list[Story]:
    r = requests.get(
        config.TECHMEME_FEED, headers=HEADERS, timeout=config.REQUEST_TIMEOUT
    )
    r.raise_for_status()
    feed = feedparser.parse(r.content)

    stories = []
    for entry in feed.entries[: config.TECHMEME_MAX_ITEMS]:
        if not entry.get("link") or not entry.get("title"):
            continue
        stories.append(
            Story(
                source="Techmeme",
                title=entry.title.strip(),
                url=entry.link,
                discussion_url=entry.get("comments"),
                published=_from_struct(entry.get("published_parsed")),
            )
        )
    return stories


def fetch_lobsters(min_score: int | None = None) -> list[Story]:
    threshold = config.LOBSTERS_MIN_SCORE if min_score is None else min_score
    r = requests.get(
        config.LOBSTERS_URL, headers=HEADERS, timeout=config.REQUEST_TIMEOUT
    )
    r.raise_for_status()

    stories = []
    for item in r.json()[: config.LOBSTERS_MAX_ITEMS]:
        score = item.get("score") or 0
        discussion = item.get("comments_url") or item.get("short_id_url")
        url = item.get("url") or discussion  # text posts have no external URL
        if score < threshold or not item.get("title") or not url:
            continue
        stories.append(
            Story(
                source="Lobsters",
                title=item["title"],
                url=url,
                discussion_url=discussion,
                points=score,
                comments=item.get("comment_count"),
                published=_from_iso(item.get("created_at")),
            )
        )
    return stories
