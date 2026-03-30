# ============================================================
# storage/database.py
#
# What this file does:
#   - Creates tables in Supabase (if they don't exist)
#   - Saves flight and weather data into those tables
#   - Uses UPSERT so re-running never creates duplicate rows
#
# DATA FLOW — data must arrive in this order:
#   1. flight_history  ← from flight_api.get_flight_history()
#   2. flights         ← from flight_api.get_flight_summary()
#   3. weather         ← from weather_api.get_weather_for_route()
#   4. refund_policy   ← manually entered by you once
#
# How to run it for testing:
#   python storage/database.py
# ============================================================

import os
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client, Client

# Load secrets from .env in project root
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

SUPABASE_URL        = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

# Create the Supabase client — this is our database connection
# Think of it like opening a connection to your database
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


# ============================================================
# GROUP 1 — FLIGHT HISTORY
# Source: flight_api.get_flight_history()
# Purpose: Stores past FI614 flights to build delay patterns
#
# Must arrive FIRST — the risk model needs this history
# to compute avg_delay before evaluating the target flight.
#
# Unique key: fr24_id (FR24's internal ID per flight instance)
# Upsert: if fr24_id exists, update it — never duplicate
# ============================================================
def save_flight_history(records: list[dict]):
    if not records:
        print("No flight history records to save.")
        return

    print(f"Saving {len(records)} flight history records...")

    for record in records:
        # Clean the record — only keep columns that match our table
        row = {
            "fr24_id":      record.get("fr24_id"),       # FR24 unique flight ID
            "flight":       record.get("flight"),         # e.g. "FI614"
            "date":         record.get("date"),           # YYYY-MM-DD
            "origin":       record.get("origin"),         # departure airport ICAO
            "destination":  record.get("destination"),    # arrival airport ICAO
            "departed_at":  record.get("departed_at"),    # actual takeoff time
            "arrived_at":   record.get("arrived_at"),     # actual landing time
            "aircraft":     record.get("aircraft"),       # plane model
            "cancelled":    record.get("cancelled"),      # True/False
            "fetched_at":   record.get("fetched_at"),     # when we pulled this
        }

        # Upsert = insert if new, update if fr24_id already exists
        supabase.table("flight_history") \
            .upsert(row, on_conflict="fr24_id") \
            .execute()

    print("Flight history saved. ✅")


# ============================================================
# GROUP 2 — FLIGHT SUMMARY (TARGET FLIGHT)
# Source: flight_api.get_flight_summary()
# Purpose: Stores the specific FI614 May 5 flight details
#
# Must arrive SECOND — depends on history already being loaded
# so the risk model has a baseline to compare against.
#
# Unique key: fr24_id
# ============================================================
def save_flight_summary(record: dict):
    if not record:
        print("No flight summary to save.")
        return

    print(f"Saving flight summary for {record.get('flight')}...")

    row = {
        "fr24_id":      record.get("fr24_id"),       # FR24 unique flight ID
        "flight":       record.get("flight"),         # "FI614"
        "origin":       record.get("origin"),         # "KJFK"
        "destination":  record.get("destination"),    # "BIKF"
        "departed_at":  record.get("departed_at"),    # actual takeoff
        "arrived_at":   record.get("arrived_at"),     # actual landing
        "aircraft":     record.get("aircraft"),       # plane model
        "tail_number":  record.get("tail_number"),    # plane registration
        "flight_ended": record.get("flight_ended"),   # did it complete?
        "fetched_at":   record.get("fetched_at"),     # when we pulled this
    }

    supabase.table("flights") \
        .upsert(row, on_conflict="fr24_id") \
        .execute()

    print("Flight summary saved. ✅")


# ============================================================
# GROUP 3 — WEATHER
# Source: weather_api.get_weather_for_route()
# Purpose: Stores current weather for JFK and BIKF
#
# Must arrive THIRD — weather is a risk input alongside
# flight history. Both are needed before running the model.
#
# Unique key: airport + date combination
# ============================================================
def save_weather(record: dict):
    if not record:
        print("No weather record to save.")
        return

    print(f"Saving weather for {record.get('airport')}...")

    row = {
        "airport":        record.get("airport"),        # "KJFK" or "BIKF"
        "city":           record.get("city"),           # "New York"
        "date":           datetime.now().strftime("%Y-%m-%d"),  # today's date
        "temp_f":         record.get("temp_f"),         # current temp °F
        "feels_like_f":   record.get("feels_like_f"),   # feels like °F
        "humidity_pct":   record.get("humidity_pct"),   # humidity %
        "wind_mph":       record.get("wind_mph"),        # wind speed
        "description":    record.get("description"),    # e.g. "light snow"
        "severity_score": record.get("severity_score"), # 0-10 risk score
        "fetched_at":     record.get("fetched_at"),     # when we pulled this
    }

    # Upsert on airport + date so we get one row per airport per day
    supabase.table("weather") \
        .upsert(row, on_conflict="airport,date") \
        .execute()

    print(f"Weather for {record.get('airport')} saved. ✅")


def save_weather_for_route(route: dict):
    # route comes from weather_api.get_weather_for_route()
    # which returns {"departure": {...}, "arrival": {...}}
    if route.get("departure"):
        save_weather(route["departure"])
    if route.get("arrival"):
        save_weather(route["arrival"])


# ============================================================
# GROUP 4 — REFUND POLICY
# Source: manually entered by you
# Purpose: Stores your refund schedule so the model knows
#          how much money you recover on each cancellation date
#
# Must arrive FOURTH — the decision engine needs this to
#          compute optimal_date = minimize(expected_loss - refund)
#
# Unique key: date
# ============================================================
def save_refund_policy(records: list[dict]):
    # Each record should look like:
    # {"date": "2025-04-01", "refund_amount": 820, "notes": "Full refund"}
    if not records:
        print("No refund policy records to save.")
        return

    print(f"Saving {len(records)} refund policy records...")

    for record in records:
        row = {
            "date":          record.get("date"),          # cancellation date
            "refund_amount": record.get("refund_amount"), # $ you get back
            "notes":         record.get("notes", ""),     # optional label
        }

        supabase.table("refund_policy") \
            .upsert(row, on_conflict="date") \
            .execute()

    print("Refund policy saved. ✅")


# ============================================================
# QUICK TEST — run with: python storage/database.py
# Tests the connection and confirms tables are reachable
# ============================================================
if __name__ == "__main__":

    print("\n" + "="*50)
    print("TEST: Supabase Connection")
    print("="*50)

    try:
        # Try to read from each table — confirms they exist
        # You must create these tables in Supabase first (see SQL below)
        tables = ["flights", "flight_history", "weather", "refund_policy"]

        for table in tables:
            result = supabase.table(table).select("*").limit(1).execute()
            print(f"✅ {table} — reachable")

        print("\nAll tables reachable. Database is ready.")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("Make sure SUPABASE_URL and SUPABASE_SECRET_KEY are set in .env")
