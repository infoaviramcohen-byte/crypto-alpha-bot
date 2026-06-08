#!/usr/bin/env python3
import requests, os, re
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
FEEDS=["https://cointelegraph.com/rss","https://decrypt.co/feed","https://theblock.co/rss.xml"]

def send(text):
    r=requests.post(f"{API}/sendMessage", json={"chat_id":CHANNEL,"text":text,"parse_mode":"HTML","disable_web_page_preview":True})
    print("sent" if r.json().get("ok") else "ERR: "+str(r.json().get("description")))

def prices():
    try:
        return requests.get("https://api.coingecko.com/api/v3/simple/price",
            params={"ids":"bitcoin,ethereum,solana","vs_currencies":"usd","include_24hr_change":True},timeout=15).json()
    except: return {}
def headlines():
    out=[]
    try:
        import feedparser
        for f in FEEDS:
            d=feedparser.parse(f)
            for e in d.entries[:4]:
                out.append(e.get("title","").strip())
            if len(out)>=10: break
    except Exception as e:
        print("feed err",e)
    return out[:10]

def row(name,d):
    v=d.get("usd",0) or 0; c=d.get("usd_24h_change",0) or 0
    vs=f"${v:,.0f}" if v>=100 else f"${v:,.2f}"
    return f"{'📈' if c>=0 else '📉'} {name} {vs} ({c:+.1f}%)"

def ai_wrap(titles):
    base="A busy day across crypto — majors held their ranges while attention rotated through trending names. Watch the open tomorrow."
    if not ANTHROPIC_KEY or not titles: return base
    try:
        import anthropic
        c=anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        m=c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=170,
            messages=[{"role":"user","content":(
                "You write a crypto end-of-day wrap. Here are today's headlines:\n- "+"\n- ".join(titles)+
                "\n\nWrite a 3-line recap of what mattered today + 1 line on what to watch tomorrow. "
                "Max 360 chars total. Sharp, no hype, no disclaimer.")}])
        return m.content[0].text.strip()
    except Exception as e:
        print("AI err",e); return base

def main():
    p=prices(); wrap=ai_wrap(headlines())
    today=datetime.now(timezone.utc).strftime("%b %d")
    pl=""
    if p:
        pl="\n".join([row('BTC',p.get('bitcoin',{})),row('ETH',p.get('ethereum',{})),row('SOL',p.get('solana',{}))])+"\n\n"
    send(f"""🌙 <b>EVENING WRAP — {today}</b>
━━━━━━━━━━━━━━

{pl}{wrap}

📡 @cryptonewsweb_3 — see you at the open ☀️""")

if __name__=="__main__": main()
