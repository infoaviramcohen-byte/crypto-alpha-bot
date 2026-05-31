import requests
from datetime import datetime, timezone, timedelta
import random

BOT_TOKEN = "8745600762:AAERjdVIaH5nSohseKif8olMkfuUU-R7jVg"
CHANNEL_ID = "@WC2026signals"

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

TEAM_ANALYSIS = {
    "Argentina": {
        "tip": "Both Teams to Score",
        "reason": "Argentina's attack is world class but they concede chances. Opponents raise their game against them.",
        "key_player": "Lautaro Martínez — clinical in big matches",
        "stat": "Argentina conceded in 7 of their last 10 internationals"
    },
    "Brazil": {
        "tip": "Over 2.5 Goals",
        "reason": "Brazil averaged 3.1 goals per game in qualifiers. Attack is relentless.",
        "key_player": "Vinicius Jr — unstoppable in open space",
        "stat": "Brazil scored 2+ goals in 8 of last 10 matches"
    },
    "France": {
        "tip": "France Win & Over 1.5",
        "reason": "Deepest squad in the tournament. Mbappé + Dembélé is unplayable on the break.",
        "key_player": "Kylian Mbappé — top scorer favourite",
        "stat": "France won 9 of last 10 competitive matches"
    },
    "England": {
        "tip": "Win to Nil",
        "reason": "England's defence has been the best in Europe. Pickford commanding in goal.",
        "key_player": "Jude Bellingham — drives from midfield into attacking positions",
        "stat": "England kept 6 clean sheets in last 10 games"
    },
    "Spain": {
        "tip": "Over 2.5 Goals",
        "reason": "Spain's tiki-taka generates 15+ shots per game. High tempo, high volume.",
        "key_player": "Pedri — controls the tempo and creates for others",
        "stat": "Spain averaged 2.9 goals per game in Euro 2024"
    },
    "Germany": {
        "tip": "Germany Win",
        "reason": "Tournament football brings out the best in Germany. Home World Cup mentality despite playing away.",
        "key_player": "Florian Wirtz — creative spark in the final third",
        "stat": "Germany lost only 1 of last 12 competitive matches"
    },
    "Portugal": {
        "tip": "Over 2.5 Goals",
        "reason": "Portugal's attack is loaded — Ronaldo, Félix, Leão. They go forward with intent.",
        "key_player": "Cristiano Ronaldo — motivated to end career with WC trophy",
        "stat": "Portugal scored 3+ goals in 5 of last 8 matches"
    },
    "Netherlands": {
        "tip": "Netherlands Win",
        "reason": "Van Dijk organises one of the tightest defences at the tournament.",
        "key_player": "Cody Gakpo — electric on the left, creates and scores",
        "stat": "Netherlands unbeaten in last 8 competitive matches"
    },
    "Mexico": {
        "tip": "Mexico to Score",
        "reason": "Host nation energy is massive. Mexico always perform at home World Cups.",
        "key_player": "Hirving Lozano — pace and directness on the wing",
        "stat": "Mexico scored in all 10 home qualifiers"
    },
    "USA": {
        "tip": "USA to Score",
        "reason": "Young, fast, hungry squad. Playing at home in front of massive crowd.",
        "key_player": "Christian Pulisic — captain, leader, match-winner",
        "stat": "USA scored in 8 of last 10 matches"
    },
    "Japan": {
        "tip": "Under 2.5 Goals",
        "reason": "Japan are tactically disciplined. They defend deep and hit on the counter.",
        "key_player": "Takefusa Kubo — quick and direct, dangerous on transition",
        "stat": "Japan kept clean sheet in 5 of last 8 matches"
    },
    "Italy": {
        "tip": "Italy Win to Nil",
        "reason": "Azzurri defence is world class. They make matches compact and hard to score against.",
        "key_player": "Federico Chiesa — pace and directness in attack",
        "stat": "Italy conceded less than 1 goal per game in qualifiers"
    },
}

WC_STATS = [
    ("68%", "of World Cup group matches have both teams scoring"),
    ("73%", "of top-seeded teams win their opening match"),
    ("2.7", "average goals per game in WC group stage historically"),
    ("81%", "of group stage favourites advance to knockout rounds"),
    ("43%", "of WC group games end with Over 2.5 goals"),
    ("62%", "of World Cup openers are won by the home/favoured team"),
    ("3", "average corners per half in WC group stage matches"),
    ("78%", "of WC matches have a goal in the first 45 minutes"),
]

