# ✈️ Flight Cancellation Predictor Project

## Overview
A decision-support tool that predicts flight disruption risk and recommends whether to cancel a flight based on risk, refund value, and timing.

**Use Case:**
- Flight Date: May 5
- Goal: Determine optimal cancellation timing to maximize refund while minimizing disruption risk

---

## 🧠 Core Features

### 1. Risk Prediction
- Flight delay and cancellation history
- Weather conditions (departure, arrival, route)
- Airport congestion and TSA wait times
- Government shutdown impact (staffing shortages)

### 2. Refund Optimization
- User-defined refund schedule
- Calculates best cancellation date

### 3. Decision Engine
Outputs:
- Cancellation risk (%)
- Delay risk (%)
- Recommended action
- Optimal cancellation date

---

## 💾 Data Storage (SQLite)

### Tables

#### flights
- flight_id
- departure_airport
- arrival_airport
- departure_time

#### flight_history
- flight_id
- date
- delay_minutes
- cancelled

#### weather
- airport
- date
- severity_score

#### refund_policy
- date
- refund_amount

---

## ⚙️ Architecture

```
project/
│
├── ingestion/
│   ├── flight_api.py
│   ├── weather_api.py
│
├── transformation/
│   ├── feature_engineering.py
│
├── model/
│   ├── risk_model.py
│
├── storage/
│   ├── database.py
│
├── app/
│   ├── widget.py
│
├── main.py
└── flight_predictor.db
```

---

## 🧮 Core Logic

### Risk Score
```
risk_score = (
    delay_weight * avg_delay +
    weather_weight * weather_score +
    congestion_weight * airport_score
)
```

### Decision Formula
```
expected_loss = risk_of_disruption * cost_of_bad_outcome

optimal_date = minimize(expected_loss - refund_amount)
```

---

## 🔁 Time Simulation

Loop through dates from today → flight date:

```
for date in date_range(today, flight_date):
    risk = predict_risk(date)
    refund = get_refund(date)
```

---

## 🖥️ Desktop Widget (End Goal)

### Option 1: Streamlit (Simple)
- Build UI with Streamlit
- Run locally
- Pin as browser app

### Option 2: Python Desktop App
- Use Tkinter or PyQt
- Small floating window showing:
  - Risk level
  - Refund value
  - Recommendation

### Widget Display Example
```
Flight FI614 - May 5

Risk: Medium (38%)
Refund Today: $820

Recommendation:
WAIT
Re-evaluate: April 25
```

---

## 🔄 Automation
- Schedule daily updates
- Refresh API data
- Recompute predictions

---

## 🚀 Future Enhancements
- Rebooking suggestions
- Price comparison for alternate flights
- Alerts for risk changes
- Machine learning model upgrade

---

## 🧰 Tools & Tech
- Python
- SQLite
- VS Code
- APIs (flight + weather)
- Optional: Streamlit / Tkinter

---

## 🎯 Outcome
A personal decision engine that answers:

**"Should I cancel my flight, and when is the best time to do it?"**

---

## Notes
- Start simple with rule-based scoring
- Focus on clean data modeling
- Build iteratively
- Prioritize usability (clear recommendation output)

