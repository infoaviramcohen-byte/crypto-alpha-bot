#!/usr/bin/env python3
import requests, os, tempfile
from datetime import datetime, timezone
from visuals import render_card, GREEN, RED, WHITE, GOLD, PURPLE

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

def send_photo(path, caption):
    with open(path,"rb") as f:
        r=requests.post(f"{API}/sendPhoto",data={"chat_id":CHANNEL,"caption":caption,"parse_mode":"HTML"},files={"photo":f})
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
            for e in d.entries[:4]: out.append(e.get("title","").strip())
            if len(out)>=10: break
    except Exception as e: print("feed err",e)
    return out[:10]
def ai_wrap(titles):
    base="Majors held their ranges while attention rotated through trending names. Watch the open tomorrow."
    if not ANTHROPIC_KEY or not titles: return base
    try:
        import anthropic
        c=anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        m=c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=160,
            messages=[{"role":"user","content":("Crypto end-of-day wrap. Today's headlines:\n- "+"\n- ".join(titles)+
            "\n\n2-3 line recap of what mattered + 1 line on what to watch tomorrow. Max 320 chars. Sharp, no hype, no disclaimer.")}])
        return m.content[0].text.strip()
    except Exception as e:
        print("AI err",e); return base

def col(c): return GREEN if c>=0 else RED
def fmt(v): return f"${v:,.0f}" if v>=100 else f"${v:,.2f}"

def main():
    p=prices(); wrap=ai_wrap(headlines())
    today=datetime.now(timezone.utc).strftime("%b %d, %Y")
    lines=[("WHERE WE CLOSED:", GOLD), ("",None)]
    for k,lbl in [("bitcoin","BTC"),("ethereum","ETH"),("solana","SOL")]:
        d=p.get(k,{}); v=d.get("usd",0) or 0; c=d.get("usd_24h_change",0) or 0
        lines.append((f"  {lbl}    {fmt(v)}     {c:+.1f}%", col(c)))
    tmp=tempfile.NamedTemporaryFile(suffix=".png",delete=False).name
    render_card(tmp,"EVENING WRAP",today,lines,accent=PURPLE)
    cap=f"🌙 <b>Evening Wrap</b>\n\n{wrap}\n\n📡 @cryptonewsweb_3 — see you at the open ☀️"
    send_photo(tmp,cap)
    os.unlink(tmp)

if __name__=="__main__": main()
