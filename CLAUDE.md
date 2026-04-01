# CLAUDE.md — scotland_flight

## Project Overview

**What this is:** A personal decision-support tool that answers one question:
> *Should I cancel or change flight FI614 (JFK → Reykjavik, May 5 2025) before departure?*

This is not a dashboard. It is not a monitoring tool. Every feature exists to produce a risk score that supports a pre-departure go/no-go decision.

**Data sources:**
- Flightradar24 API — historical and real-time flight data for FI614
- OpenWeatherMap API — weather conditions at JFK and KEF

**Storage:** Supabase Postgres (tables are stable — do not suggest schema changes without being asked)

**Transformation layer:** dbt-fusion (not dbt-core) — models will live in `transformation/`. This layer has not been started yet. Do not scaffold it unless explicitly asked.

---

## Folder Structure

```
SCOTLAND_FLIGHT/
├── app/                  # Application layer (TBD)
├── ingestion/
│   ├── __init__.py
│   ├── flight_api.py     # Flightradar24 API calls
│   └── weather_api.py    # OpenWeatherMap API calls
├── model/                # Risk scoring logic and prediction model
├── storage/
│   ├── __init__.py
│   └── database.py       # Supabase Postgres connection and queries
├── transformation/       # dbt-fusion models (not started)
├── main.py               # Entrypoint
├── .env                  # Secrets — never read, suggest, or print values
├── requirements.txt
└── README.md
```

---

## Risk Signal Priority Order

When reasoning about disruption risk, weight signals in this order:

1. **FAA/TSA staffing at JFK** — government shutdown impact is the highest-priority signal
2. **Weather at JFK** — departure airport conditions
3. **Weather at KEF** — destination airport conditions
4. **Historical cancellation rate for FI614** — base rate from Flightradar24
5. **Real-time flight status** — day-of confirmation only

Do not reorder or flatten these into equal-weight signals unless explicitly asked.

---

## Environment Variables

Reference these names only — never suggest hardcoding values, never print `.env` contents.

```
FLIGHTRADAR24_API_KEY
OPENWEATHERMAP_API_KEY
SUPABASE_URL
SUPABASE_SECRET_KEY
```

---

## Python Style Preferences

- Functional over class-based unless a class is clearly warranted
- Type hints on all function signatures
- No unnecessary abstractions — if it can be a function, make it a function
- Do not add logging frameworks unless asked; `print()` is fine for now
- Do not suggest new dependencies without asking first
- Fix the line I ask about — do not refactor surrounding code

---

## What Claude Should NOT Do

- Do not suggest schema changes to Supabase
- Do not scaffold `transformation/` without being asked
- Do not add libraries not in `requirements.txt` without asking
- Do not rewrite working code when a targeted fix was requested
- Do not explain what you're about to do — just do it

---

## Learning Loop

When I say **"remember this"** during a session, append a dated bullet to the `## Learned Preferences` section at the bottom of `~/.claude/CLAUDE.md`. Format:

```
- [YYYY-MM-DD] <what was learned>
```

Do not ask for confirmation. Just write it.
