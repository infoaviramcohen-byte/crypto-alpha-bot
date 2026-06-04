#!/usr/bin/env python3
import requests, os, re
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
CHANNEL = "-1002481155935"
API = f"https://api.telegram.org/bot{TOKEN}"
FIRECRAWL_KEY = "fc-8246f55ac31b44328fc11ec606f4f73c"

def scrape_markets():
    r = requests.post("https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
        json={"url": "https://guardis.io", "formats": ["markdown"], "onlyMainContent": True, "waitFor": 2000},
        timeout=30
    )
    return r.json().get("data", {}).get("markdown", "")

def parse_markets(markdown):
    markets = []
    # Match question + volume pattern
    pattern = r'####\s+(.+\?)\s*\n+([0-9.]+)\s*SOL\s*24h\s*Vol'
    matches = re.findall(pattern, markdown)
    for question, vol in matches:
        markets.append({"question": question.strip(), "vol": float(vol)})
    # Sort by volume descending
    markets.sort(key=lambda x: x["vol"], reverse=True)
    return markets

def category_emoji(question):
    q = question.lower()
    if any(x in q for x in ["meme", "bonk", "fartcoin", "pengu", "pepe", "doge"]): return "🐸"
    if any(x in q for x in ["pump.fun", "letsbonk", "launchpad", "graduate"]): return "🚀"
    if any(x in q for x in ["ai agent", "artificial"]): return "🤖"
    if any(x in q for x in ["nft", "pudgy", "floor"]): return "🖼️"
    if any(x in q for x in ["sol", "solana"]): return "◎"
    if any(x in q for x in ["btc", "bitcoin"]): return "₿"
    if any(x in q for x in ["eth", "ethereum"]): return "⟠"
    return "⚡"

def send(text):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": CHANNEL,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    })

def run():
    markdown = scrape_markets()
    markets = parse_markets(markdown)

    if not markets:
        print("No markets found")
        return

    top = markets[:4]
    today = datetime.now(timezone.utc).strftime("%b %d")

    lines = []
    for i, m in enumerate(top):
        emoji = category_emoji(m["question"])
        vol = m["vol"]
        lines.append(f"{emoji} <b>{m['question']}</b>\n   💧 {vol} SOL volume\n")

    markets_text = "\n".join(lines)

    post = f"""🎯 <b>ATTENTION MARKETS — {today}</b>
<i>What is the market betting on today?</i>
━━━━━━━━━━━━━━

{markets_text}
💡 The narrative with most volume = where smart money attention is flowing right now.

━━━━━━━━━━━━━━
📡 <b>Crypto Alpha Feed</b> — @crypto_alphafeed"""

    send(post)
    print(f"Posted Attention Markets — {len(top)} markets")

if __name__ == "__main__":
    run()
