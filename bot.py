
import os
import sys
from datetime import datetime, timezone

import requests

TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# Only high-impact (red folder) events for these currencies
CURRENCIES = {"USD"}
IMPACTS = {"High"}

# Warn when an event is between 10 and 15 minutes away.
# The workflow runs every 5 minutes, so each event is warned about once.
WARN_MIN = 10
WARN_MAX = 15

# Simple gold rules (keyword in event title -> note)
GOLD_HINTS = {
    "CPI": "Higher than forecast = USD up, GOLD DOWN. Lower = gold up.",
    "PCE": "Higher than forecast = USD up, GOLD DOWN. Lower = gold up.",
    "Non-Farm": "Stronger jobs = USD up, GOLD DOWN. Weaker = gold up.",
    "Unemployment Rate": "Higher rate = weaker economy, GOLD UP. Lower = gold down.",
    "Unemployment Claims": "Higher claims = GOLD UP. Lower = gold down.",
    "Federal Funds Rate": "Hawkish tone = GOLD DOWN. Dovish tone = gold up.",
    "FOMC": "Hawkish tone = GOLD DOWN. Dovish tone = gold up.",
    "Powell": "Hawkish words = GOLD DOWN. Dovish words = gold up.",
    "GDP": "Stronger than forecast = USD up, GOLD DOWN.",
    "Retail Sales": "Stronger than forecast = USD up, GOLD DOWN.",
    "ISM": "Stronger than forecast = USD up, GOLD DOWN.",
    "PMI": "Stronger than forecast = USD up, GOLD DOWN.",
}


def send(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=20,
    )
    r.raise_for_status()


def gold_hint(title):
    for key, note in GOLD_HINTS.items():
        if key.lower() in title.lower():
            return note
    return "Check actual vs forecast. Stronger USD data usually pressures gold."


def main():
    if os.getenv("TEST_MODE") == "true" or (len(sys.argv) > 1 and sys.argv[1] == "test"):
        send("Bot connected. Economic calendar alerts are ready.")
        return

    resp = requests.get(CALENDAR_URL, timeout=30)
    resp.raise_for_status()
    events = resp.json()
    now = datetime.now(timezone.utc)

    for ev in events:
        if ev.get("country") not in CURRENCIES or ev.get("impact") not in IMPACTS:
            continue
        when = datetime.fromisoformat(ev["date"])
        minutes = (when - now).total_seconds() / 60
        if not (WARN_MIN < minutes <= WARN_MAX):
            continue

        msg = (
            f"RED FOLDER in ~{int(minutes)} min\n"
            f"{ev['country']} - {ev['title']}\n"
            f"Forecast: {ev.get('forecast') or 'n/a'} | Previous: {ev.get('previous') or 'n/a'}\n\n"
            f"Gold view: {gold_hint(ev['title'])}\n"
            f"Tip: avoid new trades right before the release. First 1-5 min can fake out."
        )
        send(msg)


if __name__ == "__main__":
    main()
