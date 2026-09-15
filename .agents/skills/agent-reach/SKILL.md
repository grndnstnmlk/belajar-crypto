---
name: agent-reach
description: Universal internet and social platform reach skill for AI agents powered by Agent Reach. Enables zero-API-cost reading, searching, and content extraction across Twitter/X, Reddit, Web (Jina Reader), YouTube, GitHub, Bilibili, XiaoHongShu, Instagram, Facebook, Xueqiu, Podcasts, and RSS. Use when the user wants to research social sentiment, scrape web content without paywalls, search social discussions, or extract transcripts and community insights.
---

# 👁️ Agent Reach Skill for Antigravity

Agent Reach gives the AI agent eyes to see and search across the entire internet and high-density social platforms without paid API subscriptions.

## 🚀 Quick Execution Guide

When executing reach commands, use `agent-reach` CLI or the upstream native tools:

### 1. Web & Article Reader (Jina Reader — Zero Config)
Extract clean markdown from any URL without paywalls or ads:
```bash
curl -s "https://r.jina.ai/<TARGET_URL>"
```
Or via Python:
```python
import requests
resp = requests.get("https://r.jina.ai/https://example.com/article", timeout=15)
clean_markdown = resp.text
```

### 2. Social Sentiment & Platform Channels

#### 🐦 Twitter / X Search & Reading
Read tweets, search queries, and monitor accounts:
```bash
# Search tweets
twitter-cli search "<QUERY>" --count 10
# View user timeline
twitter-cli user "<USERNAME>" --count 10
# Read specific tweet thread
twitter-cli tweet "<TWEET_ID>"
```

#### 📖 Reddit Threads & Sentiment
Scan subreddits and read deep community discussions:
```bash
# Read subreddit hot topics
rdt-cli sub <SUBREDDIT> --limit 10
# Read post details & comments
rdt-cli post <POST_ID_OR_URL>
```

#### 🔍 Neural Web Search (Exa via mcporter)
```bash
mcporter call exa.search '{"query": "<SEARCH_QUERY>", "numResults": 5}'
```

#### 📺 YouTube / Bilibili Video & Transcripts
```bash
# Get video subtitle / transcript
yt-dlp --write-auto-subs --sub-lang en,id --skip-download -o "%(id)s" "<YOUTUBE_URL>"
```

#### 💻 V2EX Community (Tech & Macro Discussions)
```bash
# Hot topics
curl -s "https://www.v2ex.com/api/topics/hot.json"
# Node topics
curl -s "https://www.v2ex.com/api/topics/show.json?node_name=<NODE>"
```

#### 🎙️ Audio / Podcast Transcription
```bash
agent-reach transcribe "<AUDIO_URL_OR_FILE>"
```

---

## 🩺 System Diagnostics & Configuration

Check active channels anytime:
```powershell
& "$env:APPDATA\Python\Python314\Scripts\agent-reach.exe" doctor
```

Configure channels with user cookies / tokens:
```powershell
# Interactive wizard
& "$env:APPDATA\Python\Python314\Scripts\agent-reach.exe" setup
```

---

## 📈 Crypto Sentiment Integration Workflow

When used for Crypto Market Intelligence & Alpha Hunting:
1. **Twitter/X Sentiment**: Search `$BTC`, `$ETH`, `$SOL`, liquidation cascades, regulatory updates.
2. **Reddit Sentiment**: Query `r/CryptoCurrency` and `r/Bitcoin` for retail sentiment polarity (Fear/Greed alignment).
3. **Macro Web Scrapes**: Fetch institutional reports (CoinShares, Glassnode, Fed statements) through Jina Reader.
4. **Feed Updates**: Output structured sentiment scores (-1.0 to +1.0) directly into `.agents/data/sentiment_narrative.json`.
