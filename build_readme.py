#!/usr/bin/env python3

import os
import re
import requests
from datetime import datetime, timezone
from typing import List, Dict


# Configuration
SITE_URL = "https://mattlegrand.ai"
# JSON Feed 1.1 of the articles on mattlegrand.ai; rss.xml and atom.xml (the
# static links under the README's table) carry the same items. Every entry is an article at /work/<slug>/. The JSON feed
# also carries a custom `_featured: true` on the articles the homepage
# features, so the README can mirror the homepage's Featured/Recent split.
# FEED_URL can be overridden for a local test against a dev build.
FEED_URL = os.environ.get("FEED_URL", f"{SITE_URL}/feed.json")
README_FILE = "README.md"
# Same cap as the homepage's Recent block.
RECENT_COUNT = 6


def get_articles() -> List[Dict[str, str]]:
    """Fetch articles from the JSON feed, newest first"""
    try:
        response = requests.get(FEED_URL, timeout=30)
        if response.status_code != 200:
            print(f"Error fetching feed: {response.status_code}")
            return []

        feed_data = response.json()
        articles = []

        for item in feed_data.get("items", []):
            title = item.get("title", "")
            date_published = item.get("date_published", "")
            url = item.get("url", "")

            if title and url:
                articles.append(
                    {
                        "title": title,
                        "date": date_published,
                        "url": url,
                        "featured": bool(item.get("_featured")),
                    }
                )

        articles.sort(key=lambda x: x["date"], reverse=True)
        return articles
    except Exception as e:
        print(f"Error parsing feed: {e}")
        return []


def format_date(date_str: str) -> str:
    """Format ISO date string to readable format"""
    try:
        if "T" in date_str:
            # ISO datetime format (e.g., "2025-04-02T00:00:00Z")
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        elif "-" in date_str and len(date_str) == 10:
            # ISO date format (e.g., "2025-04-02")
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            # Already formatted (e.g., "April 02, 2025")
            date_obj = datetime.strptime(date_str, "%B %d, %Y")
        return date_obj.strftime("%B %d, %Y")
    except Exception:
        return date_str


def format_list(articles: List[Dict[str, str]]) -> str:
    md = ""
    for item in articles:
        md += f"- **[{item['title']}]({item['url']})**"
        if item["date"]:
            md += f" - {format_date(item['date'])}"
        md += "\n"
    return md


def replace_section(content: str, name: str, body: str) -> str:
    return re.sub(
        rf"<!-- {name} starts -->.*?<!-- {name} ends -->",
        f"<!-- {name} starts -->\n{body}<!-- {name} ends -->",
        content,
        flags=re.DOTALL,
    )


def update_readme():
    """Update the README.md file with fresh content"""
    with open(README_FILE, "r") as f:
        content = f.read()

    articles = get_articles()

    # A feed outage must not wipe the lists: keep the README as it is.
    if not articles:
        print("No articles fetched; leaving README.md unchanged.")
        return

    # Mirror the homepage: a curated Featured block and an auto Recent block
    # (newest first, capped). An article can appear in both.
    featured = [a for a in articles if a["featured"]]
    recent = articles[:RECENT_COUNT]

    content = replace_section(content, "featured", format_list(featured))
    content = replace_section(content, "recent", format_list(recent))

    now = datetime.now(timezone.utc).strftime("%B %d, %Y at %I:%M %p UTC")
    content = re.sub(
        r"<!-- last_updated starts -->.*?<!-- last_updated ends -->",
        f"<!-- last_updated starts -->{now}<!-- last_updated ends -->",
        content,
        flags=re.DOTALL,
    )

    with open(README_FILE, "w") as f:
        f.write(content)

    print("README.md updated successfully!")


if __name__ == "__main__":
    update_readme()
