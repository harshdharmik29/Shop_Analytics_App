"""
pages/1_Dashboard.py
Revenue analysis dashboard - daily revenue, top items, payment mode split.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from utils import (
    require_login,
    get_accessible_outlets,
    get_bills,
    get_bill_items_joined,
)

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
require_login(st)

user = st.session_state["user"]
st.title("📊 Revenue Dashboard")

# ----------------------------
# Outlet & Date Filters
# ----------------------------
outlets_df = get_accessible_outlets(user)

if outlets_df.empty:
    st.warning("No outlets found.")
    st.stop()

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    outlet_options = ["All Outlets"] + outlets_df["outlet_name"].tolist()
    selected_outlet = st.selectbox("Select Outlet", outlet_options)

with col2:
    start_date = st.date_input("Start Date", value=date.today() - timedelta(days=7))

with col3:
    end_date = st.date_input("End Date", value=date.today())

if selected_outlet == "All Outlets":
    outlet_ids = outlets_df["outlet_id"].tolist()
else:
    outlet_ids = outlets_df[outlets_df["outlet_name"] == selected_outlet]["outlet_id"].tolist()

start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

# ----------------------------
# Fetch Data
# ----------------------------
bills_df = get_bills(outlet_ids=outlet_ids, start_date=start_str, end_date=end_str)
items_df = get_bill_items_joined(outlet_ids=outlet_ids, start_date=start_str, end_date=end_str)

if bills_df.empty:
    st.info("No bills found for the selected filters. Generate some bills from the Billing page.")
    st.stop()

# ----------------------------
# KPI Cards
# ----------------------------
total_revenue = bills_df["total_amount"].sum()
total_bills = len(bills_df)
avg_bill_value = total_revenue / total_bills if total_bills else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
k2.metric("Total Bills", f"{total_bills}")
k3.metric("Avg Bill Value", f"₹{avg_bill_value:,.2f}")
k4.metric("Today's Revenue", f"₹{bills_df[bills_df['bill_date'] == date.today().strftime('%Y-%m-%d')]['total_amount'].sum():,.2f}")

st.markdown("---")

# ----------------------------
# Daily Revenue Trend
# ----------------------------
st.subheader("📈 Daily Revenue Trend")
daily_revenue = bills_df.groupby("bill_date")["total_amount"].sum().reset_index()
daily_revenue = daily_revenue.sort_values("bill_date")

fig_trend = px.line(
    daily_revenue, x="bill_date", y="total_amount",
    markers=True, title="Revenue Over Time",
    labels={"bill_date": "Date", "total_amount": "Revenue (₹)"}
)
st.plotly_chart(fig_trend, use_container_width=True)

# ----------------------------
# Revenue by Outlet (only if "All Outlets")
# ----------------------------
if selected_outlet == "All Outlets" and len(outlet_ids) > 1:
    st.subheader("🏬 Revenue by Outlet")
    merged = bills_df.merge(outlets_df, on="outlet_id")
    outlet_revenue = merged.groupby("outlet_name")["total_amount"].sum().reset_index()
    fig_outlet = px.bar(
        outlet_revenue, x="outlet_name", y="total_amount",
        title="Revenue Comparison by Outlet", color="outlet_name",
        labels={"outlet_name": "Outlet", "total_amount": "Revenue (₹)"}
    )
    st.plotly_chart(fig_outlet, use_container_width=True)

# ----------------------------
# Top Selling Items
# ----------------------------
st.subheader("🔥 Top Selling Items")
if not items_df.empty:
    top_items = (
        items_df.groupby("item_name")
        .agg(total_qty=("quantity", "sum"), total_sales=("subtotal", "sum"))
        .reset_index()
        .sort_values("total_sales", ascending=False)
        .head(10)
    )
    fig_items = px.bar(
        top_items, x="item_name", y="total_sales",
        title="Top 10 Items by Sales Value", color="item_name",
        labels={"item_name": "Item", "total_sales": "Sales Value (₹)"}
    )
    st.plotly_chart(fig_items, use_container_width=True)
    st.dataframe(top_items, use_container_width=True, hide_index=True)
else:
    st.info("No item-level data available yet.")

# ----------------------------
# Payment Mode Split
# ----------------------------
st.subheader("💳 Payment Mode Split")
payment_split = bills_df.groupby("payment_mode")["total_amount"].sum().reset_index()
fig_payment = px.pie(
    payment_split, names="payment_mode", values="total_amount",
    title="Revenue Share by Payment Mode"
)
st.plotly_chart(fig_payment, use_container_width=True)
