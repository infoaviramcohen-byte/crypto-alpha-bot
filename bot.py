import requests
from datetime import datetime, timezone

BOT_TOKEN = "8944585311:AAEH3vYOuBZStInpsm5FLxtawqQp7MfxE-E"
CHANNEL_ID = "@crypto_alpha_daily"

def send(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    )

def fear_greed():
    d = requests.get("https://api.alternative.me/fng/", timeout=10).json()
    v = d["data"][0]["value"]
    c = d["data"][0]["value_classification"]
    e = "😱" if int(v) < 25 else "😨" if int(v) < 45 else "😐" if int(v) < 55 else "😊" if int(v) < 75 else "🤑"
    return v, c, e

def prices():
    return requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "bitcoin,solana,ethereum", "vs_currencies": "usd", "include_24hr_change": True},
        timeout=10
    ).json()

def trending():
    return requests.get("https://api.coingecko.com/api/v3/search/trending", timeout=10).json().get("coins", [])[:5]

def top_gainers():
    return requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={"vs_currency": "usd", "order": "price_change_percentage_24h_desc", "per_page": 5, "sparkline": False},
        timeout=10
    ).json()

def sol_trending():
    data = requests.get("https://api.dexscreener.com/token-boosts/top/v1", timeout=10).json()
    return [t for t in data if t.get("chainId") == "solana"][:3]

def morning():
    fv, fc, fe = fear_greed()
    p = prices()
    gainers = top_gainers()
    btc = p.get("bitcoin", {})
    sol = p.get("solana", {})
    g = gainers[0] if gainers else {}

    return f"""🌅 <b>CRYPTO ALPHA — MORNING BRIEF</b>

<b>Market Snapshot:</b>
{"📈" if btc.get("usd_24h_change",0) > 0 else "📉"} BTC: ${btc.get("usd",0):,.0f} ({btc.get("usd_24h_change",0):+.1f}%)
{"📈" if sol.get("usd_24h_change",0) > 0 else "📉"} SOL: ${sol.get("usd",0):,.2f} ({sol.get("usd_24h_change",0):+.1f}%)

{fe} <b>Fear & Greed:</b> {fv}/100 — {fc}

🔥 <b>Top Mover 24h:</b> ${g.get("symbol","").upper()} +{g.get("price_change_percentage_24h",0):.1f}%
Smart money spotted this early. Did you?

⚡ Copy the wallets catching these moves automatically.
💬 Share this with a trader who needs to see it.

<i>📡 @crypto_alpha_daily — Pure alpha, no noise.</i>"""

def afternoon():
    t = trending()
    sol = sol_trending()

    lines = ""
    for coin in t[:3]:
        item = coin.get("item", {})
        lines += f"• <b>${item.get('symbol','').upper()}</b> — market cap rank #{item.get('market_cap_rank','?')}\n"

    sol_line = ""
    if sol:
        tok = sol[0]
        desc = tok.get("description", "")[:30]
        sol_line = f"\n🟣 <b>Solana Spotlight:</b> {desc} — volume spiking now\n"

    return f"""⚡ <b>ALPHA PULSE — MIDDAY</b>

📊 <b>What smart money is watching right now:</b>
{lines}{sol_line}
💡 These aren't random — wallets with 10x track records are accumulating.

🎯 Don't chase. Copy.
💬 Forward this to your trading group.

<i>📡 @crypto_alpha_daily — We find it first.</i>"""

def evening():
    fv, fc, fe = fear_greed()
    t = trending()

    lines = ""
    for coin in t[:4]:
        item = coin.get("item", {})
        lines += f"• <b>${item.get('symbol','').upper()}</b> ({item.get('name','')})\n"

    sentiment_take = "Smart wallets accumulating quietly." if int(fv) < 50 else "Retail is euphoric — smart money is selective."

    return f"""🌙 <b>EVENING ALPHA WRAP</b>

🧠 <b>Smart Money Watchlist Tonight:</b>
{lines}
{fe} <b>Sentiment:</b> {fv}/100 — {fc}
💬 {sentiment_take}

🔁 Track and copy the top 1% wallets on Solana.
💬 Know a trader who'd want this? Send them the channel.

<i>📡 @crypto_alpha_daily — Tomorrow's alpha, tonight.</i>"""

def main():
    hour = datetime.now(timezone.utc).hour
    if hour < 11:
        send(morning())
    elif hour < 16:
        send(afternoon())
    else:
        send(evening())

if __name__ == "__main__":
    main()
