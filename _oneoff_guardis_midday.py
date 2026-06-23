#!/usr/bin/env python3
"""One-off: repost the Guardis cashback ad at midday (13:00 local) today."""
import time, json, requests
import datetime as dt

def tok():
    for line in open("/Users/aviram/tg-crypto-bot/.env"):
        if line.startswith("TELEGRAM_BOT_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"')

TOKEN = tok()
API = f"https://api.telegram.org/bot{TOKEN}"
CHANNEL = "-1002481155935"
IMG = "/Users/aviram/Downloads/magnific_the-button-should-be-arro_8vA7EEcIrU.png"
CAP = ("Most platforms keep your fees. Guardis gives you 35% back 💰 — on every single trade.\n\n"
       "➡️ 10,000+ smart wallets tracked live\n"
       "➡️ One-click copy trading\n"
       "➡️ MEV-protected fills\n\n"
       "Exclusive offer · limited time 📥\n"
       "📡 @crypto_alphafeed")
KB = {"inline_keyboard": [[{"text": "💸 Claim 35% Cashback →",
                            "url": "https://guardis.io/?ref=652C9829"}]]}

# Wait until 13:00 local today
target = dt.datetime.now().replace(hour=13, minute=0, second=0, microsecond=0)
now = dt.datetime.now()
if target > now:
    time.sleep((target - now).total_seconds())

with open(IMG, "rb") as f:
    r = requests.post(f"{API}/sendPhoto",
                      data={"chat_id": CHANNEL, "caption": CAP, "parse_mode": "HTML",
                            "reply_markup": json.dumps(KB)},
                      files={"photo": f})
j = r.json()
print(dt.datetime.now().isoformat(), "OK" if j.get("ok") else "ERR",
      j.get("result", {}).get("message_id") if j.get("ok") else j)
