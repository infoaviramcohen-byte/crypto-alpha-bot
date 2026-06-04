#!/usr/bin/env python3
import feedparser, requests, sqlite3, os, re
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
    try:
        with open("/Users/aviram/tg-crypto-bot/.env") as f:
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    env[k] = v.strip('"')
    except:
        pass
    return env

ENV = load_env()
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or ENV.get("TELEGRAM_BOT_TOKEN", "")
CHANNEL = "-1003877748369"  # WC2026signals
API = f"https://api.telegram.org/bot{TOKEN}"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wc_news.db")

FEEDS = [
    "https://www.goal.com/feeds/en/news",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.skysports.com/rss/12040",
    "https://www.90min.com/feed.xml",
]

KEYWORDS = [
    "world cup", "wc2026", "wc26", "fifa", "2026", "usa", "canada", "mexico",
    "messi", "ronaldo", "mbappe", "haaland", "vinicius", "qualifying",
    "group stage", "knockout", "quarter", "semi", "final", "goal", "match",
    "transfer", "squad", "lineup", "injury", "coach", "manager", "bet", "odds", "predict"
]

TEAM_EMOJI = {
    "brazil": "🇧🇷", "argentina": "🇦🇷", "france": "🇫🇷", "england": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "spain": "🇪🇸", "germany": "🇩🇪", "portugal": "🇵🇹", "usa": "🇺🇸",
    "mexico": "🇲🇽", "canada": "🇨🇦", "morocco": "🇲🇦", "japan": "🇯🇵",
}

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
    conn.execute("INSERT OR IGNORE INTO posted (url, posted_at) VALUES (?,?)",
                 (url, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()

def is_relevant(title, summary=""):
    text = (title + " " + summary).lower()
    return any(k in text for k in KEYWORDS)

def extract_image(entry):
    if hasattr(entry, "media_content") and entry.media_content:
        url = entry.media_content[0].get("url", "")
        if url and url.startswith("http"): return url
    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        url = entry.media_thumbnail[0].get("url", "")
        if url and url.startswith("http"): return url
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if "image" in enc.get("type", "") or enc.get("url", "").endswith((".jpg", ".png", ".webp")):
                return enc.get("url", "")
    if hasattr(entry, "summary"):
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', entry.get("summary", ""))
        if match: return match.group(1)
    return None

def clean_text(text):
    text = re.sub(r"<[^>]+>", "", text or "").strip()
    return text[:280] + "..." if len(text) > 280 else text

def topic_emoji(title):
    t = title.lower()
    if any(x in t for x in ["goal", "score", "win", "beat"]): return "⚽"
    if any(x in t for x in ["injury", "injured", "out"]): return "🤕"
    if any(x in t for x in ["transfer", "sign", "deal"]): return "🤝"
    if any(x in t for x in ["predict", "odds", "bet", "tip"]): return "🎯"
    if any(x in t for x in ["lineup", "squad", "team"]): return "📋"
    if any(x in t for x in ["final", "semi", "quarter", "knockout"]): return "🏆"
    if any(x in t for x in ["world cup", "wc", "fifa"]): return "🌍"
    for team, emoji in TEAM_EMOJI.items():
        if team in t: return emoji
    return "⚽"

def format_post(entry, source):
    title = entry.get("title", "").strip()
    link = entry.get("link", "").strip()
    summary = clean_text(entry.get("summary", ""))
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    t_emoji = topic_emoji(title)

    return (
        f"{t_emoji} <b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"🔗 <a href='{link}'>Read full article</a>\n\n"
        f"🕐 {now}\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚽ <b>WC2026 Signals</b> — @WC2026signals"
    )

def send_with_image(image_url, caption):
    try:
        r = requests.post(f"{API}/sendPhoto", json={
            "chat_id": CHANNEL, "photo": image_url,
            "caption": caption, "parse_mode": "HTML"
        })
        if not r.json().get("ok"):
            send_text(caption)
    except:
        send_text(caption)

def send_text(text):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": CHANNEL, "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": False
    })

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
                    print(f"Posted {posted_count} WC news items.")
                    return
        except Exception as e:
            print(f"Error {feed_url}: {e}")

    print(f"Posted {posted_count} WC news items.")

if __name__ == "__main__":
    run()
