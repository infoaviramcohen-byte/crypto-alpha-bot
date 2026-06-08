#!/usr/bin/env python3
import requests, os, tempfile
from datetime import datetime, timezone
from visuals import render_card, WHITE, GOLD, GREEN, wrap_lines

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

TOPICS=[
 ("Spot a rug before you buy","spotting a honeypot / rug pull before you buy"),
 ("Use a burner wallet","why you should use a dedicated burner wallet for trading"),
 ("Beat slow fills","how priority fees & MEV protection affect your fills on Solana"),
 ("Follow the smart money","reading on-chain smart-money flows"),
 ("Size your bets","position sizing & risk management for memecoins"),
 ("Verify the contract","how to verify a token contract is safe"),
 ("Avoid fake bots","the danger of fake Telegram bot clones and how to avoid them"),
 ("Exits > entries","why taking profits matters more than your entry"),
 ("Pay less in fees","how trading-bot fees work and how to pay less"),
 ("Beat FOMO","waiting for confirmation vs chasing pumps"),
]

def ai_tip(topic):
    base=f"{topic}. Always do your own research and protect your capital."
    if not ANTHROPIC_KEY: return base
    try:
        import anthropic
        c=anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        m=c.messages.create(model="claude-haiku-4-5-20251001",max_tokens=150,
            messages=[{"role":"user","content":(f"Crypto trader-education channel. Topic: {topic}. "
            f"Write a genuinely useful, concrete tip in 2-3 short sentences (max 260 chars). Practical, no fluff, no disclaimer.")}])
        return m.content[0].text.strip()
    except Exception as e:
        print("AI err",e); return base

def main():
    doy=datetime.now(timezone.utc).timetuple().tm_yday
    short,topic=TOPICS[doy % len(TOPICS)]
    tip=ai_tip(topic)
    lines=[("",None)]+wrap_lines(tip, 34, WHITE)
    tmp=tempfile.NamedTemporaryFile(suffix=".png",delete=False).name
    render_card(tmp,"TRADER TIP",short,lines,accent=GOLD)
    cap=f"📚 <b>Trader Tip of the Day</b>\n\n{tip}\n\n🛡️ Stay sharp, stay safe.\n📡 @cryptonewsweb_3"
    send_photo(tmp,cap)
    os.unlink(tmp)

if __name__=="__main__": main()