TOURNAMENT_FACTS = [
    "48 teams competing for the first time in WC history — more upsets expected than ever",
    "104 matches across USA, Canada and Mexico — biggest World Cup ever",
    "The group stage alone has more matches than entire previous World Cups",
    "6 host cities in the USA including New York, LA, Dallas, Miami, San Francisco and Seattle",
    "Argentina enter as defending champions — only 8 teams have successfully defended the WC title",
    "Brazil have never been eliminated in the group stage of a World Cup",
    "France are the only team to win the World Cup with a squad worth over €1 billion",
    "Germany have reached at least the semi-finals in 8 of the last 10 World Cups",
    "Portugal have never won the World Cup despite having one of the most decorated squads in history",
    "England last won the World Cup in 1966 — 60 years of hurt ends here?",
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
    return [m for m in MATCHES if m["date"] >= today][:n]

def days_to_wc():
    delta = datetime(2026, 6, 11, tzinfo=timezone.utc) - datetime.now(timezone.utc)
    return max(0, delta.days)

def morning():
    today_matches = get_todays_matches()
    next_matches = get_next_matches(3)
    stat_val, stat_label = random.choice(WC_STATS)
    fact = random.choice(TOURNAMENT_FACTS)

    if today_matches:
        match_lines = ""
        for m in today_matches:
            analysis = TEAM_ANALYSIS.get(m["home"], {})
            match_lines += f"\n⚽ <b>{m['home']} vs {m['away']}</b> — Group {m['group']} · {m['time']} UTC\n"
            match_lines += f"🔍 Pick: <b>{analysis.get('tip', 'Home Win')}</b>\n"
            match_lines += f"💡 {analysis.get('reason', '')}\n"
            match_lines += f"⭐ Key player: {analysis.get('key_player', '')}\n"
            match_lines += f"📊 {analysis.get('stat', '')}\n"

        return f"""🌅 <b>WC2026 MATCH DAY BRIEF</b>

{match_lines}
📊 <b>Stat of the day:</b>
<b>{stat_val}</b> — {stat_label}

📡 @WC2026signals"""

    else:
        d = days_to_wc()
        countdown = f"⏳ <b>{d} days</b> until kickoff!" if d > 0 else "🚨 The World Cup is HERE!"

        next_lines = ""
        for m in next_matches:
            next_lines += f"• <b>{m['home']} vs {m['away']}</b> — {m['date']} · Group {m['group']}\n"

        return f"""🌅 <b>WC2026 MORNING BRIEF</b>

{countdown}

📅 <b>Upcoming Fixtures:</b>
{next_lines}
🧠 <b>Did you know?</b>
{fact}

📊 <b>Key stat:</b> {stat_val} — {stat_label}

📡 @WC2026signals"""

def afternoon():
    today_matches = get_todays_matches()
    next_matches = get_next_matches(2)
    stat_val, stat_label = random.choice(WC_STATS)

    if today_matches:
        m = today_matches[0]
        analysis = TEAM_ANALYSIS.get(m["home"], {})
        home_analysis = TEAM_ANALYSIS.get(m["home"], {})
        away_analysis = TEAM_ANALYSIS.get(m["away"], {})

        return f"""⚡ <b>MATCH PREVIEW — {m['home'].upper()} vs {m['away'].upper()}</b>

🏟️ Group {m['group']} · Kickoff {m['time']} UTC

🔵 <b>{m['home']}:</b>
{home_analysis.get('reason', 'Strong contenders')}
⭐ Watch: {home_analysis.get('key_player', 'TBC')}

🔴 <b>{m['away']}:</b>
{away_analysis.get('reason', 'Dangerous opposition')}
⭐ Watch: {away_analysis.get('key_player', 'TBC')}

📊 <b>Our Analysis:</b> <b>{home_analysis.get('tip', 'Home Win')}</b>
{home_analysis.get('stat', '')}

📡 @WC2026signals"""

    else:
        match_lines = ""
        for m in next_matches:
            analysis = TEAM_ANALYSIS.get(m["home"], {})
            match_lines += f"⚽ <b>{m['home']} vs {m['away']}</b> — {m['date']}\n"
            match_lines += f"📌 {analysis.get('tip', 'Home Win')} · {analysis.get('reason', '')}\n\n"

        return f"""⚡ <b>WC2026 ANALYSIS — MIDDAY</b>

🔍 <b>Matches to analyse:</b>
{match_lines}
📊 <b>Sharp stat:</b>
<b>{stat_val}</b> — {stat_label}

📡 @WC2026signals"""

def evening():
    tomorrow_matches = get_tomorrows_matches()
    next_matches = get_next_matches(3)
    fact = random.choice(TOURNAMENT_FACTS)

    if tomorrow_matches:
        preview_lines = ""
        for m in tomorrow_matches:
            analysis = TEAM_ANALYSIS.get(m["home"], {})
            preview_lines += f"⚽ <b>{m['home']} vs {m['away']}</b> · {m['time']} UTC\n"
            preview_lines += f"📌 <b>{analysis.get('tip', 'Home Win')}</b> — {analysis.get('reason', '')}\n"
            preview_lines += f"📊 {analysis.get('stat', '')}\n\n"

        return f"""🌙 <b>TOMORROW'S PREVIEW</b>

{preview_lines}🧠 <b>Tournament insight:</b>
{fact}

📡 @WC2026signals"""

    else:
        next_lines = ""
        for m in next_matches:
            analysis = TEAM_ANALYSIS.get(m["home"], {})
            next_lines += f"⚽ <b>{m['home']} vs {m['away']}</b> — {m['date']}\n"
            next_lines += f"📌 {analysis.get('tip', 'Home Win')} · {analysis.get('key_player', '')}\n\n"

        return f"""🌙 <b>WC2026 EVENING PREVIEW</b>

📅 <b>Coming up:</b>
{next_lines}🧠 <b>Tournament fact:</b>
{fact}

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
