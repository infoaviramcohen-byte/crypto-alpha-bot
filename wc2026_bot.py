import requests
from datetime import datetime, timezone, timedelta
import random

BOT_TOKEN = "8745600762:AAERjdVIaH5nSohseKif8olMkfuUU-R7jVg"
CHANNEL_ID = "@WC2026signals"

# WC2026 Group Stage schedule (kickoff times UTC)
MATCHES = [
    {"date": "2026-06-11", "home": "Mexico", "away": "Ecuador", "group": "A", "time": "23:00"},
    {"date": "2026-06-12", "home": "USA", "away": "Canada", "group": "B", "time": "02:00"},
    {"date": "2026-06-12", "home": "Argentina", "away": "Nigeria", "group": "C", "time": "18:00"},
    {"date": "2026-06-12", "home": "Brazil", "away": "Colombia", "group": "D", "time": "21:00"},
    {"date": "2026-06-13", "home": "France", "away": "Australia", "group": "E", "time": "18:00"},
    {"date": "2026-06-13", "home": "England", "away": "Senegal", "group": "F", "time": "21:00"},
    {"date": "2026-06-13", "home": "Germany", "away": "South Korea", "group": "G", "time": "00:00"},
    {"date": "2026-06-14", "home": "Spain", "away": "Morocco", "group": "H", "time": "18:00"},
    {"date": "2026-06-14", "home": "Portugal", "away": "Ghana", "group": "I", "time": "21:00"},
    {"date": "2026-06-15", "home": "Netherlands", "away": "Uruguay", "group": "J", "time": "18:00"},
    {"date": "2026-06-15", "home": "Japan", "away": "Croatia", "group": "K", "time": "21:00"},
    {"date": "2026-06-16", "home": "Italy", "away": "Cameroon", "group": "L", "time": "18:00"},
]

TEAM_TIPS = {
    "Argentina": ("Both Teams to Score", "Argentina attack creates chances but leave gaps"),
    "Brazil": ("Over 2.5 Goals", "Brazil's attack has been relentless in qualifiers"),
    "France": ("France Win & Over 1.5", "France have best squad depth in the tournament"),
    "England": ("England Win to Nil", "England's defence has been rock solid"),
    "Spain": ("Over 2.5 Goals", "Spain's tiki-taka generates volume chances"),
    "Germany": ("Germany Win", "Germany always perform at World Cups"),
    "Portugal": ("Ronaldo Anytime Scorer", "Ronaldo hungry to prove himself one last time"),
    "Netherlands": ("Netherlands Win", "Netherlands have a well-balanced squad"),
    "USA": ("USA to Score", "Host nation energy will drive them forward"),
    "Mexico": ("Mexico Win", "Home crowd advantage is massive in CONCACAF"),
    "Japan": ("Japan & Under 2.5", "Japan are defensively disciplined"),
    "Italy": ("Italy Win to Nil", "Italy's Azzurri defence is world class"),
}

VALUE_BETS = [
    ("Both Teams to Score", "High-tempo group stage matches favour BTTS — over 68% hit rate in last WC"),
    ("Over 2.5 Goals", "Group stage averages 2.7 goals per game historically"),
    ("First Half Over 1.5", "Teams attack early to set the tone — great value pre-match"),
    ("Asian Handicap -0.5 Favourite", "Top seeds rarely drop points in group openers"),
    ("Anytime Goalscorer", "Star players show up on the biggest stage"),
    ("Draw No Bet — Favourite", "Eliminate the draw risk on heavy favourites"),
]

BONUSES = [
    ("100% Welcome Bonus up to $200", "New accounts only · T&Cs apply"),
    ("Bet $10 Get $30 in Free Bets", "Min deposit $10 · Free bets expire in 7 days"),
    ("Enhanced Odds on All WC2026 Matches", "Available for 24h only · Max stake $5"),
    ("Money Back if Your Team Loses", "Up to $50 refund as free bet · Selected markets"),
    ("Accumulator Boost — 50% Extra Winnings", "On 4+ leg accumulators · Every matchday"),
]

def send(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    )

def get_todays_matches():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return [m for m in MATCHES if m["date"] == today]

def get_tomorrows_matches():
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
    return [m for m in MATCHES if m["date"] == tomorrow]

def get_next_matches(n=3):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    upcoming = [m for m in MATCHES if m["date"] >= today]
    return upcoming[:n]

