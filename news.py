#!/usr/bin/env python3
import feedparser, requests, sqlite3, os, re, json, random
import anthropic
from datetime import datetime, timezone

def load_env():
    env = {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return env
    try:
        with open(env_path) as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    env[k] = v.strip('"')
    except:
        pass
    return env
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
CHANNELS = ["-1002481155935", "-1001652015415"]  # Crypto Alpha Feed + Crypto News AI
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

# Generic hub/roundup pages these feeds publish with no real article content — skip them.
BLOCKLIST = [
    "what happened in crypto today",
    "need to know what happened in crypto",
    "here is the latest news on daily trends",
    "latest news on daily trends and events",
    "price analysis week ahead",
]

def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    if any(b in text for b in BLOCKLIST):
        return False
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

# Rotating CTA buttons — A/B test which hook drives the most clicks (tracked via utm_content in GA4).
CTA_BASE = "https://botarenasol.com/?utm_source=telegram&utm_medium=news_cta&utm_campaign=news_rotation&utm_content={content}#comparison"
CTAS = [
    ("🐋 Track Smart Money →", "cta_smartmoney"),
    ("💸 Trade with 35% Cashback →", "cta_cashback"),
    ("⚡ Don't Miss the Next Move →", "cta_fomo"),
    ("🤖 Compare Top Solana Bots →", "cta_compare"),
]
CHAN_LABEL = {"-1002481155935": "alphafeed", "-1001652015415": "cryptonewsai"}

def cta_markup(channel):
    """Pick a random CTA and return an inline-button keyboard with a tracked URL."""
    text, tag = random.choice(CTAS)
    url = CTA_BASE.format(content=f"{tag}_{CHAN_LABEL.get(str(channel), 'x')}")
    return {"inline_keyboard": [[{"text": text, "url": url}]]}

def send_text(text):
    for channel in CHANNELS:
        requests.post(f"{API}/sendMessage", json={
            "chat_id": channel,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
            "reply_markup": cta_markup(channel)
        })

def generate_fallback_image(title):
    try:
        from PIL import Image, ImageDraw, ImageFont
        import textwrap, tempfile

        w, h = 1280, 720
        img = Image.new('RGB', (w, h), (10, 10, 15))
        draw = ImageDraw.Draw(img)

        # Dark gradient overlay
        for y in range(h):
            alpha = int(15 + (y / h) * 20)
            draw.line([(0, y), (w, y)], fill=(10, alpha, 20))

        # Green accent bar
        draw.rectangle([0, 0, 6, h], fill=(20, 241, 149))

        # Grid lines
        for x in range(0, w, 80):
            draw.line([(x, 0), (x, h)], fill=(255, 255, 255, 8))
        for y in range(0, h, 80):
            draw.line([(0, y), (w, y)], fill=(255, 255, 255, 8))

        # Channel label
        try:
            font_big = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 52)
            font_med = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except:
            font_big = font_med = font_small = ImageFont.load_default()

        draw.text((40, 40), "CRYPTO ALPHA FEED", font=font_small, fill=(20, 241, 149))

        # Title wrapped
        wrapped = textwrap.wrap(title, width=38)[:4]
        y_text = 160
        for line in wrapped:
            draw.text((40, y_text), line, font=font_big, fill=(232, 232, 240))
            y_text += 70

        # Bottom bar
        draw.rectangle([0, h-60, w, h], fill=(15, 15, 25))
        draw.text((40, h-42), "@crypto_alphafeed  •  cryptoalpha.feed", font=font_small, fill=(107, 107, 128))

        # Save to temp file
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(tmp.name, 'PNG')
        return tmp.name
    except Exception as e:
        print(f"Image gen error: {e}")
        return None

def send_with_image(image_url, caption):
    for channel in CHANNELS:
        cap = caption
        markup = cta_markup(channel)
        try:
            if image_url and not image_url.startswith("http"):
                with open(image_url, 'rb') as f:
                    r = requests.post(f"{API}/sendPhoto",
                        data={"chat_id": channel, "caption": cap, "parse_mode": "HTML",
                              "reply_markup": json.dumps(markup)},
                        files={"photo": f}
                    )
            else:
                r = requests.post(f"{API}/sendPhoto", json={
                    "chat_id": channel, "photo": image_url,
                    "caption": cap, "parse_mode": "HTML", "reply_markup": markup
                })
            if not r.json().get("ok"):
                requests.post(f"{API}/sendMessage", json={
                    "chat_id": channel, "text": cap, "parse_mode": "HTML", "reply_markup": markup
                })
        except Exception as e:
            print(f"send_with_image error on {channel}: {e}")
    # Clean up local file once after sending to all channels
    if image_url and not image_url.startswith("http"):
        import os
        try: os.unlink(image_url)
        except: pass

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
        f"{t_emoji} <b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"Sentiment: {badge}\n\n"
        f"📡 <b>Crypto Alpha Feed</b> — @crypto_alphafeed"
    )
    return caption

