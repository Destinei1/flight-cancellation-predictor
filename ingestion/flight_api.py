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

# ── Step 1: Load your secret keys from the .env file ────────
# This reads FR24_API_KEY, FLIGHT_NUMBER, FLIGHT_DATE
# so we never hardcode secrets in the code itself
load_dotenv()

API_KEY       = os.getenv("FR24_API_KEY")       # your Flightradar24 key
FLIGHT_NUMBER = os.getenv("FLIGHT_NUMBER", "FI614")     # default: FI614
FLIGHT_DATE   = os.getenv("FLIGHT_DATE",   "2025-05-05") # default: May 5


# ── Step 2: Set up the "header" we send with every request ──
# Think of this like showing your ID badge before entering a building.
# FR24 checks this on every single call to confirm you're allowed in.
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",  # your key goes here
    "Accept-Version": "v1",                # tells FR24 which API version to use
}

# The base URL for all FR24 API calls
BASE_URL = "https://fr24api.flightradar24.com"


# ============================================================
# FUNCTION 1: get_flight_summary()
#
# Asks FR24: "What happened on flight FI614 on a specific date?"
# Returns one dictionary with all the details of that flight.
#
# When to call it: Once per day as May 5 approaches.
# ============================================================
def get_flight_summary(flight_number=FLIGHT_NUMBER, flight_date=FLIGHT_DATE):

    print(f"Fetching summary for {flight_number} on {flight_date}...")

    # Build the URL we are calling
    # This is like typing a web address into your browser
    url = f"{BASE_URL}/api/v1/flight-summary/full"

    # These are the "search filters" we send along with the request
    # FR24 uses these to know which flight we want
    params = {
        "flights":              flight_number,  # e.g. "FI614"
        "flight_datetime_from": flight_date,    # e.g. "2025-05-05"
        "flight_datetime_to":   flight_date,    # same date = just that one day
    }

    # Make the actual call to FR24
    # requests.get() is like opening a URL — it returns the response
    response = requests.get(url, headers=HEADERS, params=params)

    # If FR24 returns an error (e.g. bad key, no credits), stop and show it
    response.raise_for_status()

    # Convert the response from raw text into a Python dictionary
    data = response.json()

    # FR24 returns a list called "data" — we want the first item
    flights = data.get("data", [])

    # If nothing came back, say so
    if not flights:
        print(f"No data found for {flight_number} on {flight_date}")
        return None

    # Grab the first (and usually only) result
    flight = flights[0]

    # Pull out only the fields we care about and return them cleanly
    # This is our "clean row" that will go into the database later
    return {
        "fr24_id":     flight.get("fr24_id"),           # FR24's internal ID
        "flight":      flight.get("flight"),            # "FI614"
        "origin":      flight.get("orig_icao"),         # departure airport code
        "destination": flight.get("dest_icao_actual")   # arrival airport code
                       or flight.get("dest_icao"),
        "departed_at": flight.get("datetime_takeoff"),  # actual takeoff time
        "arrived_at":  flight.get("datetime_landed"),   # actual landing time
        "aircraft":    flight.get("type"),              # plane model e.g. "B738"
        "tail_number": flight.get("reg"),               # plane's registration
        "flight_ended": flight.get("flight_ended"),     # did it complete?
        "fetched_at":  datetime.utcnow().isoformat(),   # when WE pulled this
    }


# ============================================================
# FUNCTION 2: get_flight_history()
#
# Asks FR24: "How has FI614 performed over the last 30 days?"
# Returns a LIST of dictionaries — one per past flight.
#
# When to call it: Once at setup, then weekly.
# This builds the delay pattern used in the risk score.
# ============================================================
def get_flight_history(flight_number=FLIGHT_NUMBER, flight_date=FLIGHT_DATE, lookback_days=30):

    # Figure out the date range
    # Example: if flight_date = May 5, then:
    #   date_from = April 5
    #   date_to   = May 4  (we stop before the target date)
    target    = datetime.strptime(flight_date, "%Y-%m-%d")
    date_from = (target - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    date_to   = (target - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Fetching {lookback_days} days of history for {flight_number}...")
    print(f"Date range: {date_from} to {date_to}")

    url = f"{BASE_URL}/api/v1/flight-summary/full"

    params = {
        "flights":              flight_number,
        "flight_datetime_from": date_from,
        "flight_datetime_to":   date_to,
    }

    response = requests.get(url, headers=HEADERS, params=params)
    response.raise_for_status()

    data    = response.json()
    flights = data.get("data", [])

    if not flights:
        print(f"No history found for {flight_number}")
        return []

    print(f"Found {len(flights)} past flights for {flight_number}")

    # Loop through every past flight and build a clean list
    results = []
    for flight in flights:

        # Was this flight cancelled?
        # A flight is cancelled if it never took off (no takeoff time)
        was_cancelled = flight.get("datetime_takeoff") is None

        results.append({
            "fr24_id":      flight.get("fr24_id"),
            "flight":       flight.get("flight"),
            "date":         flight.get("datetime_takeoff", "")[:10],  # just YYYY-MM-DD
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
# QUICK TEST
#
# When you run this file directly with:
#   python ingestion/flight_api.py
#
# It will print the results to your screen so you can
# inspect what FR24 actually returns before storing anything.
# ============================================================
if __name__ == "__main__":
    import json

    print("\n" + "="*50)
    print("TEST 1: Flight Summary for May 5")
    print("="*50)
    summary = get_flight_summary()
    print(json.dumps(summary, indent=2))  # pretty-print the dictionary

    print("\n" + "="*50)
    print("TEST 2: Last 30 Days of FI614 History")
    print("="*50)
    history = get_flight_history()
    print(f"Total records returned: {len(history)}")
    if history:
        print("Most recent record:")
        print(json.dumps(history[0], indent=2))