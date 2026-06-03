#!/usr/bin/env python3
import feedparser, requests, sqlite3, os, re
import anthropic
from datetime import datetime, timezone

def load_env():
    env = {}
    with open("/Users/aviram/tg-crypto-bot/.env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k] = v.strip('"')
    return env

ENV = load_env()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or ENV.get("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY") or ENV.get("ANTHROPIC_API_KEY", "")
CHANNEL = "-1002481155935"
API = f"https://api.telegram.org/bot{TOKEN}"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "news.db")

FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://theblock.co/rss.xml",
]

KEYWORDS = [
    "bitcoin", "ethereum", "solana", "defi", "web3", "crypto", "nft",
    "blockchain", "altcoin", "token", "airdrop", "dex", "layer2", "btc", "eth"
]

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("CREATE TABLE IF NOT EXISTS posted (url TEXT PRIMARY KEY, posted_at TEXT)")
    conn.commit()
    conn.close()

def already_posted(url):
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT 1 FROM posted WHERE url=?", (url,)).fetchone()
    conn.close()
    return row is not None

def mark_posted(url):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR IGNORE INTO posted (url, posted_at) VALUES (?,?)", (url, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    return any(k in text for k in KEYWORDS)

def extract_image(entry):
    # Try media_content
    if hasattr(entry, "media_content") and entry.media_content:
        url = entry.media_content[0].get("url", "")
        if url and url.startswith("http"):
            return url
    # Try media_thumbnail
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get("url", "")
        if url and url.startswith("http"):
            return url
    # Try enclosures
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if "image" in enc.get("type", "") or enc.get("url", "").endswith((".jpg", ".png", ".webp")):
                return enc.get("url", "")
    # Try extracting img from summary HTML
    if hasattr(entry, "summary"):
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry.get("summary", ""))
        if match:
            return match.group(1)
    return None

def clean_summary(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    text = text.strip()
    return text[:600] + "..." if len(text) > 600 else text

def ai_summary_and_sentiment(title, raw_summary):
    if not ANTHROPIC_KEY or ANTHROPIC_KEY == "your_key_here":
        return clean_summary(raw_summary)[:280], sentiment_from_keywords(title + " " + raw_summary)
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{
                "role": "user",
                "content": (
                    f"You are a crypto alpha channel writer. Given this news:\n"
                    f"Title: {title}\nSummary: {raw_summary[:500]}\n\n"
                    f"Write exactly 2 punchy lines (max 180 chars total) that a crypto trader would find valuable. "
                    f"No fluff. Then on a new line write only one word: BULLISH, BEARISH, or NEUTRAL."
                )
            }]
        )
        lines = msg.content[0].text.strip().split("\n")
        sentiment_word = lines[-1].strip().upper()
        summary = "\n".join(lines[:-1]).strip()
        if sentiment_word not in ("BULLISH", "BEARISH", "NEUTRAL"):
            sentiment_word = sentiment_from_keywords(title)
        return summary, sentiment_word
    except Exception as e:
        print(f"AI error: {e}")
        return clean_summary(raw_summary)[:280], sentiment_from_keywords(title + " " + raw_summary)

def sentiment_from_keywords(text):
    t = text.lower()
    bullish = ["surge", "rally", "pump", "ath", "bull", "launch", "adoption", "gain", "up", "rise", "partnership", "listing"]
    bearish = ["crash", "drop", "fall", "bear", "hack", "exploit", "ban", "sec", "dump", "loss", "down", "scam", "breach"]
    b_score = sum(1 for w in bullish if w in t)
    r_score = sum(1 for w in bearish if w in t)
    if b_score > r_score: return "BULLISH"
    if r_score > b_score: return "BEARISH"
    return "NEUTRAL"

def sentiment_badge(sentiment):
    return {"BULLISH": "🟢 Bullish", "BEARISH": "🔴 Bearish", "NEUTRAL": "⚪ Neutral"}.get(sentiment, "⚪ Neutral")

def send_text(text):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    })

def send_with_image(image_url, caption):
    try:
        r = requests.post(f"{API}/sendPhoto", json={
            "chat_id": CHANNEL,
            "photo": image_url,
            "caption": caption,
            "parse_mode": "HTML"
        })
        if not r.json().get("ok"):
            send_text(caption)
    except:
        send_text(caption)

SOURCE_EMOJI = {
    "cointelegraph": "🟡",
    "coindesk": "🔵",
    "decrypt": "🟣",
    "block": "⚫",
}

def source_emoji(source):
    for key, emoji in SOURCE_EMOJI.items():
        if key in source.lower():
            return emoji
    return "📡"

def topic_emoji(title):
    t = title.lower()
    if any(x in t for x in ["bitcoin", "btc"]): return "₿"
    if any(x in t for x in ["ethereum", "eth"]): return "⟠"
    if any(x in t for x in ["solana", "sol"]): return "◎"
    if any(x in t for x in ["hack", "exploit", "breach", "scam"]): return "🚨"
    if any(x in t for x in ["sec", "regulation", "legal", "ban"]): return "⚖️"
    if any(x in t for x in ["airdrop"]): return "🪂"
    if any(x in t for x in ["nft"]): return "🖼️"
    if any(x in t for x in ["defi"]): return "🏦"
    if any(x in t for x in ["launch", "listing", "new"]): return "🚀"
    if any(x in t for x in ["pump", "surge", "ath", "rally", "bull"]): return "📈"
    if any(x in t for x in ["crash", "drop", "fall", "bear", "dump"]): return "📉"
    return "⚡"

def format_post(entry, source):
    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    raw = clean_summary(entry.get("summary", ""))
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    t_emoji = topic_emoji(title)
    s_emoji = source_emoji(source)

    summary, sentiment = ai_summary_and_sentiment(title, raw)
    badge = sentiment_badge(sentiment)

    caption = (
        f"{t_emoji} <b>{title}</b>\n"
        f"{'─' * 28}\n"
        f"{summary}\n\n"
        f"Sentiment: {badge}\n\n"
        f"🔗 <a href='{link}'>Read full article</a>\n\n"
        f"{s_emoji} {source}  •  🕐 {now}\n"
        f"━━━━━━━━━━━━━━\n"
        f"📡 <b>Crypto Alpha Feed</b> — @crypto_alphafeed"
    )
    return caption

def run():
    init_db()
    posted_count = 0

    for feed_url in FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source = feed.feed.get("title", feed_url)

            for entry in feed.entries[:10]:
                link = entry.get("link", "")
                title = entry.get("title", "")

                if not link or already_posted(link):
                    continue

                if not is_relevant(title, entry.get("summary", "")):
                    continue

                image = extract_image(entry)
                caption = format_post(entry, source)

                if image:
                    send_with_image(image, caption)
                else:
                    send_text(caption)

                mark_posted(link)
                posted_count += 1

                if posted_count >= 2:
                    print(f"Posted {posted_count} news items.")
                    return

        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")

    print(f"Posted {posted_count} news items.")

if __name__ == "__main__":
    run()
