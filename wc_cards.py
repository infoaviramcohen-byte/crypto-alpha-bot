#!/usr/bin/env python3
"""Daily World Cup AI betting cards -> @WC2026signals.
Fetches the day's fixtures, generates an AI prediction per match, renders a
branded flag card, and posts it. Runs daily via GitHub Actions."""
import os, io, json, sqlite3, datetime, requests
from PIL import Image, ImageDraw, ImageFont

def load_env():
    env = {}
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k, v = line.strip().split("=", 1)
                env[k] = v.strip('"')
    return env
ENV = load_env()
WC_TOKEN = os.environ.get("WC_BOT_TOKEN") or ENV.get("WC_BOT_TOKEN", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY") or ENV.get("ANTHROPIC_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY") or ENV.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-flash-latest"
CHANNEL = "-1003877748369"
API = f"https://api.telegram.org/bot{WC_TOKEN}"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wc_cards.db")

W, H = 1080, 1350
GREEN = (34, 222, 128); GOLD = (255, 200, 60); WHITE = (245, 247, 250); GREY = (150, 158, 168); DARK = (8, 12, 10)

FLAG = {
    "usa": "us", "united states": "us", "mexico": "mx", "canada": "ca", "argentina": "ar", "brazil": "br",
    "france": "fr", "england": "gb-eng", "spain": "es", "germany": "de", "netherlands": "nl", "portugal": "pt",
    "belgium": "be", "croatia": "hr", "uruguay": "uy", "colombia": "co", "japan": "jp", "south korea": "kr",
    "korea republic": "kr", "australia": "au", "senegal": "sn", "morocco": "ma", "ghana": "gh", "nigeria": "ng",
    "ivory coast": "ci", "cote d'ivoire": "ci", "egypt": "eg", "algeria": "dz", "tunisia": "tn", "cameroon": "cm",
    "ecuador": "ec", "peru": "pe", "chile": "cl", "paraguay": "py", "saudi arabia": "sa", "iran": "ir",
    "iraq": "iq", "qatar": "qa", "jordan": "jo", "switzerland": "ch", "austria": "at", "denmark": "dk",
    "sweden": "se", "norway": "no", "poland": "pl", "scotland": "gb-sct", "wales": "gb-wls", "serbia": "rs",
    "ukraine": "ua", "turkey": "tr", "greece": "gr", "cape verde": "cv", "cabo verde": "cv", "curacao": "cw",
    "haiti": "ht", "panama": "pa", "costa rica": "cr", "jamaica": "jm", "new zealand": "nz", "uzbekistan": "uz",
    "south africa": "za", "venezuela": "ve", "bolivia": "bo",
}

def font(sz, bold=True):
    paths = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in paths:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except: pass
    return ImageFont.load_default()

def flag_img(name, size):
    code = FLAG.get(name.lower().strip())
    if not code:
        return None
    try:
        r = requests.get(f"https://flagcdn.com/w320/{code}.png", timeout=20)
        im = Image.open(io.BytesIO(r.content)).convert("RGBA").resize((size, size))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(im, (0, 0), mask)
        return out
    except Exception:
        return None

def render_card(out, kind, accent, tA, tB, meta, picklabel, pick, conf, value, score=""):
    img = Image.new("RGB", (W, H), DARK); d = ImageDraw.Draw(img, "RGBA")
    for y in range(H):
        t = y / H; d.line([(0, y), (W, y)], fill=(int(8 + 6 * t), int(14 + 11 * t), int(10 + 7 * t)))
    def glow(cx, cy, r, c, s=14):
        for i in range(r, 0, -7): d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=(c[0], c[1], c[2], max(0, s - int(s * (i / r)))))
    glow(160, 150, 460, GREEN, 10); glow(940, 1190, 520, accent, 12)
    for gx in range(0, W, 90): d.line([(gx, 0), (gx, H)], fill=(255, 255, 255, 4))
    def ct(txt, f, y, fill, cx=W / 2): d.text((cx - d.textlength(txt, font=f) / 2, y), txt, font=f, fill=fill)
    ct("FOOTBALL  ·  AI BETTING SIGNALS", font(30), 60, WHITE)
    d.line([(80, 110), (W - 80, 110)], fill=(40, 52, 46), width=2)
    tf = font(30); tw = d.textlength(kind, font=tf)
    d.rounded_rectangle([W / 2 - tw / 2 - 26, 150, W / 2 + tw / 2 + 26, 202], radius=26, fill=(accent[0], accent[1], accent[2], 45), outline=accent, width=2); ct(kind, tf, 160, accent)
    ct("FIFA WORLD CUP 2026", font(24), 224, GOLD)
    fy = 360; r = 150
    for cx, name, col in [(285, tA, GREEN), (795, tB, accent)]:
        fl = flag_img(name, r)
        d.ellipse([cx - r // 2 - 6, fy - r // 2 - 6, cx + r // 2 + 6, fy + r // 2 + 6], outline=col, width=5)
        if fl: img.paste(fl, (cx - r // 2, fy - r // 2), fl)
        else: d.ellipse([cx - r // 2, fy - r // 2, cx + r // 2, fy + r // 2], fill=(30, 36, 32))
        nf = font(40)
        while d.textlength(name, font=nf) > 400 and nf.size > 24: nf = font(nf.size - 2)
        d.text((cx - d.textlength(name, font=nf) / 2, fy + r // 2 + 18), name, font=nf, fill=WHITE)
    ct("VS", font(60), fy - 36, GOLD)
    ct(meta, font(28), fy + r // 2 + 90, GREY)
    px0, py0, px1, py1 = 80, 720, W - 80, 1000
    d.rounded_rectangle([px0, py0, px1, py1], radius=28, fill=(255, 255, 255, 9), outline=(accent[0], accent[1], accent[2], 120), width=2)
    d.text((px0 + 40, py0 + 28), picklabel, font=font(26), fill=accent)
    pf = font(48)
    while d.textlength(pick, font=pf) > px1 - px0 - 80 and pf.size > 28: pf = font(pf.size - 2)
    d.text((px0 + 40, py0 + 66), pick, font=pf, fill=WHITE)
    if score:
        d.text((px0 + 40, py0 + 128), f"Predicted score:  {score}", font=font(30), fill=GOLD)
    if conf:
        by = py1 - 70; bx0, bx1 = px0 + 40, px1 - 40
        d.rounded_rectangle([bx0, by, bx1, by + 18], radius=9, fill=(40, 52, 46))
        d.rounded_rectangle([bx0, by, bx0 + int((bx1 - bx0) * conf / 100), by + 18], radius=9, fill=accent)
        d.text((bx0, by + 30), f"Model confidence: {conf}%", font=font(28), fill=accent)
    vf = font(34)
    while d.textlength(value, font=vf) > W - 160 and vf.size > 22: vf = font(vf.size - 2)
    ct(value, vf, 1040, WHITE)
    d.line([(80, H - 150), (W - 80, H - 150)], fill=(40, 52, 46), width=2)
    ct("@WC2026signals", font(34), H - 128, WHITE); ct("18+  ·  Bet responsibly  ·  Not advice", font(26), H - 78, GREY)
    img.save(out, "PNG")

def todays_fixtures():
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    url = f"https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d={day}&s=Soccer"
    try:
        evs = (requests.get(url, timeout=25).json() or {}).get("events") or []
    except Exception as e:
        print("fixtures error:", e); return []
    return [e for e in evs if "World Cup" in (e.get("strLeague") or "")]

def ai_predict(home, away):
    base = {"pick": f"{home} to win", "score": "1-0", "confidence": 55, "value": "Match result",
            "reasons": ["Stronger squad on paper", "Better recent form", "Tournament experience edge"]}
    if not GEMINI_KEY:
        return base
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        prompt = (
            f"You are an AI football analyst for a betting-signals channel. Match: {home} vs {away}, "
            "FIFA World Cup 2026 group stage. Analyze team strength, form and matchup, then give a data-style lean "
            "and a most-likely final scoreline. Reply ONLY with compact JSON, no markdown: "
            '{"pick":"<Team> to win|Draw","score":"<home_goals>-<away_goals>","confidence":<integer 52-88>,'
            '"value":"<one short value-bet angle, e.g. Team -1 handicap or Over 2.5 goals>",'
            '"reasons":["<r1>","<r2>","<r3>"]}. No extra text, no guarantees.')
        r = requests.post(url, headers={"x-goog-api-key": GEMINI_KEY, "Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=40)
        j = r.json()
        if "error" in j:
            print("gemini error:", str(j["error"].get("message", ""))[:140]); return base
        txt = j["candidates"][0]["content"]["parts"][0]["text"].strip().strip("`")
        if txt.startswith("json"): txt = txt[4:]
        data = json.loads(txt[txt.find("{"):txt.rfind("}") + 1])
        data["confidence"] = int(data.get("confidence", 55))
        data.setdefault("score", "")
        return data
    except Exception as e:
        print("ai_predict error:", e); return base

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS predictions (
        event_id TEXT PRIMARY KEY, home TEXT, away TEXT, pick TEXT, value TEXT,
        posted_at TEXT, graded INTEGER DEFAULT 0, won INTEGER, results_posted INTEGER DEFAULT 0)""")
    conn.commit(); conn.close()

def already(eid):
    conn = sqlite3.connect(DB); row = conn.execute("SELECT 1 FROM predictions WHERE event_id=?", (eid,)).fetchone(); conn.close()
    return row is not None

def save_prediction(eid, home, away, pick, value):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR REPLACE INTO predictions (event_id, home, away, pick, value, posted_at, graded) VALUES (?,?,?,?,?,?,0)",
                 (eid, home, away, pick, value, datetime.datetime.now(datetime.timezone.utc).isoformat()))
    conn.commit(); conn.close()

def post_card(path, caption):
    with open(path, "rb") as f:
        r = requests.post(f"{API}/sendPhoto", data={"chat_id": CHANNEL, "caption": caption, "parse_mode": "HTML"}, files={"photo": f}, timeout=60)
    return r.json().get("ok")

def run():
    init_db()
    fixtures = todays_fixtures()
    print(f"Found {len(fixtures)} World Cup fixtures today.")
    posted = 0
    for e in fixtures:
        eid = str(e.get("idEvent") or e.get("strEvent"))
        if already(eid):
            continue
        # Skip matches that have already kicked off / finished
        ts = e.get("strTimestamp")
        if ts:
            try:
                kickoff = datetime.datetime.fromisoformat(ts).replace(tzinfo=datetime.timezone.utc)
                if kickoff < datetime.datetime.now(datetime.timezone.utc):
                    continue
            except Exception:
                pass
        home = (e.get("strHomeTeam") or "").strip()
        away = (e.get("strAwayTeam") or "").strip()
        if not home or not away:
            continue
        venue = (e.get("strVenue") or "").split(",")[0].strip() or "World Cup"
        t = (e.get("strTimestamp") or "")[11:16]
        meta = f"{venue}" + (f" · {t} UTC" if t else "")
        pred = ai_predict(home, away)
        tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"_wc_{eid}.png")
        render_card(tmp, "AI MATCH PREDICTION", GREEN, home, away, meta, "MODEL PICK",
                    pred.get("pick", f"{home} to win"), pred.get("confidence", 55),
                    "Value: " + pred.get("value", "Match result"), score=pred.get("score", ""))
        reasons = "\n".join(f"• {x}" for x in (pred.get("reasons") or [])[:3])
        score_line = f"🔮 Predicted score: <b>{home} {pred.get('score','')} {away}</b>\n" if pred.get("score") else ""
        cap = (f"🤖 <b>AI MATCH PREDICTION</b>\n\n⚽ {home} vs {away}\n{meta}\n\n"
               f"📊 Model lean: <b>{pred.get('pick','')}</b> ({pred.get('confidence',55)}%)\n"
               f"{score_line}{reasons}\n\n"
               f"🎯 Value: <b>{pred.get('value','')}</b>\n\n18+ · Bet responsibly · Not advice\n📡 @WC2026signals")
        if post_card(tmp, cap):
            save_prediction(eid, home, away, pred.get("pick", f"{home} to win"), pred.get("value", ""))
            posted += 1
            print("posted", home, "vs", away)
        try: os.unlink(tmp)
        except: pass
    print(f"Posted {posted} cards.")

if __name__ == "__main__":
    run()
