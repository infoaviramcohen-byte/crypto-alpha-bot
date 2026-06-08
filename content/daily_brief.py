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
CHANNEL="-1001652015415"  # @cryptonewsweb_3 (Crypto News AI)
API=f"https://api.telegram.org/bot{TOKEN}"

def send(text):
    r=requests.post(f"{API}/sendMessage", json={"chat_id":CHANNEL,"text":text,"parse_mode":"HTML","disable_web_page_preview":True})
    print("sent" if r.json().get("ok") else "ERR: "+str(r.json().get("description")))

def prices():
    return requests.get("https://api.coingecko.com/api/v3/simple/price",
        params={"ids":"bitcoin,ethereum,solana","vs_currencies":"usd","include_24hr_change":True},timeout=15).json()
def fng():
    d=requests.get("https://api.alternative.me/fng/",timeout=15).json()["data"][0]
    return d["value"], d["value_classification"]
def gainers():
    return requests.get("https://api.coingecko.com/api/v3/coins/markets",
        params={"vs_currency":"usd","order":"price_change_percentage_24h_desc","per_page":3,"sparkline":False},timeout=15).json()

def row(name,d):
    v=d.get("usd",0) or 0; c=d.get("usd_24h_change",0) or 0
    vs=f"${v:,.0f}" if v>=100 else f"${v:,.2f}"
    return f"{'📈' if c>=0 else '📉'} {name}: {vs} ({c:+.1f}%)"

def main():
    p=prices()
    try: fv,fc=fng()
    except: fv,fc="?","?"
    fe="😱" if (str(fv).isdigit() and int(fv)<25) else "😨" if (str(fv).isdigit() and int(fv)<45) \
        else "😐" if (str(fv).isdigit() and int(fv)<55) else "😊" if (str(fv).isdigit() and int(fv)<75) else "🤑"
    g=""
    try:
        gs=gainers(); g="\n🔥 <b>Top movers 24h:</b> "+", ".join(f"${x['symbol'].upper()} ({x.get('price_change_percentage_24h',0):+.0f}%)" for x in gs[:3])
    except: pass
    today=datetime.now(timezone.utc).strftime("%b %d")
    send(f"""☀️ <b>DAILY BRIEF — {today}</b>
━━━━━━━━━━━━━━

{row('BTC',p.get('bitcoin',{}))}
{row('ETH',p.get('ethereum',{}))}
{row('SOL',p.get('solana',{}))}

{fe} <b>Fear &amp; Greed:</b> {fv}/100 — {fc}{g}

📡 @cryptonewsweb_3""")

if __name__=="__main__": main()
