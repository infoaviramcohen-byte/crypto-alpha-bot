#!/usr/bin/env python3
"""Grade finished WC predictions and post a results / track-record update to
@WC2026signals. Runs daily before the new predictions go out."""
import os, sqlite3, datetime, requests
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
GREEN = (34, 222, 128); GOLD = (255, 200, 60); WHITE = (245, 247, 250); GREY = (150, 158, 168); RED = (255, 86, 86); DARK = (8, 12, 10)

def _font(sz, bold=True):
    for p in ["/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except: pass
    return ImageFont.load_default()

def render_results_card(out, items, w, l, rate, day):
    img = Image.new("RGB", (W, H), DARK); d = ImageDraw.Draw(img, "RGBA")
    for y in range(H):
        t = y / H; d.line([(0, y), (W, y)], fill=(int(8 + 6 * t), int(14 + 11 * t), int(10 + 7 * t)))
    def glow(cx, cy, r, c, s=13):
        for i in range(r, 0, -7): d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=(c[0], c[1], c[2], max(0, s - int(s * (i / r)))))
    glow(160, 150, 460, GREEN, 10); glow(940, 1190, 520, GOLD, 11)
    def ct(txt, f, y, fill, cx=W / 2): d.text((cx - d.textlength(txt, font=f) / 2, y), txt, font=f, fill=fill)
    ct("FOOTBALL  ·  AI BETTING SIGNALS", _font(30), 60, WHITE)
    d.line([(80, 110), (W - 80, 110)], fill=(40, 52, 46), width=2)
    tag = f"RESULTS · {day}"
    tf = _font(30); tw = d.textlength(tag, font=tf)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, 150, W / 2 + tw / 2 + 26, 202], radius=26, fill=(255, 200, 60, 45), outline=GOLD, width=2)
    ct(tag, tf, 160, GOLD)
    # rows
    y = 270
    for pick, home, away, hs, a, won in items[:6]:
        col = GREEN if won else RED
        d.rounded_rectangle([80, y, W - 80, y + 110], radius=20, fill=(255, 255, 255, 8), outline=(col[0], col[1], col[2], 110), width=2)
        # marker circle
        cx = 145; cy = y + 55; r = 26
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
        if won:
            d.line([(cx - 12, cy), (cx - 3, cy + 11)], fill=(8, 12, 10), width=5)
            d.line([(cx - 3, cy + 11), (cx + 14, cy - 11)], fill=(8, 12, 10), width=5)
        else:
            d.line([(cx - 11, cy - 11), (cx + 11, cy + 11)], fill=(8, 12, 10), width=5)
            d.line([(cx - 11, cy + 11), (cx + 11, cy - 11)], fill=(8, 12, 10), width=5)
        pf = _font(34)
        pk = pick if d.textlength(pick, font=pf) < 560 else pick[:34]
        d.text((200, y + 18), pk, font=pf, fill=WHITE)
        d.text((200, y + 60), f"{home} {hs}-{a} {away}", font=_font(28), fill=GREY)
        y += 126
    # record box
    by = y + 20
    d.rounded_rectangle([80, by, W - 80, by + 180], radius=28, fill=(34, 222, 128, 22), outline=GREEN, width=2)
    ct(f"{w}W  –  {l}L", _font(72), by + 28, WHITE)
    ct(f"{rate} hit rate", _font(34), by + 118, GREEN)
    ct("Transparency always — we post the losses too.", _font(28), by + 210, GREY)
    d.line([(80, H - 150), (W - 80, H - 150)], fill=(40, 52, 46), width=2)
    ct("@WC2026signals", _font(34), H - 128, WHITE)
    ct("18+  ·  Bet responsibly  ·  Not advice", _font(26), H - 78, GREY)
    img.save(out, "PNG")

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

    total = w + l
    rate = f"{round(100*w/total)}%" if total else "—"
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%b %d")

    lines = []
    for pick, home, away, hs, a, won in newly:
        mark = "✅" if won else "❌"
        lines.append(f"{mark} {pick} — {home} {hs}-{a} {away}")
    cap = (f"📈 <b>RESULTS — {today}</b>\n\n" + "\n".join(lines) +
           f"\n\n🏆 Running record: <b>{w}W – {l}L</b> ({rate} hit rate)\n"
           f"Transparency always — we post the losses too.\n\n18+ · Bet responsibly\n📡 @WC2026signals")

    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_wc_results.png")
    try:
        render_results_card(tmp, newly, w, l, rate, today)
        with open(tmp, "rb") as f:
            requests.post(f"{API}/sendPhoto", data={"chat_id": CHANNEL, "caption": cap, "parse_mode": "HTML"}, files={"photo": f}, timeout=60)
        os.unlink(tmp)
    except Exception as e:
        print("results card error, sending text:", e)
        send(cap)
    print(f"posted results: {len(newly)} graded | record {w}-{l}")

if __name__ == "__main__":
    run()
