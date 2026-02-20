import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import timedelta
from app.pricing_engine import simulate_price
from app.config import BASE_PRICE_FILE


# ------------------------
# Page Config
# ------------------------

st.set_page_config(
    page_title="Airline Price Monitor",
    layout="centered"
)

GREEN = "#00ff88"


# ------------------------
# Load Data
# ------------------------

df = pd.read_csv(BASE_PRICE_FILE)

routes = df[["origin", "destination"]].drop_duplicates()
route_options = routes.apply(
    lambda x: f"{x['origin']} → {x['destination']}", axis=1
).tolist()

st.title("Airline Price Monitoring & Simulation")

st.caption(
    "This simulation uses historical scraped base prices. "
    "Realtime market prices may vary depending on airline inventory and demand."
)


# ------------------------
# Route Selection
# ------------------------

selected_route = st.selectbox("Select Route", route_options)
origin, destination = selected_route.split(" → ")

route_df = df[
    (df["origin"] == origin) &
    (df["destination"] == destination)
].sort_values("date")

available_dates = pd.to_datetime(route_df["date"]).dt.date.unique()
earliest_date = min(available_dates)
latest_date = max(available_dates)


# ------------------------
# Date Inputs
# ------------------------

col1, col2 = st.columns(2)

with col1:
    departure_date = st.date_input(
        "Departure Date",
        min_value=earliest_date,
        max_value=latest_date
    )

with col2:
    purchase_date = st.date_input(
        "Purchase Date",
        min_value=earliest_date,
        max_value=departure_date
    )


# ------------------------
# Forms
# ------------------------

with st.form("simulation_form"):
    simulate_btn = st.form_submit_button("Simulate Price")

with st.form("validation_form"):
    realtime_price = st.number_input(
        "Enter Realtime Observed Price (IDR)",
        min_value=0,
        step=1000
    )
    submit_validation = st.form_submit_button("Validate Price")


# ------------------------
# Simulation Logic
# ------------------------

if simulate_btn or submit_validation:

    departure_str = departure_date.strftime("%Y-%m-%d")
    purchase_str = purchase_date.strftime("%Y-%m-%d")

    result = simulate_price(origin, destination, departure_str, purchase_str)

    st.divider()
    st.subheader("Simulation Result")

    st.write(
        f"Base Price (scraped on 20 Feb 2026): "
        f"Rp {result['base_price']:,}"
    )

    st.caption(
        "Base price represents historical scraped fare used as structural input "
        "for multiplier-based price simulation."
    )

    st.write(f"Days Before Departure: {result['days_before_departure']}")
    st.write(f"Applied Multiplier: {result['multiplier']:.4f}")

    st.markdown("### Final Simulated Price")
    st.markdown(
        f"<h1 style='color:{GREEN}; font-weight:700;'>Rp {result['final_price']:,}</h1>",
        unsafe_allow_html=True
    )

    # H-0 comparison
    h0_price = simulate_price(
        origin,
        destination,
        departure_str,
        departure_str
    )["final_price"]

    if purchase_date != departure_date:
        diff = ((h0_price - result["final_price"]) / h0_price) * 100
        st.write(f"Difference vs H-0: {diff:.2f}%")

    # ------------------------
    # Price Evolution Window
    # ------------------------

    window_dates = []
    prices = []

    current = purchase_date
    while current <= departure_date:
        sim = simulate_price(
            origin,
            destination,
            departure_str,
            current.strftime("%Y-%m-%d")
        )
        window_dates.append(current)
        prices.append(sim["final_price"])
        current += timedelta(days=1)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=window_dates,
            y=prices,
            mode="lines",
            line=dict(color=GREEN, width=3),
            name="Simulated Price"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[purchase_date],
            y=[result["final_price"]],
            mode="markers",
            marker=dict(size=10, color=GREEN),
            name="Selected Purchase Date"
        )
    )

    fig.update_layout(
        title="Price Evolution Until Departure",
        xaxis_title="Purchase Date",
        yaxis_title="Simulated Price (IDR)",
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=20),
        height=450,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # ------------------------
    # Validation
    # ------------------------

    if submit_validation and realtime_price > 0:

        implied_multiplier = realtime_price / result["base_price"]
        deviation = (
            (implied_multiplier - result["multiplier"])
            / result["multiplier"]
        ) * 100

        st.divider()
        st.subheader("Validation Result")

        st.write(f"Implied Realtime Multiplier: {implied_multiplier:.4f}")
        st.write(f"Deviation vs Model: {deviation:.2f}%")

        st.caption(
            "Deviation vs Model measures the percentage difference between "
            "the realtime observed multiplier (derived from market price) "
            "and the model's calculated multiplier. "
            "Values closer to 0% indicate stronger alignment with observed market pricing."
        )


# ------------------------
# Footer
# ------------------------

st.markdown(
    "<div style='position: fixed; bottom: 12px; left: 20px; "
    "font-size: 11px; color: rgba(255,255,255,0.25);'>"
    "Airline Pricing Simulation Model | a portfolio by tianyus"
    "</div>",
    unsafe_allow_html=True
)
