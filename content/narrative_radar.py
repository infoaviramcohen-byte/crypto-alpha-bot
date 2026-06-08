#!/usr/bin/env python3
import requests, os
from datetime import datetime, timezone

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

def send(text):
    r=requests.post(f"{API}/sendMessage", json={"chat_id":CHANNEL,"text":text,"parse_mode":"HTML","disable_web_page_preview":True})
    print("sent" if r.json().get("ok") else "ERR: "+str(r.json().get("description")))

def top_categories():
    try:
        cats=requests.get("https://api.coingecko.com/api/v3/coins/categories",
            params={"order":"market_cap_change_24h_desc"},timeout=15).json()
        return [(c["name"], c.get("market_cap_change_24h") or 0) for c in cats[:5]]
    except: return []
def trending():
    try:
        coins=requests.get("https://api.coingecko.com/api/v3/search/trending",timeout=15).json().get("coins",[])
        return [c["item"]["symbol"].upper() for c in coins[:5]]
    except: return []

def ai_take(cats, trend):
    base="Money is rotating between narratives fast — watch which sector keeps its bid into tomorrow."
    if not ANTHROPIC_KEY: return base
    try:
        import anthropic
        c=anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        m=c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=110,
            messages=[{"role":"user","content":(
                f"You write a crypto narrative-rotation channel. Top gaining sectors 24h: {cats}. Trending coins: {trend}. "
                f"Write 2 punchy lines (max 190 chars) on which narrative is heating up and what it means for traders. "
                f"Sharp, no hype, no disclaimers.")}])
        return m.content[0].text.strip()
    except Exception as e:
        print("AI err",e); return base

def main():
    cats=top_categories(); trend=trending()
    take=ai_take([c[0] for c in cats], trend)
    today=datetime.now(timezone.utc).strftime("%b %d")
    cat_lines=""
    for name,chg in cats[:4]:
        cat_lines+=f"{'📈' if chg>=0 else '📉'} {name} ({chg:+.1f}%)\n"
    trend_line=("\n🔥 <b>Trending:</b> "+", ".join(f"${s}" for s in trend)) if trend else ""
    send(f"""🔍 <b>NARRATIVE RADAR — {today}</b>
━━━━━━━━━━━━━━

{take}

<b>Hottest sectors (24h):</b>
{cat_lines}{trend_line}

📡 @cryptonewsweb_3""")

if __name__=="__main__": main()
