#!/usr/bin/env python3
import requests
import sys
import os
from datetime import datetime

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHANNELS = ["-1002481155935"]  # Crypto Alpha Feed only

def send(text):
    for chat_id in CHANNELS:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        )

def get_market_data():
    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "ids": "bitcoin,ethereum,solana",
            "price_change_percentage": "24h"
        },
        timeout=10
    ).json()
    return {c["id"]: c for c in r}

def get_top_gainer():
    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "percent_change_24h_desc",
            "per_page": 20,
            "page": 1,
            "price_change_percentage": "24h"
        },
        timeout=10
    ).json()
    top = max(r, key=lambda x: x.get("price_change_percentage_24h") or 0)
    return top

def get_eth_gas():
    try:
        r = requests.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle", timeout=10).json()
        return r["result"]["ProposeGasPrice"]
    except:
        return "N/A"

def get_dex_movers():
    r = requests.get(
        "https://api.dexscreener.com/latest/dex/tokens/ETH,SOL",
        timeout=10
    ).json()
    pairs = r.get("pairs", []) or []
    # sort by volume change
    pairs = [p for p in pairs if p.get("volume", {}).get("h24")]
    pairs.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0)), reverse=True)
    return pairs[:3]

def arrow(pct):
    return "🟢" if pct >= 0 else "🔴"

def fmt_pct(pct):
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"

def morning_post():
    coins = get_market_data()
    gainer = get_top_gainer()
    gas = get_eth_gas()
    btc = coins.get("bitcoin", {})
    eth = coins.get("ethereum", {})
    sol = coins.get("solana", {})

    btc_pct = btc.get("price_change_percentage_24h", 0) or 0
    eth_pct = eth.get("price_change_percentage_24h", 0) or 0
    sol_pct = sol.get("price_change_percentage_24h", 0) or 0
    gain_pct = gainer.get("price_change_percentage_24h", 0) or 0

    text = f"""⚡ MARKET PULSE — {datetime.utcnow().strftime('%b %d')}

{arrow(btc_pct)} BTC: ${btc.get('current_price', 0):,.0f} ({fmt_pct(btc_pct)})
{arrow(eth_pct)} ETH: ${eth.get('current_price', 0):,.0f} ({fmt_pct(eth_pct)})
{arrow(sol_pct)} SOL: ${sol.get('current_price', 0):,.2f} ({fmt_pct(sol_pct)})

🏆 Top Gainer: ${gainer.get('symbol','').upper()} {fmt_pct(gain_pct)}
⛽ ETH Gas: {gas} Gwei

📡 Crypto Alpha Feed"""
    send(text)

def midday_post():
    try:
        # Top trending on DexScreener - Solana pairs
        r = requests.get("https://api.dexscreener.com/latest/dex/search?q=SOL", timeout=10).json()
        pairs = r.get("pairs", []) or []
        pairs = [p for p in pairs if p.get("chainId") == "solana" and p.get("volume", {}).get("h24")]
        pairs.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0)), reverse=True)
        top = pairs[:3]

        lines = []
        for p in top:
            name = p.get("baseToken", {}).get("symbol", "?")
            vol = float(p.get("volume", {}).get("h24", 0))
            price_change = p.get("priceChange", {}).get("h24", 0) or 0
            lines.append(f"{arrow(float(price_change))} ${name} — Vol: ${vol:,.0f} ({fmt_pct(float(price_change))})")

        body = "\n".join(lines) if lines else "No data available"
        text = f"""🔥 ON-CHAIN ALPHA — SOLANA TOP VOLUME

{body}

These are the pairs with highest 24h trading volume on Solana DEXs right now.

📡 Crypto Alpha Feed"""
        send(text)
    except Exception as e:
        print(f"Midday error: {e}")

def evening_post():
    coins = get_market_data()
    btc = coins.get("bitcoin", {})
    eth = coins.get("ethereum", {})
    sol = coins.get("solana", {})

    btc_pct = btc.get("price_change_percentage_24h", 0) or 0
    eth_pct = eth.get("price_change_percentage_24h", 0) or 0
    sol_pct = sol.get("price_change_percentage_24h", 0) or 0

    overall = (btc_pct + eth_pct + sol_pct) / 3
    mood = "Bullish 🟢" if overall > 1 else "Bearish 🔴" if overall < -1 else "Neutral ⚪"

    text = f"""🌙 DAILY WRAP — {datetime.utcnow().strftime('%b %d')}

Market Sentiment: {mood}

{arrow(btc_pct)} BTC closed at ${btc.get('current_price', 0):,.0f} ({fmt_pct(btc_pct)})
{arrow(eth_pct)} ETH closed at ${eth.get('current_price', 0):,.0f} ({fmt_pct(eth_pct)})
{arrow(sol_pct)} SOL closed at ${sol.get('current_price', 0):,.2f} ({fmt_pct(sol_pct)})

See you tomorrow with more alpha. 👊

📡 Crypto Alpha Feed"""
    send(text)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "morning"
    if mode == "morning":
        morning_post()
    elif mode == "midday":
        midday_post()
    elif mode == "evening":
        evening_post()
    else:
        print("Usage: post.py [morning|midday|evening]")
