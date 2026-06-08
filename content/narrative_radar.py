#!/usr/bin/env python3
import requests, os, tempfile
from datetime import datetime, timezone
from visuals import render_card, GREEN, RED, WHITE, GOLD

def load_env():
    env={}
    p=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..",".env")
    if os.path.exists(p):
        for line in open(p):
            if "=" in line and not line.startswith("#"):
                k,v=line.strip().split("=",1); env[k]=v.strip('"')
    return env
ENV=load_env()
TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN") or ENV.get("TELEGRAM_BOT_TOKEN","")
ANTHROPIC_KEY=os.environ.get("ANTHROPIC_API_KEY") or ENV.get("ANTHROPIC_API_KEY","")
CHANNEL="-1001652015415"
API=f"https://api.telegram.org/bot{TOKEN}"

def send_photo(path, caption):
    with open(path,"rb") as f:
        r=requests.post(f"{API}/sendPhoto",data={"chat_id":CHANNEL,"caption":caption,"parse_mode":"HTML"},files={"photo":f})
    print("sent" if r.json().get("ok") else "ERR: "+str(r.json().get("description")))

def top_categories():
    try:
        cats=requests.get("https://api.coingecko.com/api/v3/coins/categories",
            params={"order":"market_cap_change_24h_desc"},timeout=15).json()
        return [(c["name"], c.get("market_cap_change_24h") or 0) for c in cats[:4]]
    except: return []
def trending():
    try:
        coins=requests.get("https://api.coingecko.com/api/v3/search/trending",timeout=15).json().get("coins",[])
        return [c["item"]["symbol"].upper() for c in coins[:5]]
    except: return []
def ai_take(cats, trend):
    base="Money is rotating between narratives fast — watch which sector holds its bid into tomorrow."
    if not ANTHROPIC_KEY: return base
    try:
        import anthropic
        c=anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        m=c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=110,
            messages=[{"role":"user","content":(f"Crypto narrative-rotation channel. Top sectors 24h: {cats}. Trending: {trend}. "
            f"2 punchy lines (max 190 chars) on which narrative is heating up + what it means. Sharp, no hype, no disclaimer.")}])
        return m.content[0].text.strip()
    except Exception as e:
        print("AI err",e); return base

def short(name): return (name[:22]+"…") if len(name)>23 else name

def main():
    cats=top_categories(); trend=trending(); take=ai_take([c[0] for c in cats],trend)
    today=datetime.now(timezone.utc).strftime("%b %d, %Y")
    lines=[("HOTTEST SECTORS (24h):", GOLD), ("",None)]
    for name,chg in cats[:4]:
        lines.append((f"  {short(name)}   {chg:+.1f}%", GREEN if chg>=0 else RED))
    tmp=tempfile.NamedTemporaryFile(suffix=".png",delete=False).name
    render_card(tmp,"NARRATIVE RADAR",today,lines,accent=GREEN)
    tl=("\n🔥 Trending: "+", ".join(f"${s}" for s in trend)) if trend else ""
    cap=f"🔍 <b>Narrative Radar</b>\n\n{take}{tl}\n\n📡 @cryptonewsweb_3"
    send_photo(tmp,cap)
    os.unlink(tmp)

if __name__=="__main__": main()
