#!/usr/bin/env python3
import os, sqlite3, time, requests
from datetime import datetime

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or open("/Users/aviram/tg-crypto-bot/.env").read().strip().split("=",1)[1].strip('"')
API = f"https://api.telegram.org/bot{TOKEN}"
CHANNEL = "@crypto_alphafeed"
DB = "/Users/aviram/tg-crypto-bot/referrals.db"
GIVEAWAY_END = "2026-06-17"  # 2 weeks

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                referred_by INTEGER,
                joined_at TEXT
            );
            CREATE TABLE IF NOT EXISTS referrals (
                referrer_id INTEGER,
                referred_id INTEGER,
                joined_at TEXT,
                PRIMARY KEY (referrer_id, referred_id)
            );
        """)

def send(chat_id, text, parse_mode="HTML"):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    })

def get_ref_count(user_id):
    with db() as conn:
        row = conn.execute("SELECT COUNT(*) as c FROM referrals WHERE referrer_id=?", (user_id,)).fetchone()
        return row["c"]

def create_invite_link(user_id):
    r = requests.post(f"{API}/createChatInviteLink", json={
        "chat_id": CHANNEL,
        "name": str(user_id),
        "creates_join_request": False
    }).json()
    return r.get("result", {}).get("invite_link", "")

def handle_start(msg, payload):
    user_id = msg["from"]["id"]
    username = msg["from"].get("username", "")
    first_name = msg["from"].get("first_name", "")

    with db() as conn:
        existing = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()

        if not existing:
            invite_link = create_invite_link(user_id)
            conn.execute("""INSERT INTO users (user_id, username, first_name, referred_by, joined_at, invite_link)
                VALUES (?,?,?,NULL,?,?)""",
                (user_id, username, first_name, datetime.utcnow().isoformat(), invite_link))
        else:
            invite_link = existing["invite_link"] or create_invite_link(user_id)

    count = get_ref_count(user_id)

    send(user_id, f"""⚡ <b>Welcome to Crypto Alpha Feed Giveaway!</b>

🏆 <b>Prize: 50 USDT</b> to the top referrer
📅 Ends: {GIVEAWAY_END}

Your referral link:
<code>{invite_link}</code>

Share this link — every person who clicks it joins the <b>channel directly</b> and counts as your referral.

📊 Your referrals so far: <b>{count}</b>

Commands:
/top — Leaderboard
/mystats — Your stats""")

def handle_top(msg):
    user_id = msg["from"]["id"]
    with db() as conn:
        rows = conn.execute("""
            SELECT u.first_name, u.username, COUNT(r.referred_id) as cnt
            FROM referrals r
            JOIN users u ON u.user_id = r.referrer_id
            GROUP BY r.referrer_id
            ORDER BY cnt DESC
            LIMIT 10
        """).fetchall()

    if not rows:
        send(user_id, "No referrals yet — be the first! 🚀")
        return

    medals = ["🥇", "🥈", "🥉"] + ["🔹"] * 7
    lines = []
    for i, row in enumerate(rows):
        name = f"@{row['username']}" if row['username'] else row['first_name']
        lines.append(f"{medals[i]} {name} — {row['cnt']} referrals")

    send(user_id, f"""🏆 <b>GIVEAWAY LEADERBOARD</b>
Prize: 50 USDT | Ends: {GIVEAWAY_END}

{"".join(chr(10)+l for l in lines)}

Use /mystats to see your position.""")

def handle_mystats(msg):
    user_id = msg["from"]["id"]
    count = get_ref_count(user_id)
    ref_link = f"https://t.me/crypto_alphagroup_bot?start={user_id}"

    with db() as conn:
        rank_row = conn.execute("""
            SELECT COUNT(*) + 1 as rank FROM (
                SELECT referrer_id, COUNT(*) as cnt FROM referrals GROUP BY referrer_id
            ) WHERE cnt > (SELECT COUNT(*) FROM referrals WHERE referrer_id=?)
        """, (user_id,)).fetchone()

    rank = rank_row["rank"] if rank_row else 1

    send(user_id, f"""📊 <b>Your Stats</b>

Referrals: <b>{count}</b>
Rank: <b>#{rank}</b>
Ends: {GIVEAWAY_END}

Your link:
<code>{ref_link}</code>""")

def process_update(update):
    msg = update.get("message")
    if not msg or "text" not in msg:
        return

    text = msg["text"]
    if text.startswith("/start"):
        parts = text.split(" ", 1)
        payload = parts[1] if len(parts) > 1 else ""
        handle_start(msg, payload)
    elif text.startswith("/top"):
        handle_top(msg)
    elif text.startswith("/mystats"):
        handle_mystats(msg)

def run():
    init_db()
    offset = 0
    print("Referral bot running...")
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={
                "offset": offset,
                "timeout": 30,
                "allowed_updates": ["message"]
            }, timeout=35).json()

            for update in r.get("result", []):
                offset = update["update_id"] + 1
                process_update(update)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
