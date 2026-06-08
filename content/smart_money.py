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
                desc=(t.get("description") or "").strip()[:40]
                if desc: out.append(desc)
            if len(out)>=3: break
        return out
    except: return []

def ai_take(symbols, sol):
    base="Smart money is rotating fast today — these are the names catching the most attention on-chain right now."
    if not ANTHROPIC_KEY: return base
    try:
        import anthropic
        c=anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        m=c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=110,
            messages=[{"role":"user","content":(
                f"You write a sharp crypto 'smart money' channel. Trending today: {symbols}. Solana attention: {sol}. "
                f"Write 2 punchy lines (max 190 chars) on what smart money seems to be watching/accumulating today. "
                f"Sharp insight, no hype words (no 'moon'/'gem'), no disclaimers.")}])
        return m.content[0].text.strip()
    except Exception as e:
        print("AI err",e); return base

def main():
    syms=cg_trending(); sol=sol_boosts()
    take=ai_take(syms, sol)
    today=datetime.now(timezone.utc).strftime("%b %d")
    trend_line=("🔥 <b>On the radar:</b> "+", ".join(f"${s}" for s in syms)+"\n\n") if syms else ""
    sol_line=("🟣 <b>Solana attention:</b> "+" · ".join(sol)+"\n\n") if sol else ""
    send(f"""🐋 <b>SMART MONEY WATCH — {today}</b>
━━━━━━━━━━━━━━

{take}

{trend_line}{sol_line}💡 The narrative with the most volume = where attention is flowing first.

📡 @cryptonewsweb_3""")

if __name__=="__main__": main()
