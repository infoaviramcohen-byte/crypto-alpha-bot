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

# Rotate topic by day of year so tips don't repeat back-to-back
TOPICS=[
 "spotting a honeypot / rug pull before you buy",
 "why you should use a dedicated burner wallet for trading",
 "how priority fees & MEV protection affect your fills on Solana",
 "reading on-chain smart-money flows",
 "managing risk: position sizing for memecoins",
 "how to verify a token contract is safe",
 "the danger of fake Telegram bot clones (and how to avoid them)",
 "taking profits: why exits matter more than entries",
 "how trading bot fees actually work (and how to pay less)",
 "avoiding FOMO: waiting for confirmation vs chasing pumps",
]

def ai_tip(topic):
    base=f"💡 Trader tip: {topic}. Always do your own research and protect your capital."
    if not ANTHROPIC_KEY: return base
    try:
        import anthropic
        c=anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        m=c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=160,
            messages=[{"role":"user","content":(
                f"You write a crypto trader-education channel. Topic: {topic}. "
                f"Write a genuinely useful, concrete tip in 3-4 short lines (max 320 chars). "
                f"Practical and specific, no fluff, no hype. Don't add a disclaimer.")}])
        return m.content[0].text.strip()
    except Exception as e:
        print("AI err",e); return base

def main():
    doy=datetime.now(timezone.utc).timetuple().tm_yday
    topic=TOPICS[doy % len(TOPICS)]
    tip=ai_tip(topic)
    send(f"""📚 <b>TRADER TIP OF THE DAY</b>
━━━━━━━━━━━━━━

{tip}

🛡️ Stay sharp, stay safe.
📡 @cryptonewsweb_3""")

if __name__=="__main__": main()