# ---- Fallback "Market Pulse" for slow-news runs ----
PULSE_KEY = "__MARKET_PULSE__"
PULSE_MIN_GAP_HOURS = 6

def last_pulse_at():
    conn = sqlite3.connect(DB)
    row = conn.execute("SELECT posted_at FROM posted WHERE url=?", (PULSE_KEY,)).fetchone()
    conn.close()
    if not row:
        return None
    try:
        return datetime.fromisoformat(row[0])
    except Exception:
        return None

def mark_pulse():
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR REPLACE INTO posted (url, posted_at) VALUES (?,?)",
                 (PULSE_KEY, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def build_pulse():
    try:
        p = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,solana", "vs_currencies": "usd", "include_24hr_change": True},
            timeout=10
        ).json()
    except Exception:
        return None
    if not p.get("bitcoin"):
        return None

    try:
        fng = requests.get("https://api.alternative.me/fng/", timeout=10).json()["data"][0]
        fv, fc = fng["value"], fng["value_classification"]
    except Exception:
        fv, fc = "?", "?"
    fe = "😱" if (fv.isdigit() and int(fv) < 25) else "😨" if (fv.isdigit() and int(fv) < 45) \
        else "😐" if (fv.isdigit() and int(fv) < 55) else "😊" if (fv.isdigit() and int(fv) < 75) else "🤑"

    trend = ""
    try:
        coins = requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10).json().get("coins", [])[:5]
        syms = [f"${c['item']['symbol'].upper()}" for c in coins]
        if syms:
            trend = "🔥 <b>Trending:</b> " + ", ".join(syms) + "\n\n"
    except Exception:
        pass

    def row(name, key):
        d = p.get(key, {})
        val = d.get("usd", 0) or 0
        ch = d.get("usd_24h_change", 0) or 0
        vs = f"${val:,.0f}" if val >= 100 else f"${val:,.2f}"
        return f"{'📈' if ch >= 0 else '📉'} {name}: {vs} ({ch:+.1f}%)"

    today = datetime.now(timezone.utc).strftime("%b %d")
    return (
        f"📊 <b>MARKET PULSE — {today}</b>\n"
        f"<i>Quiet on the news front — here's where the market stands:</i>\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"{row('BTC','bitcoin')}\n"
        f"{row('ETH','ethereum')}\n"
        f"{row('SOL','solana')}\n\n"
        f"{fe} <b>Fear &amp; Greed:</b> {fv}/100 — {fc}\n\n"
        f"{trend}"
        f"📡 <b>Crypto Alpha Feed</b> — @crypto_alphafeed"
    )

def post_fallback():
    last = last_pulse_at()
    if last:
        hrs = (datetime.now(timezone.utc) - last).total_seconds() / 3600
        if hrs < PULSE_MIN_GAP_HOURS:
            print(f"No news; last Market Pulse {hrs:.1f}h ago (< {PULSE_MIN_GAP_HOURS}h) — posting nothing.")
            return False
    pulse = build_pulse()
    if not pulse:
        print("No news and pulse data unavailable — posting nothing.")
        return False
    send_text(pulse)
    mark_pulse()
    print("No fresh news — posted Market Pulse fallback.")
    return True

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
                if not image:
                    image = generate_fallback_image(title)

                caption = format_post(entry, source)
                if image:
                    send_with_image(image, caption)
                else:
                    send_text(caption)
                mark_posted(link)
                posted_count += 1

                if posted_count >= 1:
                    print(f"Posted {posted_count} news items.")
                    return

        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")

    if posted_count == 0:
        # No fresh news this run — post a Market Pulse instead, or stay quiet.
        post_fallback()
    else:
        print(f"Posted {posted_count} news items.")

if __name__ == "__main__":
    run()
