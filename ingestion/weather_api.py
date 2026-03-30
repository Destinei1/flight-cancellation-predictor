# First make sure to import libraries being used

import requests # Helps us call the API
import json  # Helps us read and parse JSON Data
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env", override=True)

OPENWEATHER_API = os.getenv("OPENWEATHER_API")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

#the two airports that we care about 
# ICAO code → (city name, country code)
AIRPORTS = {
    "KJFK": ("New York",    "US"),
    "BIKF": ("Reykjavik",   "IS"),
}

# ============================================================
# FUNCTION 1: get_weather_by_airport()
# Pulls current weather for one airport using city + country.
# Returns a clean dict with just the fields we need.
# ============================================================
def get_weather_by_airport(icao_code):
 
    # Look up the city and country for this airport code
    if icao_code not in AIRPORTS:
        print(f"Unknown airport: {icao_code}")
        return None
 
    city, country = AIRPORTS[icao_code]
    print(f"Fetching weather for {icao_code} ({city}, {country})...")
 
    # Build the request — q=city,country tells OWM where we want
    # units=imperial gives us Fahrenheit
    url = f"{BASE_URL}?q={city},{country}&appid={OPENWEATHER_API}&units=imperial"
 
    response = requests.get(url)
    response.raise_for_status()
 
    # Parse the JSON response into a Python dictionary
    data = response.json()
 
    # Pull out only what the risk model needs
    return {
        "airport":      icao_code,
        "city":         data.get("name"),
        "temp_f":       data["main"]["temp"],           # current temp in °F
        "feels_like_f": data["main"]["feels_like"],     # feels like temp
        "humidity_pct": data["main"]["humidity"],       # humidity %
        "wind_mph":     data["wind"]["speed"],          # wind speed
        "description":  data["weather"][0]["description"],  # e.g. "light snow"
        "severity_score": _compute_severity(data),      # 0-10 risk score
        "fetched_at":   datetime.now().isoformat(),
    }

# ============================================================
# FUNCTION 2: get_weather_for_route()
# Pulls weather for both JFK and BIKF in one call.
# This is what the risk model will actually use.
# ============================================================
def get_weather_for_route():
    print("Fetching weather for full JFK → BIKF route...\n")
 
    departure = get_weather_by_airport("KJFK")
    arrival   = get_weather_by_airport("BIKF")
 
    return {
        "departure": departure,
        "arrival":   arrival,
    }


# ============================================================
# HELPER: _compute_severity()
# Converts raw weather data into a single 0-10 severity score.
# Higher = worse conditions = higher flight risk.
#
# This is rule-based for now — we can tune weights later.
# ============================================================
def _compute_severity(data):
    score = 0
 
    wind_mph  = data["wind"]["speed"]
    humidity  = data["main"]["humidity"]
    condition = data["weather"][0]["main"].lower()  # e.g. "snow", "rain"
 
    # Wind scoring — strong winds cause the most delays
    if wind_mph > 40:
        score += 4
    elif wind_mph > 25:
        score += 2
    elif wind_mph > 15:
        score += 1
 
    # Weather condition scoring
    if "thunderstorm" in condition:
        score += 4
    elif "snow" in condition:
        score += 3
    elif "rain" in condition:
        score += 2
    elif "fog" in condition or "mist" in condition:
        score += 2
    elif "cloud" in condition:
        score += 1
 
    # High humidity adds minor risk
    if humidity > 90:
        score += 1
 
    # Cap at 10
    return min(score, 10)
 
 
# ============================================================
# QUICK TEST — run with: python ingestion/weather_api.py
# ============================================================
if __name__ == "__main__":
    import json
 
    print("\n" + "="*50)
    print("TEST 1: JFK Weather")
    print("="*50)
    jfk = get_weather_by_airport("KJFK")
    print(json.dumps(jfk, indent=2))
 
    print("\n" + "="*50)
    print("TEST 2: BIKF Weather")
    print("="*50)
    bikf = get_weather_by_airport("BIKF")
    print(json.dumps(bikf, indent=2))
 
    print("\n" + "="*50)
    print("TEST 3: Full Route")
    print("="*50)
    route = get_weather_for_route()
    print(f"JFK severity score:  {route['departure']['severity_score']}/10")
    print(f"BIKF severity score: {route['arrival']['severity_score']}/10")