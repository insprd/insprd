#!/usr/bin/env python3

import os
import re
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
from bs4 import BeautifulSoup

# Configuration
GITHUB_USERNAME = 'insprd'
WORK_URL = 'https://legrand.design/work'
POSTS_API_URL = 'https://posts.legrand.design/api/v1/accounts/110675830643979741/statuses'
README_FILE = 'README.md'

def get_work_items() -> List[Dict[str, str]]:
    """Fetch work items from legrand.design/work"""
    try:
        response = requests.get(WORK_URL)
        if response.status_code != 200:
            print(f"Error fetching work items: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        work_items = []

        # Look for work items in the HTML structure
        # Based on the HTML structure I observed, work items are in specific containers
        articles = soup.find_all('a', href=lambda x: x and x.startswith('/work/'))

        for article in articles[:5]:  # Get top 5 work items
            title_elem = article.find('h2')
            desc_elem = article.find('span', class_=lambda x: x and 'rt-Text' in x)
            date_elem = article.find('span', class_=lambda x: x and 'rt-Text' in x and 'rt-r-size-1' in x)

            if title_elem:
                title = title_elem.get_text(strip=True)
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                date = date_elem.get_text(strip=True) if date_elem else ''
                url = f"https://legrand.design{article.get('href')}"

                work_items.append({
                    'title': title,
                    'description': description,
                    'date': date,
                    'url': url
                })

        return work_items
    except Exception as e:
        print(f"Error parsing work items: {e}")
        return []

def get_recent_posts() -> List[Dict[str, str]]:
    """Fetch recent posts from Mastodon API"""
    try:
        response = requests.get(POSTS_API_URL, params={'limit': 5})
        if response.status_code != 200:
            print(f"Error fetching posts: {response.status_code}")
            return []

        posts_data = response.json()
        posts = []

        for post in posts_data:
            # Parse the HTML content to get plain text
            soup = BeautifulSoup(post.get('content', ''), 'html.parser')
            content = soup.get_text(strip=True)

            # Truncate content if too long
            if len(content) > 150:
                content = content[:147] + '...'

            created_at = post.get('created_at', '')
            post_url = post.get('url', '')

            posts.append({
                'content': content,
                'date': created_at,
                'url': post_url
            })

        return posts
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

def format_date(date_str: str) -> str:
    """Format ISO date string to readable format"""
    try:
        # Handle different date formats
        if 'T' in date_str:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date_obj = datetime.strptime(date_str, '%B %d, %Y')
        return date_obj.strftime('%B %d, %Y')
    except:
        return date_str

def update_readme():
    """Update the README.md file with fresh content"""
    with open(README_FILE, 'r') as f:
        content = f.read()

    # Get data
    work_items = get_work_items()
    posts = get_recent_posts()

    # Format work items
    work_md = ""
    for item in work_items:
        work_md += f"- **[{item['title']}]({item['url']})**"
        if item['date']:
            work_md += f" - {format_date(item['date'])}"
        work_md += "\n"
        if item['description']:
            work_md += f"  - {item['description']}\n"

    if not work_md:
        work_md = "No work items found.\n"

    # Format posts
    posts_md = ""
    for post in posts:
        posts_md += f"- {post['content']}"
        if post['date']:
            posts_md += f" - {format_date(post['date'])}"
        if post['url']:
            posts_md += f" - [View post]({post['url']})"
        posts_md += "\n"

    if not posts_md:
        posts_md = "No recent posts found.\n"

    # Update content
    content = re.sub(
        r'<!-- work starts -->.*?<!-- work ends -->',
        f'<!-- work starts -->\n{work_md}<!-- work ends -->',
        content,
        flags=re.DOTALL
    )

    content = re.sub(
        r'<!-- posts starts -->.*?<!-- posts ends -->',
        f'<!-- posts starts -->\n{posts_md}<!-- posts ends -->',
        content,
        flags=re.DOTALL
    )

    # Update last updated timestamp
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    content = re.sub(
        r'<!-- last_updated starts -->.*?<!-- last_updated ends -->',
        f'<!-- last_updated starts -->{now}<!-- last_updated ends -->',
        content,
        flags=re.DOTALL
    )

    # Write updated content
    with open(README_FILE, 'w') as f:
        f.write(content)

    print("README.md updated successfully!")

if __name__ == '__main__':
    update_readme()
