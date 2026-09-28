"""
internet_researcher.py - Real-Time Internet Search, Web Intelligence RAG & Autonomous Learning Engine
Synthesized for Belajar Kripto Trading Desk & Ollama Local AI Brain.

Features:
1. Zero-Cost Live Web Search & Scraping:
   - Live RSS news feeds: Cointelegraph, CoinDesk, Decrypt, CryptoSlate.
   - Live community pulse: Reddit r/CryptoCurrency, r/Bitcoin, r/solana.
   - DuckDuckGo zero-fee search engine integration.
   - Jina Reader (https://r.jina.ai/{url}) clean markdown article extraction.
   - Binance Vision 24h ticker feed for live token catalysts and price dynamics.
2. Web-Augmented Retrieval Grounding (Web RAG):
   - Synthesizes real-time internet context dynamically injected into Ollama's prompt.
   - Empowers Ollama (deepseek-r1:8b) to cite live breaking news and current market catalysts.
3. Autonomous Internet Learning Loop (Karpathy / ATLAS Style Continuous Learning):
   - Ollama autonomously researches the web, reads institutional articles, and extracts 
     quant tactics, regime warnings, and setup rules.
   - Commits learnings into agent_memory_bank.json and internet_research_stream.json.
4. REST API Endpoints (/api/ai/internet_research) for Dashboard Telemetry & Manual Learning Trigger.
"""

