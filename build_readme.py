#!/usr/bin/env python3

import os
import re
import json
import requests
from datetime import datetime
from typing import List, Dict, Any


# Configuration
GITHUB_USERNAME = "insprd"
WORK_FEED_URL = "https://legrand.design/feed.json"
POSTS_FEED_URL = "https://legrand.design/posts/feed.json"
README_FILE = "README.md"


def get_work_items() -> List[Dict[str, str]]:
    """Fetch work items from JSON feed"""
    try:
        response = requests.get(WORK_FEED_URL)
        if response.status_code != 200:
            print(f"Error fetching work feed: {response.status_code}")
            return []

        feed_data = response.json()
        work_items = []

        # Parse JSON feed items
        for item in feed_data.get("items", []):
            title = item.get("title", "")
            description = item.get("summary", "")
            date_published = item.get("date_published", "")
            url = item.get("url", "")

            if title and url:
                work_items.append(
                    {
                        "title": title,
                        "description": description,
                        "date": date_published,
                        "url": url,
                    }
                )

        # Sort by date (newest first)
        work_items.sort(key=lambda x: x["date"], reverse=True)
        return work_items
    except Exception as e:
        print(f"Error parsing work feed: {e}")
        return []


def get_recent_posts() -> List[Dict[str, str]]:
    """Fetch recent posts from JSON feed"""
    try:
        response = requests.get(POSTS_FEED_URL)
        if response.status_code != 200:
            print(f"Error fetching posts feed: {response.status_code}")
            return []

        feed_data = response.json()
        posts = []

        # Parse JSON feed items
        for item in feed_data.get("items", []):
            title = item.get("title", "")
            date_published = item.get("date_published", "")
            url = item.get("url", "")

            content = title

            # Truncate content if too long
            if len(content) > 150:
                content = content[:147] + "..."

            if content and url:
                posts.append({"content": content, "date": date_published, "url": url})

                # Limit to 4 posts
                if len(posts) >= 4:
                    break

        return posts
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []


def format_date(date_str: str) -> str:
    """Format ISO date string to readable format"""
    try:
        # Handle different date formats
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
    except:
        return date_str


def update_readme():
    """Update the README.md file with fresh content"""
    with open(README_FILE, "r") as f:
        content = f.read()

    # Get data
    work_items = get_work_items()
    posts = get_recent_posts()

    # Format work items
    work_md = ""
    for item in work_items:
        work_md += f"- **[{item['title']}]({item['url']})**"
        if item["date"]:
            work_md += f" - {format_date(item['date'])}"
        work_md += "\n"

    if not work_md:
        work_md = "No work items found.\n"

    # Add feed links for work
    work_md += (
        "\n[RSS](https://legrand.design/rss) • [Atom](https://legrand.design/atom)\n"
    )

    # Format posts
    posts_md = ""
    for post in posts:
        posts_md += f"- {post['content']}"
        if post["date"]:
            posts_md += f" - {format_date(post['date'])}"
        if post["url"]:
            posts_md += f" - [View post]({post['url']})"
        posts_md += "\n"

    if not posts_md:
        posts_md = "No recent posts found.\n"

    # Add feed links for posts
    posts_md += "\n[RSS](https://legrand.design/posts/rss) • [Atom](https://legrand.design/posts/atom)\n"

    # Update content
    content = re.sub(
        r"<!-- work starts -->.*?<!-- work ends -->",
        f"<!-- work starts -->\n{work_md}<!-- work ends -->",
        content,
        flags=re.DOTALL,
    )

    content = re.sub(
        r"<!-- posts starts -->.*?<!-- posts ends -->",
        f"<!-- posts starts -->\n{posts_md}<!-- posts ends -->",
        content,
        flags=re.DOTALL,
    )

    # Update last updated timestamp
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p UTC")
    content = re.sub(
        r"<!-- last_updated starts -->.*?<!-- last_updated ends -->",
        f"<!-- last_updated starts -->{now}<!-- last_updated ends -->",
        content,
        flags=re.DOTALL,
    )

    # Write updated content
    with open(README_FILE, "w") as f:
        f.write(content)

    print("README.md updated successfully!")


if __name__ == "__main__":
    update_readme()
