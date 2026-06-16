#!/usr/bin/env python3
"""Smart Money Pros bot — a 'find your Solana bot' quiz funnel that recommends
Guardis, links to botarenasol, and logs every user (a DM-able list)."""
import requests, time, csv, os, datetime

def env(k, default=""):
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(p):
        for line in open(p):
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get(k, default)

TOKEN = env("SMARTMONEY_BOT_TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"
USERS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot_users.csv")
GUARDIS = "https://guardis.io/?ref=652C9829"
SITE = "https://botarenasol.com/?utm_source=telegram&utm_medium=bot&utm_campaign=smartmoney_bot"

def log_user(u):
    uid = str(u.get("id"))
    seen = set()
    if os.path.exists(USERS_CSV):
        for row in csv.reader(open(USERS_CSV)):
            if row: seen.add(row[0])
    if uid in seen:
        return
    new = not os.path.exists(USERS_CSV)
    with open(USERS_CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["id", "username", "first_name", "first_seen"])
        w.writerow([uid, u.get("username", ""), u.get("first_name", ""),
                    datetime.datetime.now(datetime.timezone.utc).isoformat()])

def kb(rows):
    return {"inline_keyboard": rows}

def send(chat_id, text, markup=None):
    import json
    d = {"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}
    if markup: d["reply_markup"] = json.dumps(markup)
    j = requests.post(f"{API}/sendMessage", data=d, timeout=20).json()
    if not j.get("ok"): print("SEND FAIL:", j.get("description"), flush=True)
    return j

def edit(chat_id, mid, text, markup=None):
    import json
    d = {"chat_id": chat_id, "message_id": mid, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}
    if markup: d["reply_markup"] = json.dumps(markup)
    j = requests.post(f"{API}/editMessageText", data=d, timeout=20).json()
    if not j.get("ok"): print("EDIT FAIL:", j.get("description"), flush=True)
    return j

def answer_cb(cb_id):
    requests.post(f"{API}/answerCallbackQuery", data={"callback_query_id": cb_id}, timeout=20)

WELCOME = ("👋 <b>Welcome to Smart Money Pros</b>\n\n"
           "Stop trading on hype. I'll match you with the best Solana trading tool for your style — "
           "in 20 seconds. 🐋\n\nReady?")

def handle_start(chat_id, user):
    log_user(user)
    send(chat_id, WELCOME, kb([[{"text": "🚀 Find my bot", "callback_data": "q1"}]]))

STEPS = {
    "q1": ("<b>1/3 · How would you describe yourself?</b>",
           [[{"text": "🐣 Newer trader", "callback_data": "q2"}],
            [{"text": "🔥 Experienced", "callback_data": "q2"}]]),
    "q2": ("<b>2/3 · What do you mostly trade?</b>",
           [[{"text": "🚀 Memecoins", "callback_data": "q3"}],
            [{"text": "📊 Majors (BTC/ETH/SOL)", "callback_data": "q3"}]]),
    "q3": ("<b>3/3 · What matters most to you?</b>",
           [[{"text": "💸 Lower fees", "callback_data": "res"}],
            [{"text": "⚡ Speed", "callback_data": "res"}],
            [{"text": "🛡️ Safety", "callback_data": "res"}]]),
}

RESULT = ("🥇 <b>Your match: Guardis</b>\n\n"
          "Based on your answers, Guardis is your best fit — our #1-rated Solana bot for 2026:\n\n"
          "🐋 Real-time smart-money tracking\n"
          "🛡️ Scam &amp; rug detection before you buy\n"
          "💸 35% cashback on every trade\n"
          "🔐 Non-custodial · no seed phrase\n\n"
          "👉 Start in 60 seconds, or see how it ranked vs the rest.")

RESULT_KB = kb([
    [{"text": "🥇 Try Guardis →", "url": GUARDIS}],
    [{"text": "🏆 See Full Rankings →", "url": SITE}],
])

def handle_cb(cb):
    data = cb.get("data", "")
    chat_id = cb["message"]["chat"]["id"]
    mid = cb["message"]["message_id"]
    answer_cb(cb["id"])
    if data in STEPS:
        text, rows = STEPS[data]
        edit(chat_id, mid, text, kb(rows))
    elif data == "res":
        edit(chat_id, mid, RESULT, RESULT_KB)

def main():
    try:
        requests.post(f"{API}/setMyDescription", data={"description": "Find your perfect Solana trading bot in 20 seconds. Smart-money signals, scam protection & 35% cashback."}, timeout=10)
    except Exception as e:
        print("setMyDescription skipped:", e, flush=True)
    print("Smart Money Pros bot running...", flush=True)
    offset = None
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"offset": offset, "timeout": 30}, timeout=40).json()
            res = r.get("result", [])
            if res:
                print(f"received {len(res)} update(s)", flush=True)
            for upd in res:
                offset = upd["update_id"] + 1
                if "message" in upd:
                    m = upd["message"]
                    if (m.get("text") or "").startswith("/start"):
                        print("→ /start from", m["chat"]["id"], flush=True)
                        handle_start(m["chat"]["id"], m.get("from", {}))
                elif "callback_query" in upd:
                    print("→ callback:", upd["callback_query"].get("data"), flush=True)
                    handle_cb(upd["callback_query"])
        except Exception as e:
            print("loop error:", e, flush=True); time.sleep(3)

if __name__ == "__main__":
    main()
