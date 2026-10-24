"""Fetch stories from Hacker News and Techmeme."""
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlparse

import feedparser
import requests

from . import config

HEADERS = {"User-Agent": config.USER_AGENT}


@dataclass
class Story:
    source: str                 # "HN" or "Techmeme"
    title: str
    url: str
    discussion_url: str | None = None
    points: int | None = None
    comments: int | None = None
    hn_id: str | None = None

    @property
    def key(self) -> str:
        """Dedup key. Same article from HN and Techmeme -> same key."""
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


def fetch_hacker_news() -> list[Story]:
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
        if points < config.HN_MIN_POINTS or not hit.get("title"):
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
            )
        )
    return stories
