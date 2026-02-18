from __future__ import annotations

from datetime import datetime

import feedparser

DEFAULT_SOURCES = [
    ("Hydro-Québec", "https://www.hydroquebec.com/data/rss/en/nouvelles.xml"),
    ("Gouv Québec", "https://www.quebec.ca/nouvelles/rss.xml"),
    ("Radio-Canada Énergie", "https://ici.radio-canada.ca/rss/4159"),
]


def collect_articles(limit_per_source: int = 10) -> list[dict]:
    articles: list[dict] = []
    for source_name, source_url in DEFAULT_SOURCES:
        feed = feedparser.parse(source_url)
        for entry in feed.entries[:limit_per_source]:
            published = None
            if getattr(entry, "published_parsed", None):
                published = datetime(*entry.published_parsed[:6])
            articles.append(
                {
                    "title": entry.get("title", "Sans titre"),
                    "url": entry.get("link", ""),
                    "source": source_name,
                    "published_at": published,
                    "summary": entry.get("summary", ""),
                }
            )
    return [a for a in articles if a["url"]]
