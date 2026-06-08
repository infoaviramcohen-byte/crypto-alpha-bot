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
CHANNEL="-1001652015415"
API=f"https://api.telegram.org/bot{TOKEN}"

def send_photo(path, caption):
    with open(path,"rb") as f:
        r=requests.post(f"{API}/sendPhoto",data={"chat_id":CHANNEL,"caption":caption,"parse_mode":"HTML"},files={"photo":f})
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

def col(c): return GREEN if c>=0 else RED
def fmt(v): return f"${v:,.0f}" if v>=100 else f"${v:,.2f}"

def main():
    p=prices()
    def cell(k):
        d=p.get(k,{}); return d.get("usd",0) or 0, d.get("usd_24h_change",0) or 0
    bv,bc=cell("bitcoin"); ev,ec=cell("ethereum"); sv,sc=cell("solana")
    try: fv,fc=fng()
    except: fv,fc="?","?"
    fe="😱" if (str(fv).isdigit() and int(fv)<25) else "😨" if (str(fv).isdigit() and int(fv)<45) \
        else "😐" if (str(fv).isdigit() and int(fv)<55) else "😊" if (str(fv).isdigit() and int(fv)<75) else "🤑"
    today=datetime.now(timezone.utc).strftime("%b %d, %Y")
    lines=[
      (f"BTC      {fmt(bv)}      {bc:+.1f}%", col(bc)),
      (f"ETH      {fmt(ev)}      {ec:+.1f}%", col(ec)),
      (f"SOL      {fmt(sv)}        {sc:+.1f}%", col(sc)),
      ("",None),
      (f"Fear & Greed:  {fv}/100  —  {fc}", GOLD),
    ]
    tmp=tempfile.NamedTemporaryFile(suffix=".png",delete=False).name
    render_card(tmp,"DAILY BRIEF",today,lines,accent=GREEN)
    mv=""
    try:
        gs=gainers(); mv="\n🔥 Top movers: "+", ".join(f"${x['symbol'].upper()} {x.get('price_change_percentage_24h',0):+.0f}%" for x in gs[:3])
    except: pass
    cap=f"☀️ <b>Daily Market Brief</b>\n\n{fe} Market sentiment: <b>{fc}</b> ({fv}/100){mv}\n\n📡 @cryptonewsweb_3"
    send_photo(tmp,cap)
    os.unlink(tmp)

if __name__=="__main__": main()
