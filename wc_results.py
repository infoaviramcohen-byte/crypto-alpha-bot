#!/usr/bin/env python3
"""Grade finished WC predictions and post a results / track-record update to
@WC2026signals. Runs daily before the new predictions go out."""
import os, sqlite3, datetime, requests

def load_env():
    env = {}
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1); env[k] = v.strip('"')
    return env
ENV = load_env()
WC_TOKEN = os.environ.get("WC_BOT_TOKEN") or ENV.get("WC_BOT_TOKEN", "")
CHANNEL = "-1003877748369"
API = f"https://api.telegram.org/bot{WC_TOKEN}"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wc_cards.db")

FINISHED = {"Match Finished", "FT", "AET", "PEN", "After Extra Time", "Finished"}

def lookup_event(eid):
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/lookupevent.php?id={eid}"
        evs = (requests.get(url, timeout=25).json() or {}).get("events") or []
        return evs[0] if evs else None
    except Exception as e:
        print("lookup error", eid, e); return None

def grade(pick, home, away, hs, a):
    p = (pick or "").lower()
    if "draw" in p:
        return hs == a
    if home.lower() in p:
        return hs > a
    if away.lower() in p:
        return a > hs
    return None  # can't grade automatically

def send(text):
    requests.post(f"{API}/sendMessage", data={"chat_id": CHANNEL, "text": text, "parse_mode": "HTML", "disable_web_page_preview": "true"}, timeout=30)

def run():
    if not os.path.exists(DB):
        print("no db yet"); return
    conn = sqlite3.connect(DB)
    # ensure columns exist (in case of older db)
    conn.execute("""CREATE TABLE IF NOT EXISTS predictions (
        event_id TEXT PRIMARY KEY, home TEXT, away TEXT, pick TEXT, value TEXT,
        posted_at TEXT, graded INTEGER DEFAULT 0, won INTEGER, results_posted INTEGER DEFAULT 0)""")
    rows = conn.execute("SELECT event_id, home, away, pick FROM predictions WHERE graded=0").fetchall()
    newly = []
    for eid, home, away, pick in rows:
        ev = lookup_event(eid)
        if not ev:
            continue
        status = (ev.get("strStatus") or "").strip()
        hs, a = ev.get("intHomeScore"), ev.get("intAwayScore")
        if status not in FINISHED or hs is None or a is None or hs == "" or a == "":
            continue
        hs, a = int(hs), int(a)
        res = grade(pick, home, away, hs, a)
        won = None if res is None else (1 if res else 0)
        conn.execute("UPDATE predictions SET graded=1, won=? WHERE event_id=?", (won, eid))
        if won is not None:
            newly.append((pick, home, away, hs, a, won))
    conn.commit()

    # all-time record
    w = conn.execute("SELECT COUNT(*) FROM predictions WHERE graded=1 AND won=1").fetchone()[0]
    l = conn.execute("SELECT COUNT(*) FROM predictions WHERE graded=1 AND won=0").fetchone()[0]
    conn.close()

    if not newly:
        print("no newly finished matches to grade."); return

    lines = []
    for pick, home, away, hs, a, won in newly:
        mark = "✅" if won else "❌"
        lines.append(f"{mark} {pick} — {home} {hs}-{a} {away}")
    total = w + l
    rate = f"{round(100*w/total)}%" if total else "—"
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%b %d")
    msg = (f"📈 <b>RESULTS — {today}</b>\n\n" + "\n".join(lines) +
           f"\n\n🏆 Running record: <b>{w}W – {l}L</b> ({rate} hit rate)\n"
           f"Transparency always — we post the losses too.\n\n"
           f"18+ · Bet responsibly\n📡 @WC2026signals")
    send(msg)
    print(f"posted results: {len(newly)} graded | record {w}-{l}")

if __name__ == "__main__":
    run()
