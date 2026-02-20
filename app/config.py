import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PRICE_FILE = os.path.join(BASE_DIR, "..", "seasonal_base_prices.csv")

URGENCY_STEPS = [
    (21, float("inf"), 1.00),
    (14, 20, 1.01),
    (7, 13, 1.02),
    (3, 6, 1.035),
    (1, 2, 1.05),
    (0, 0, 1.07)
]

EOD_DELTA = 0.015
EOD_CENTER = 20
EOD_STEEPNESS = 0.8