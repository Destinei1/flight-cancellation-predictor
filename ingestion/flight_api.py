# ============================================================
# ingestion/flight_api.py
#
# What this file does:
#   - Calls the Flightradar24 API (like ordering from a menu)
#   - Asks for info about flight FI614
#   - Returns that info as a Python dictionary (like a row in a table)
#
# How to run it for testing:
#   python ingestion/flight_api.py
# ============================================================

import os                          # reads your .env variables
import requests                    # makes HTTP calls to the API (like a browser would)
from datetime import datetime, timedelta
from dotenv import load_dotenv     # loads your .env file into Python
from pathlib import Path

# ── Step 1: Load your secret keys from the .env file ────────
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

API_KEY       = os.getenv("FR24_API_KEY")
FLIGHT_NUMBER = os.getenv("FLIGHT_NUMBER", "FI614")
FLIGHT_DATE   = os.getenv("FLIGHT_DATE") or "2026-05-05"

# ── Step 2: Headers sent with every request (your ID badge) ──
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Accept-Version": "v1",
}

BASE_URL = "https://fr24api.flightradar24.com"


# ============================================================
# FUNCTION 1: get_flight_summary()
# Asks FR24: "What happened on FI614 on a specific date?"
# Call once per day as May 5 approaches.
# ============================================================
def get_flight_summary(flight_number=FLIGHT_NUMBER, flight_date=FLIGHT_DATE):

    print(f"Fetching summary for {flight_number} on {flight_date}...")

    # URL built manually so colons don't get encoded to %3A
    url = (
        f"{BASE_URL}/api/flight-summary/full"
        f"?flights={flight_number}"
        f"&flight_datetime_from={flight_date}T00:00:00"
        f"&flight_datetime_to={flight_date}T23:59:59"
    )

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    data    = response.json()
    flights = data.get("data", [])

    if not flights:
        print(f"No data found for {flight_number} on {flight_date}")
        return None

    flight = flights[0]

    return {
        "fr24_id":      flight.get("fr24_id"),
        "flight":       flight.get("flight"),
        "origin":       flight.get("orig_icao"),
        "destination":  flight.get("dest_icao_actual") or flight.get("dest_icao"),
        "departed_at":  flight.get("datetime_takeoff"),
        "arrived_at":   flight.get("datetime_landed"),
        "aircraft":     flight.get("type"),
        "tail_number":  flight.get("reg"),
        "flight_ended": flight.get("flight_ended"),
        "fetched_at":   datetime.utcnow().isoformat(),
    }


# ============================================================
# FUNCTION 2: get_flight_history()
# Asks FR24: "How has FI614 performed over the last 30 days?"
# Call once at setup, then weekly.
# ============================================================
def get_flight_history(flight_number=FLIGHT_NUMBER, flight_date=FLIGHT_DATE, lookback_days=3):

    target    = datetime.strptime(flight_date, "%Y-%m-%d")
    date_from = (target - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    date_to   = (target - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Fetching {lookback_days} days of history for {flight_number}...")
    print(f"Date range: {date_from} to {date_to}")

    # URL built manually so colons don't get encoded to %3A
    url = (
        f"{BASE_URL}/api/flight-summary/full"
        f"?flights={flight_number}"
        f"&flight_datetime_from={date_from}T00:00:00"
        f"&flight_datetime_to={date_to}T23:59:59"
    )

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    data    = response.json()
    flights = data.get("data", [])

    if not flights:
        print(f"No history found for {flight_number}")
        return []

    print(f"Found {len(flights)} past flights for {flight_number}")

    results = []
    for flight in flights:
        was_cancelled = flight.get("datetime_takeoff") is None
        results.append({
            "fr24_id":      flight.get("fr24_id"),
            "flight":       flight.get("flight"),
            "date":         flight.get("datetime_takeoff", "")[:10],
            "origin":       flight.get("orig_icao"),
            "destination":  flight.get("dest_icao_actual") or flight.get("dest_icao"),
            "departed_at":  flight.get("datetime_takeoff"),
            "arrived_at":   flight.get("datetime_landed"),
            "aircraft":     flight.get("type"),
            "cancelled":    was_cancelled,
            "fetched_at":   datetime.utcnow().isoformat(),
        })

    return results


# ============================================================
# QUICK TEST — run with: python ingestion/flight_api.py
# ============================================================
if __name__ == "__main__":
    import json

    print("\n" + "="*50)
    print("TEST 1: Flight Summary for May 5")
    print("="*50)
    summary = get_flight_summary()
    print(json.dumps(summary, indent=2))

    print("\n" + "="*50)
    print("TEST 2: Last 7 Days of FI614 History")
    print("="*50)
    history = get_flight_history()
    print(f"Total records returned: {len(history)}")
    if history:
        print("Most recent record:")
        print(json.dumps(history[0], indent=2))