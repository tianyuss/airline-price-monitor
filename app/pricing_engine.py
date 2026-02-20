import pandas as pd
from datetime import datetime
import math
from app.config import BASE_PRICE_FILE, URGENCY_STEPS, EOD_DELTA, EOD_CENTER, EOD_STEEPNESS

df = pd.read_csv(BASE_PRICE_FILE)

def get_base_price(origin, destination, departure_date):
    row = df[
        (df["origin"] == origin) &
        (df["destination"] == destination) &
        (df["date"] == departure_date)
    ]
    if row.empty:
        raise ValueError("Price not found")
    return int(row.iloc[0]["base_price_idr"])

def get_urgency_multiplier(days_before):
    for min_days, max_days, multiplier in URGENCY_STEPS:
        if min_days <= days_before <= max_days:
            return multiplier
    return 1.0

def get_intraday_multiplier(days_before):
    if days_before != 0:
        return 1.0

    current_hour = datetime.now().hour
    logistic = 1 / (1 + math.exp(-EOD_STEEPNESS * (current_hour - EOD_CENTER)))
    return 1 + (EOD_DELTA * logistic)

def simulate_price(origin, destination, departure_date, purchase_date):

    departure = datetime.strptime(departure_date, "%Y-%m-%d")
    purchase = datetime.strptime(purchase_date, "%Y-%m-%d")

    days_before = (departure - purchase).days
    if days_before < 0:
        raise ValueError("Invalid dates")

    base_price = get_base_price(origin, destination, departure_date)

    urgency = get_urgency_multiplier(days_before)
    intraday = get_intraday_multiplier(days_before)

    combined_multiplier = urgency * intraday

    final_price = int(base_price * combined_multiplier)

    return {
        "base_price": base_price,
        "days_before_departure": days_before,
        "multiplier": round(combined_multiplier, 4),
        "final_price": final_price
    }