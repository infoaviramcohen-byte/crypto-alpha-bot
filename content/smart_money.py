#!/usr/bin/env python3
import requests, os, tempfile
from datetime import datetime, timezone
from visuals import render_card, GREEN, WHITE, GOLD, PURPLE

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

def cg_trending():
    try:
        coins=requests.get("https://api.coingecko.com/api/v3/search/trending",timeout=15).json().get("coins",[])
        return [c["item"]["symbol"].upper() for c in coins[:6]]
    except: return []
def sol_boosts():
    try:
        data=requests.get("https://api.dexscreener.com/token-boosts/top/v1",timeout=15).json()
        out=[]
        for t in data:
            if t.get("chainId")=="solana":
                desc=(t.get("description") or "").strip()[:36]
                if desc: out.append(desc)
            if len(out)>=3: break
        return out
    except: return []
def ai_take(symbols, sol):
    base="Smart money is rotating fast today — these names are catching the most attention on-chain right now."
    if not ANTHROPIC_KEY: return base
    try:
        import anthropic
        c=anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        m=c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=110,
            messages=[{"role":"user","content":(f"You write a sharp crypto 'smart money' channel. Trending today: {symbols}. Solana attention: {sol}. "
            f"Write 2 punchy lines (max 190 chars) on what smart money seems to be watching/accumulating. Sharp, no hype, no disclaimers.")}])
        return m.content[0].text.strip()
    except Exception as e:
        print("AI err",e); return base

def main():
    syms=cg_trending(); sol=sol_boosts(); take=ai_take(syms,sol)
    today=datetime.now(timezone.utc).strftime("%b %d, %Y")
    lines=[("ON THE RADAR TODAY:", GOLD), ("",None)]
    for s in syms[:5]: lines.append((f"  ${s}", WHITE))
    tmp=tempfile.NamedTemporaryFile(suffix=".png",delete=False).name
    render_card(tmp,"SMART MONEY WATCH",today,lines,accent=PURPLE)
    sol_line=("\n🟣 Solana attention: "+" · ".join(sol)) if sol else ""
    cap=f"🐋 <b>Smart Money Watch</b>\n\n{take}{sol_line}\n\n💡 Most volume = where attention flows first.\n📡 @cryptonewsweb_3"
    send_photo(tmp,cap)
    os.unlink(tmp)

if __name__=="__main__": main()
