"""
pages/4_Recommendations.py
AI-powered recommendations:
  1. Session-wise top-selling items (Morning/Afternoon/Evening/Night)
  2. Next-day demand forecast per item with restock alerts
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from utils import (
    require_login,
    get_accessible_outlets,
    get_items_for_outlet,
    get_bill_items_joined,
)
from ml.session_analysis import top_items_by_session, stock_recommendations
from ml.demand_forecast import forecast_next_day, items_to_restock

st.set_page_config(page_title="Recommendations", page_icon="🤖", layout="wide")
require_login(st)

user = st.session_state["user"]
st.title("🤖 AI Recommendations")
st.caption("Session-wise top sellers & next-day demand forecast to help you plan stock.")

# ----------------------------
# Outlet Selection
# ----------------------------
outlets_df = get_accessible_outlets(user)

if outlets_df.empty:
    st.warning("No outlets found.")
    st.stop()

if user["role"] == "owner":
    outlet_name = st.selectbox("Select Outlet", outlets_df["outlet_name"].tolist())
    outlet_id = int(outlets_df[outlets_df["outlet_name"] == outlet_name]["outlet_id"].iloc[0])
else:
    outlet_id = user["outlet_id"]
    outlet_name = outlets_df["outlet_name"].iloc[0]
    st.info(f"Outlet: **{outlet_name}**")

# Look back over last 30 days by default for recommendations
start_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
end_date = date.today().strftime("%Y-%m-%d")

items_joined = get_bill_items_joined(outlet_ids=[outlet_id], start_date=start_date, end_date=end_date)
current_stock_df = get_items_for_outlet(outlet_id)

if items_joined.empty:
    st.info("Not enough billing history yet. Generate some bills first to see recommendations.")
    st.stop()

# ----------------------------
# Session-wise Top Items
# ----------------------------
st.markdown("---")
st.subheader("🕐 Session-wise Top Sellers (Last 30 Days)")
st.caption("Morning: 5AM-12PM | Afternoon: 12PM-5PM | Evening: 5PM-9PM | Night: 9PM-5AM")

session_top = top_items_by_session(items_joined, top_n=5)

if not session_top.empty:
    for session_name in ["Morning", "Afternoon", "Evening", "Night"]:
        session_data = session_top[session_top["session"] == session_name]
        if not session_data.empty:
            with st.expander(f"📍 {session_name} - Top Items", expanded=True):
                fig = px.bar(
                    session_data, x="item_name", y="total_qty",
                    title=f"{session_name}: Top Items by Quantity Sold",
                    labels={"item_name": "Item", "total_qty": "Quantity Sold"},
                    color="item_name"
                )
                st.plotly_chart(fig, use_container_width=True)
                st.dataframe(
                    session_data.rename(columns={
                        "item_name": "Item", "total_qty": "Qty Sold", "total_sales": "Sales (₹)"
                    })[["Item", "Qty Sold", "Sales (₹)"]],
                    use_container_width=True, hide_index=True
                )

# ----------------------------
# Stock Recommendations based on Session Demand
# ----------------------------
st.markdown("---")
st.subheader("📦 Session-Based Stock Recommendations")

stock_recs = stock_recommendations(items_joined, current_stock_df, top_n=5)
if not stock_recs.empty:
    st.dataframe(
        stock_recs.rename(columns={
            "session": "Session", "item_name": "Item", "total_qty": "Avg Qty Sold (30 days)",
            "current_stock": "Current Stock", "recommendation": "Recommendation"
        })[["Session", "Item", "Avg Qty Sold (30 days)", "Current Stock", "Recommendation"]],
        use_container_width=True, hide_index=True
    )

# ----------------------------
# Next-Day Demand Forecast
# ----------------------------
st.markdown("---")
st.subheader("🔮 Next-Day Demand Forecast")
st.caption("Based on recent sales trend (linear regression on daily quantities).")

forecast_df = forecast_next_day(items_joined)

if not forecast_df.empty:
    fig_forecast = px.bar(
        forecast_df.head(10), x="item_name", y="predicted_qty",
        title="Predicted Quantity Needed Tomorrow (Top 10 Items)",
        labels={"item_name": "Item", "predicted_qty": "Predicted Qty"},
        color="item_name"
    )
    st.plotly_chart(fig_forecast, use_container_width=True)

    restock_alerts = items_to_restock(forecast_df, current_stock_df)
    st.dataframe(
        restock_alerts.rename(columns={
            "item_name": "Item", "predicted_qty": "Predicted Demand (Tomorrow)",
            "avg_qty": "Avg Daily Demand", "current_stock": "Current Stock",
            "status": "Status"
        })[["Item", "Predicted Demand (Tomorrow)", "Avg Daily Demand", "Current Stock", "Status"]],
        use_container_width=True, hide_index=True
    )
else:
    st.info("Not enough data yet to generate a forecast.")
