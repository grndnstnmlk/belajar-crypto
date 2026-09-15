"""
Agent Reach Intelligence Engine
Synthesized from Agent Reach (https://github.com/Panniantong/agent-reach)
and Akademi Crypto Market Intelligence architecture.

Provides zero-API-fee internet scanning, social sentiment scraping,
web page markdown parsing (Jina Reader), and community pulse detection
for Antigravity and the Belajar Kripto Trading Desk.
"""

import json
import os
import sys
import time
import requests
import feedparser
from datetime import datetime

# Windows UTF-8 stdout configuration
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
REACH_CACHE_FILE = os.path.join(DATA_DIR, "agent_reach_feed.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

def fetch_url_markdown(url: str, timeout: int = 10) -> str:
    """
    Extracts clean markdown from any URL via Jina Reader (Zero API fee).
    """
    jina_endpoint = f"https://r.jina.ai/{url}"
    try:
        resp = requests.get(jina_endpoint, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        return f"Error fetching {url}: {e}"
    return ""

def scan_reddit_feed(subreddit: str = "CryptoCurrency", limit: int = 5) -> list:
    """
    Scrapes hot posts and community sentiment from a given subreddit using Agent Reach RSS channel.
    """
    url = f"https://www.reddit.com/r/{subreddit}/.rss"
    results = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:limit]:
            results.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "author": entry.get("author", "")
            })
    except Exception:
        pass
    return results

def scan_crypto_news_feed(limit: int = 5) -> list:
    """
    Fetches real-time institutional crypto headlines via decentralized RSS feeds.
    """
    feeds = [
        "https://cointelegraph.com/rss",
        "https://www.coindesk.com/arc/outboundfeeds/rss/"
    ]
    news = []
    for f_url in feeds:
        try:
            feed = feedparser.parse(f_url)
            for entry in feed.entries[:limit]:
                news.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "")[:200]
                })
                if len(news) >= limit:
                    break
        except Exception:
            continue
        if len(news) >= limit:
            break
    return news

def get_social_intelligence_digest() -> dict:
    """
    Generates a unified social intelligence pulse report from multiple zero-fee sources.
    """
    reddit_crypto = scan_reddit_feed("CryptoCurrency", limit=5)
    reddit_btc = scan_reddit_feed("Bitcoin", limit=5)
    news_feed = scan_crypto_news_feed(limit=5)
    
    digest = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "HEALTHY",
        "channels": {
            "reddit_cryptocurrency": reddit_crypto,
            "reddit_bitcoin": reddit_btc,
            "crypto_news_rss": news_feed,
            "jina_reader": "ONLINE"
        },
        "total_items_captured": len(reddit_crypto) + len(reddit_btc) + len(news_feed)
    }
    
    # Cache result
    try:
        with open(REACH_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(digest, f, indent=2)
    except Exception:
        pass
        
    return digest

if __name__ == "__main__":
    print("=" * 60)
    print("👁️ AGENT REACH INTELLIGENCE ENGINE — LIVE SCAN")
    print("=" * 60)
    digest = get_social_intelligence_digest()
    print(f"Timestamp : {digest['timestamp']}")
    print(f"Captured  : {digest['total_items_captured']} items across Reddit & News RSS")
    print("\n[r/CryptoCurrency Discussions]:")
    for idx, p in enumerate(digest['channels']['reddit_cryptocurrency'][:3], 1):
        print(f"  {idx}. {p['title']}")
    print("\n[Latest Crypto Headlines]:")
    for idx, n in enumerate(digest['channels']['crypto_news_rss'][:3], 1):
        print(f"  {idx}. {n['title']}")
    print("=" * 60)