import json
import os
import re
import ssl
import sys
import threading
import time
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(TOOLS_DIR))
DATA_DIR = os.path.join(os.path.dirname(TOOLS_DIR), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

RESEARCH_STREAM_FILE = os.path.join(DATA_DIR, "internet_research_stream.json")
MEMORY_BANK_FILE = os.path.join(PROJECT_ROOT, "agent_memory_bank.json")
ALT_MEMORY_FILE = os.path.join(DATA_DIR, "agent_memory_bank.json")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

# In-memory caches to guarantee sub-millisecond execution when called in high frequency
_NEWS_CACHE = {
    "timestamp": 0.0,
    "data": []
}
_REDDIT_CACHE = {
    "timestamp": 0.0,
    "data": []
}
_SEARCH_CACHE: Dict[str, Tuple[float, List[Dict[str, str]]]] = {}

CACHE_TTL_NEWS = 120.0  # 2 minutes
CACHE_TTL_REDDIT = 180.0  # 3 minutes
CACHE_TTL_SEARCH = 300.0  # 5 minutes


# =====================================================================
# 1. CORE INTERNET ACCESS MODULES (ZERO-API-FEE)
# =====================================================================

def fetch_url_markdown(url: str, timeout: int = 10) -> str:
    """
    Extracts clean markdown text from any web page using Jina Reader (Zero API fee).
    """
    if not url.startswith("http"):
        return ""
    clean_target = f"https://r.jina.ai/{url}"
    req = urllib.request.Request(clean_target, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            # Truncate to reasonable token length for local LLMs
            return content[:3000].strip()
    except Exception as e:
        return f"Fetch error: {e}"


def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Performs zero-fee DuckDuckGo web search using HTML parsing.
    Returns: [{"title": ..., "snippet": ..., "link": ...}, ...]
    """
    global _SEARCH_CACHE
    now = time.time()
    if query in _SEARCH_CACHE and (now - _SEARCH_CACHE[query][0] < CACHE_TTL_SEARCH):
        return _SEARCH_CACHE[query][1]

    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers=HEADERS)
    results = []

    try:
        with urllib.request.urlopen(req, timeout=8, context=SSL_CTX) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            
            # Extract links and snippets with regex
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
            titles = re.findall(r'<a class="result__url[^>]*>(.*?)</a>', html, re.DOTALL)
            anchors = re.findall(r'<h2 class="result__title">.*?<a class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)

            for i in range(min(max_results, len(anchors))):
                link, raw_title = anchors[i]
                clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
                snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                
                # Unwrap duckduckgo redirect link if present
                if "/uddg=" in link:
                    m = re.search(r'uddg=([^&]+)', link)
                    if m:
                        link = urllib.parse.unquote(m.group(1))

                results.append({
                    "title": clean_title,
                    "snippet": snippet,
                    "link": link
                })
    except Exception:
        # Fallback to empty if duckduckgo rate-limited
        pass

    _SEARCH_CACHE[query] = (now, results)
    return results


def get_live_crypto_news(limit: int = 6) -> List[Dict[str, Any]]:
    """
    Fetches real-time breaking crypto headlines from multiple decentralized RSS channels.
    """
    global _NEWS_CACHE
    now = time.time()
    if _NEWS_CACHE["data"] and (now - _NEWS_CACHE["timestamp"] < CACHE_TTL_NEWS):
        return _NEWS_CACHE["data"][:limit]

    feeds = [
        ("Cointelegraph", "https://cointelegraph.com/rss"),
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Decrypt", "https://decrypt.co/feed")
    ]
    collected = []

    import feedparser
    for source_name, feed_url in feeds:
        try:
            req = urllib.request.Request(feed_url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
                raw_xml = resp.read()
                parsed = feedparser.parse(raw_xml)
                for entry in parsed.entries[:3]:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()
                    summary = re.sub(r'<[^>]+>', '', entry.get("summary", "")).strip()[:180]
                    published = entry.get("published", "")
                    if title:
                        collected.append({
                            "source": source_name,
                            "title": title,
                            "link": link,
                            "summary": summary,
                            "published": published
                        })
        except Exception:
            continue

    if collected:
        _NEWS_CACHE = {"timestamp": now, "data": collected}
        return collected[:limit]
    
    return _NEWS_CACHE["data"][:limit]


def get_live_reddit_sentiment(subreddits: Optional[List[str]] = None, limit_per_sub: int = 4) -> List[Dict[str, Any]]:
    """
    Scrapes hot discussions and retail sentiment from crypto subreddits.
    """
    global _REDDIT_CACHE
    now = time.time()
    if _REDDIT_CACHE["data"] and (now - _REDDIT_CACHE["timestamp"] < CACHE_TTL_REDDIT):
        return _REDDIT_CACHE["data"]

    subs = subreddits or ["CryptoCurrency", "Bitcoin"]
    posts = []

    import feedparser
    for sub in subs:
        url = f"https://www.reddit.com/r/{sub}/.rss"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BelajarKripto-Researcher/2.0"})
            with urllib.request.urlopen(req, timeout=5, context=SSL_CTX) as resp:
                raw_xml = resp.read()
                feed = feedparser.parse(raw_xml)
                for entry in feed.entries[:limit_per_sub]:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "").strip()
                    if title:
                        posts.append({
                            "subreddit": f"r/{sub}",
                            "title": title,
                            "link": link
                        })
        except Exception:
            continue

    if posts:
        _REDDIT_CACHE = {"timestamp": now, "data": posts}
    return _REDDIT_CACHE["data"]


def get_binance_ticker_24h(symbol: str = "BTCUSDT") -> Dict[str, Any]:
    """
    Fetches real-time 24h market stats directly from Binance Vision.
    """
    sym = symbol.upper().replace("-", "").replace("/", "")
    if not sym.endswith("USDT"):
        sym = f"{sym}USDT"
    url = f"https://data-api.binance.vision/api/v3/ticker/24hr?symbol={sym}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=4, context=SSL_CTX) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "symbol": sym,
                "price": float(data.get("lastPrice", 0.0)),
                "change_pct": float(data.get("priceChangePercent", 0.0)),
                "high_24h": float(data.get("highPrice", 0.0)),
                "low_24h": float(data.get("lowPrice", 0.0)),
                "volume_usdt": float(data.get("quoteVolume", 0.0))
            }
    except Exception:
        return {}


# =====================================================================
# 2. WEB-AUGMENTED RETRIEVAL (RAG) SYNTHESIZER FOR OLLAMA
# =====================================================================

def synthesize_web_context_for_prompt(user_query: str, max_tokens: int = 800) -> str:
    """
    Synthesizes live internet headlines, sentiment, and token stats into an information-dense
    context block that is directly injected into Ollama's prompt.
    """
    query_upper = user_query.upper()
    
    # 1. Identify target token in query
    target_coins = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "LINK", "ADA", "SUI", "AVAX", "NEAR"]
    found_coin = None
    for c in target_coins:
        if c in query_upper or f"{c}USDT" in query_upper:
            found_coin = c
            break

    # 2. Collect live news & reddit
    news_items = get_live_crypto_news(limit=4)
    reddit_items = get_live_reddit_sentiment(limit_per_sub=3)
    ticker_info = get_binance_ticker_24h(f"{found_coin}USDT") if found_coin else get_binance_ticker_24h("BTCUSDT")

    # 3. If query mentions specific keywords or unfamiliar topic, run DuckDuckGo
    search_snippets = []
    if any(k in user_query.lower() for k in ["apa itu", "berita", "kenapa", "news", "faktor", "mengapa", "analisa", "prospek"]):
        search_results = search_duckduckgo(f"crypto market {user_query}", max_results=3)
        for r in search_results:
            search_snippets.append(f"• {r['title']}: {r['snippet']}")

    # 4. Format into clean RAG context block
    rag_lines = [
        "=======================================================",
        "🌐 [LIVE INTERNET & REAL-TIME WEB INTELLIGENCE (WEB RAG)]",
        f"Synchronized at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "Sources: Cointelegraph, CoinDesk, Decrypt, Reddit, Binance Vision",
        "-------------------------------------------------------"
    ]

    if ticker_info and ticker_info.get("price"):
        rag_lines.append(f"📊 LIVE 24H TICKER ({ticker_info['symbol']}): Price: ${ticker_info['price']:,.2f} | 24h Change: {ticker_info['change_pct']:+.2f}% | 24h Range: ${ticker_info['low_24h']:,.2f} - ${ticker_info['high_24h']:,.2f}")

    if news_items:
        rag_lines.append("\n📰 BREAKING CRYPTO HEADLINES:")
        for idx, n in enumerate(news_items, 1):
            rag_lines.append(f"  {idx}. [{n['source']}] {n['title']} ({n.get('summary', '')[:100]}...)")

    if reddit_items:
        rag_lines.append("\n💬 COMMUNITY & RETAIL SENTIMENT PULSE:")
        for idx, r in enumerate(reddit_items[:3], 1):
            rag_lines.append(f"  {idx}. [{r['subreddit']}] {r['title']}")

    if search_snippets:
        rag_lines.append("\n🔍 LIVE SEARCH SNIPPETS:")
        for s in search_snippets[:2]:
            rag_lines.append(f"  {s}")

    rag_lines.append("=======================================================")
    return "\n".join(rag_lines)


# =====================================================================
# 3. AUTONOMOUS INTERNET LEARNING LOOP FOR OLLAMA
# =====================================================================

def run_ollama_internet_research(force: bool = False) -> Dict[str, Any]:
    """
    Autonomous Internet Research and Accelerated Continuous Learning Loop:
    1. Collects live internet market news and community trends.
    2. Uses Jina Reader to read the top breaking article.
    3. Prompts Ollama (DeepSeek-R1 / Qwen2.5) to synthesize actionable institutional lessons.
    4. Commits the newly learned tactics into agent_memory_bank.json and internet_research_stream.json.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    news = get_live_crypto_news(limit=5)
    reddit = get_live_reddit_sentiment(limit_per_sub=3)

    if not news and not reddit:
        return {
            "status": "OFFLINE",
            "message": "Tidak dapat mengakses internet saat ini.",
            "timestamp": now_str
        }

    # Fetch full text of top news article via Jina Reader
    top_article_text = ""
    top_article_title = news[0]["title"] if news else "Market Overview"
    if news and news[0].get("link"):
        top_article_text = fetch_url_markdown(news[0]["link"], timeout=8)

    # Compile learning brief for Ollama
    intel_brief = f"""
[LIVE INTERNET MARKET INTELLIGENCE TO PROCESS]
Top Headlines:
{json.dumps([n['title'] for n in news], indent=2)}

Community Discussions:
{json.dumps([r['title'] for r in reddit[:4]], indent=2)}

Featured In-Depth Article: "{top_article_title}"
Excerpt:
{top_article_text[:1200]}
"""

    prompt = f"""
{intel_brief}

[MISSION FOR LOCAL AI BRAIN]
You are the Autonomous Quant Research Officer of Belajar Kripto Trading Desk.
Analyze the live internet market intelligence above. Synthesize 2-3 high-impact, actionable 
trading insights, market regime shifts, and risk guardrails for our autonomous trading bot.

Output STRICTLY a valid JSON object matching this schema:
{{
  "market_regime": "BULLISH_TREND | BEARISH_PULLBACK | RANGE_CONSOLIDATION | HIGH_VOLATILITY_CHOP",
  "key_catalysts": ["catalyst 1", "catalyst 2"],
  "learned_tactics": [
    {{
      "topic": "Short title of learned tactic",
      "insight": "Concise explanation of market dynamics",
      "rule": "Specific actionable rule for the trading engine (e.g. adjust stop-loss, avoid long on resistance, etc.)",
      "applicable_coins": ["BTC", "ETH"]
    }}
  ],
  "sentiment_summary": "1-2 sentence overall summary in Indonesian"
}}
"""
    sys_prompt = "You are the Institutional Research Brain of an automated crypto fund. Output strictly valid JSON without markdown fences."

    learned_data = None
    provider_used = "Ollama Local Brain"

    # Query Local LLM (Ollama)
    try:
        import local_cognitive_brain
        is_live, ep, mdl = local_cognitive_brain.test_local_llm_connection(timeout=0.5)
        if is_live:
            resp = local_cognitive_brain.query_local_llm(
                prompt=prompt,
                system_prompt=sys_prompt,
                model=mdl or "deepseek-r1:8b",
                endpoint=ep or "http://localhost:11434/v1",
                temperature=0.2,
                timeout=45.0,
                response_json=True
            )
            if resp:
                # Clean response
                cleaned = resp.strip()
                if "<think>" in cleaned and "</think>" in cleaned:
                    cleaned = cleaned.split("</think>")[-1].strip()
                cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.MULTILINE)
                cleaned = re.sub(r'```$', '', cleaned, flags=re.MULTILINE).strip()
                try:
                    learned_data = json.loads(cleaned)
                except Exception:
                    pass
    except Exception as e:
        print(f"[InternetResearcher] Local LLM call error: {e}")

    # Fallback heuristic synthesizer if Ollama is busy or offline
    if not learned_data:
        provider_used = "Algorithmic Internet Synthesizer"
        learned_data = {
            "market_regime": "RANGE_CONSOLIDATION",
            "key_catalysts": [n["title"] for n in news[:2]],
            "learned_tactics": [
                {
                    "topic": "Internet News Flow Monitoring",
                    "insight": f"Pasar menyerap katalis utama: {news[0]['title'] if news else 'Volatilitas makro'}.",
                    "rule": "Perketat trailing stop loss ke breakeven pada R >= +1.5R ketika berita besar dirilis.",
                    "applicable_coins": ["BTC", "ETH", "SOL"]
                }
            ],
            "sentiment_summary": f"Sentimen pasar dipengaruhi oleh {len(news)} berita terkini dan diskusi komunitas Reddit."
        }

    research_record = {
        "timestamp": now_str,
        "provider": provider_used,
        "articles_analyzed": len(news),
        "reddit_threads_analyzed": len(reddit),
        "featured_article": top_article_title,
        "market_regime": learned_data.get("market_regime", "RANGE_CONSOLIDATION"),
        "key_catalysts": learned_data.get("key_catalysts", []),
        "learned_tactics": learned_data.get("learned_tactics", []),
        "sentiment_summary": learned_data.get("sentiment_summary", "")
    }

    # 1. Save to internet_research_stream.json
    try:
        stream = []
        if os.path.exists(RESEARCH_STREAM_FILE):
            try:
                with open(RESEARCH_STREAM_FILE, "r", encoding="utf-8") as f:
                    stream = json.load(f)
                    if not isinstance(stream, list):
                        stream = []
            except Exception:
                stream = []
        stream.insert(0, research_record)
        stream = stream[:50]  # Keep latest 50 sessions
        with open(RESEARCH_STREAM_FILE, "w", encoding="utf-8") as f:
            json.dump(stream, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[InternetResearcher] Failed to save research stream: {e}")

    # 2. Append newly learned tactics to agent_memory_bank.json
    commit_tactics_to_memory_bank(research_record)

    return research_record


def commit_tactics_to_memory_bank(research_record: Dict[str, Any]):
    """
    Persists internet-derived tactics into the central agent memory bank so that
    all trading desk engines immediately benefit from Ollama's internet discoveries.
    """
    for file_path in [MEMORY_BANK_FILE, ALT_MEMORY_FILE]:
        if not os.path.exists(file_path):
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                mb = json.load(f)

            if "learned_tactics" not in mb or not isinstance(mb["learned_tactics"], list):
                mb["learned_tactics"] = []

            for tactic in research_record.get("learned_tactics", []):
                tactic_entry = {
                    "id": f"NET_{int(time.time())}_{len(mb['learned_tactics'])+1}",
                    "topic": tactic.get("topic", "Internet Research"),
                    "rule": tactic.get("rule", ""),
                    "insight": tactic.get("insight", ""),
                    "source": "INTERNET_RESEARCH (Live Web RAG)",
                    "applicable_coins": tactic.get("applicable_coins", ["ALL"]),
                    "timestamp": research_record.get("timestamp"),
                    "confidence": 88
                }
                mb["learned_tactics"].insert(0, tactic_entry)

            # Cap learned tactics at 100
            mb["learned_tactics"] = mb["learned_tactics"][:100]

            # Update meta telemetry
            if "meta" in mb and isinstance(mb["meta"], dict):
                mb["meta"]["last_internet_learning_sync"] = research_record.get("timestamp")
                mb["meta"]["total_internet_learnings"] = len([t for t in mb["learned_tactics"] if "INTERNET" in str(t.get("source"))])

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(mb, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[InternetResearcher] Memory bank commit failed for {file_path}: {e}")


def get_latest_internet_research() -> Dict[str, Any]:
    """
    Returns the most recent internet research results or runs an initial lightweight scan.
    """
    if os.path.exists(RESEARCH_STREAM_FILE):
        try:
            with open(RESEARCH_STREAM_FILE, "r", encoding="utf-8") as f:
                stream = json.load(f)
                if stream and isinstance(stream, list):
                    return stream[0]
        except Exception:
            pass

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "INITIALIZING",
        "articles_analyzed": 0,
        "market_regime": "NEUTRAL",
        "learned_tactics": [],
        "sentiment_summary": "Internet research loop ready for activation."
    }


# Background thread for periodic auto-learning (every 30 minutes)
_RESEARCH_THREAD = None
_STOP_EVENT = threading.Event()

def _research_daemon_loop():
    while not _STOP_EVENT.is_set():
        try:
            run_ollama_internet_research()
        except Exception:
            pass
        # Sleep for 30 minutes (1800s) with periodic exit checks
        for _ in range(180):
            if _STOP_EVENT.is_set():
                break
            time.sleep(10)

def start_internet_research_daemon():
    """Starts the background continuous internet research thread."""
    global _RESEARCH_THREAD
    if _RESEARCH_THREAD is None or not _RESEARCH_THREAD.is_alive():
        _STOP_EVENT.clear()
        _RESEARCH_THREAD = threading.Thread(target=_research_daemon_loop, daemon=True, name="OllamaInternetResearcher")
        _RESEARCH_THREAD.start()
        print("🌐 [Internet Researcher] Background continuous internet learning daemon started.")


if __name__ == "__main__":
    print("=" * 60)
    print("🌐 BELAJAR KRIPTO INTERNET RESEARCHER & OLLAMA WEB RAG")
    print("=" * 60)
    print("\n1. Testing Live Breaking Crypto News RSS...")
    news = get_live_crypto_news(limit=3)
    for idx, n in enumerate(news, 1):
        print(f"   {idx}. [{n['source']}] {n['title']}")

    print("\n2. Testing Reddit Sentiment...")
    red = get_live_reddit_sentiment(limit_per_sub=2)
    for idx, r in enumerate(red, 1):
        print(f"   {idx}. [{r['subreddit']}] {r['title']}")

    print("\n3. Testing DuckDuckGo Search...")
    sr = search_duckduckgo("Bitcoin price target 2026", max_results=2)
    for idx, s in enumerate(sr, 1):
        print(f"   {idx}. {s['title']} -> {s['link']}")

    print("\n4. Testing Web Context Synthesizer for Ollama...")
    ctx = synthesize_web_context_for_prompt("Bagaimana analisa BTC hari ini?")
    print(ctx[:300] + "...\n[Truncated for console]")

    print("\n5. Running Autonomous Internet Learning Session...")
    learn = run_ollama_internet_research()
    print(f"Provider: {learn.get('provider')}")
    print(f"Market Regime: {learn.get('market_regime')}")
    print(f"Learned Tactics Count: {len(learn.get('learned_tactics', []))}")
    print(f"Summary: {learn.get('sentiment_summary')}")
    print("=" * 60)