def morning():
    today_matches = get_todays_matches()
    next_matches = get_next_matches(3)
    vbet, vreason = random.choice(VALUE_BETS)
    bonus, bcond = random.choice(BONUSES)

    if today_matches:
        match_lines = ""
        for m in today_matches:
            tip_market, tip_reason = TEAM_TIPS.get(m["home"], ("Home Win", "Strong home performance expected"))
            match_lines += f"\n⚽ <b>{m['home']} vs {m['away']}</b> — Group {m['group']} · {m['time']} UTC\n"
            match_lines += f"📌 Our Pick: <b>{tip_market}</b>\n"
            match_lines += f"💡 {tip_reason}\n"

        return f"""🌅 <b>WC2026 MATCH DAY BRIEF</b>

🏆 <b>Today's Fixtures & Picks:</b>
{match_lines}
📊 <b>Value Bet of the Day:</b>
<b>{vbet}</b> — {vreason}

🎁 <b>Best Bonus Today:</b>
{bonus}
<i>{bcond}</i>

💬 Share with your betting group — let's win together.
📡 @WC2026signals"""

    else:
        next_lines = ""
        for m in next_matches:
            next_lines += f"• <b>{m['home']} vs {m['away']}</b> — {m['date']} · Group {m['group']}\n"

        days_to_wc = (datetime(2026, 6, 11, tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
        countdown = f"⏳ <b>{max(0, days_to_wc)} days</b> until kickoff!" if days_to_wc > 0 else "🚨 <b>The World Cup is HERE!</b>"

        return f"""🌅 <b>WC2026 MORNING BRIEF</b>

{countdown}

📅 <b>Next Matches to Watch:</b>
{next_lines}
📊 <b>Pre-Tournament Value Bet:</b>
<b>{vbet}</b> — {vreason}

🎁 <b>Best Bonus Right Now:</b>
{bonus}
<i>{bcond}</i>

💬 Forward this to your group — more members = better intel.
📡 @WC2026signals"""

def afternoon():
    next_matches = get_next_matches(2)
    vbet, vreason = random.choice(VALUE_BETS)
    bonus, bcond = random.choice(BONUSES)

    match_lines = ""
    for m in next_matches:
        tip_market, tip_reason = TEAM_TIPS.get(m["home"], ("Home Win", "Form suggests home advantage"))
        match_lines += f"⚽ <b>{m['home']} vs {m['away']}</b>\n📌 {tip_market} · {tip_reason}\n\n"

    stats = [
        ("68%", "of WC group matches have BTTS"),
        ("73%", "of WC favourites win their opener"),
        ("2.7", "average goals per WC group game"),
        ("81%", "of top seeds advance from groups"),
    ]
    stat_val, stat_label = random.choice(stats)

    return f"""⚡ <b>ODDS ALERT — MIDDAY PULSE</b>

📈 <b>Stat that matters:</b>
<b>{stat_val}</b> — {stat_label}

🔍 <b>Upcoming Value Plays:</b>
{match_lines}🎯 <b>Sharp Pick:</b> {vbet}
<i>{vreason}</i>

🎁 <b>Don't miss:</b> {bonus}
<i>{bcond}</i>

💬 Tag a friend who bets on football.
📡 @WC2026signals"""

def evening():
    tomorrow_matches = get_tomorrows_matches()
    next_matches = get_next_matches(3)
    bonus, bcond = random.choice(BONUSES)

    acca_teams = random.sample(list(TEAM_TIPS.keys()), 3)
    acca_lines = ""
    for team in acca_teams:
        market, _ = TEAM_TIPS[team]
        acca_lines += f"• {team} — {market}\n"

    if tomorrow_matches:
        preview_lines = ""
        for m in tomorrow_matches:
            tip_market, tip_reason = TEAM_TIPS.get(m["home"], ("Home Win", "Tactical edge expected"))
            preview_lines += f"⚽ <b>{m['home']} vs {m['away']}</b> · {m['time']} UTC\n"
            preview_lines += f"📌 Pick: <b>{tip_market}</b> — {tip_reason}\n\n"

        return f"""🌙 <b>TOMORROW'S PREVIEW & PICKS</b>

{preview_lines}🔗 <b>Tonight's Accumulator:</b>
{acca_lines}
⚠️ Always bet responsibly. Accas are high risk / high reward.

🎁 <b>Boost your bankroll:</b> {bonus}
<i>{bcond}</i>

💬 Share with your betting crew.
📡 @WC2026signals"""

    else:
        next_lines = ""
        for m in next_matches:
            next_lines += f"• <b>{m['home']} vs {m['away']}</b> — {m['date']}\n"

        return f"""🌙 <b>EVENING PREVIEW</b>

📅 <b>Matches Coming Up:</b>
{next_lines}
🔗 <b>Accumulator Idea:</b>
{acca_lines}
⚠️ Bet responsibly. Past performance ≠ future results.

🎁 {bonus}
<i>{bcond}</i>

💬 Know someone who loves football betting? Send them this channel.
📡 @WC2026signals"""

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
