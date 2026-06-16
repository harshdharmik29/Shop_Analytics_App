"""
pages/5_Outlet_Comparison.py
Owner-only page: compare revenue, top items, and stock health
across all outlets side-by-side.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

from utils import (
    require_login,
    get_all_outlets,
    get_bills,
    get_bill_items_joined,
    get_items_for_outlet,
)

st.set_page_config(page_title="Outlet Comparison", page_icon="🏬", layout="wide")
require_login(st)

user = st.session_state["user"]

if user["role"] != "owner":
    st.error("🚫 This page is only accessible to the Owner.")
    st.stop()

st.title("🏬 Outlet Comparison")

outlets_df = get_all_outlets()

if outlets_df.empty or len(outlets_df) < 1:
    st.warning("No outlets found.")
    st.stop()

# ----------------------------
# Date Range Filter
# ----------------------------
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
with col2:
    end_date = st.date_input("End Date", value=date.today())

start_str = start_date.strftime("%Y-%m-%d")
end_str = end_date.strftime("%Y-%m-%d")

outlet_ids = outlets_df["outlet_id"].tolist()

bills_df = get_bills(outlet_ids=outlet_ids, start_date=start_str, end_date=end_str)
items_df = get_bill_items_joined(outlet_ids=outlet_ids, start_date=start_str, end_date=end_str)

if bills_df.empty:
    st.info("No bills found for the selected date range.")
    st.stop()

merged = bills_df.merge(outlets_df, on="outlet_id")

# ----------------------------
# Revenue Comparison
# ----------------------------
st.markdown("---")
st.subheader("💰 Revenue Comparison")

outlet_revenue = (
    merged.groupby("outlet_name")
    .agg(total_revenue=("total_amount", "sum"), total_bills=("bill_id", "count"))
    .reset_index()
)
outlet_revenue["avg_bill_value"] = outlet_revenue["total_revenue"] / outlet_revenue["total_bills"]

col_a, col_b = st.columns(2)
with col_a:
    fig_rev = px.bar(
        outlet_revenue, x="outlet_name", y="total_revenue",
        title="Total Revenue by Outlet", color="outlet_name",
        labels={"outlet_name": "Outlet", "total_revenue": "Revenue (₹)"}
    )
    st.plotly_chart(fig_rev, use_container_width=True)

with col_b:
    fig_bills = px.bar(
        outlet_revenue, x="outlet_name", y="total_bills",
        title="Total Bills by Outlet", color="outlet_name",
        labels={"outlet_name": "Outlet", "total_bills": "Number of Bills"}
    )
    st.plotly_chart(fig_bills, use_container_width=True)

st.dataframe(
    outlet_revenue.rename(columns={
        "outlet_name": "Outlet", "total_revenue": "Total Revenue (₹)",
        "total_bills": "Total Bills", "avg_bill_value": "Avg Bill Value (₹)"
    }),
    use_container_width=True, hide_index=True
)

# ----------------------------
# Daily Revenue Trend per Outlet
# ----------------------------
st.markdown("---")
st.subheader("📈 Daily Revenue Trend per Outlet")

daily_outlet = merged.groupby(["bill_date", "outlet_name"])["total_amount"].sum().reset_index()
fig_trend = px.line(
    daily_outlet, x="bill_date", y="total_amount", color="outlet_name",
    markers=True, title="Revenue Trend Comparison",
    labels={"bill_date": "Date", "total_amount": "Revenue (₹)", "outlet_name": "Outlet"}
)
st.plotly_chart(fig_trend, use_container_width=True)

# ----------------------------
# Top Items per Outlet
# ----------------------------
st.markdown("---")
st.subheader("🔥 Top Items per Outlet")

if not items_df.empty:
    items_merged = items_df.merge(outlets_df, on="outlet_id")
    for _, outlet_row in outlets_df.iterrows():
        outlet_name = outlet_row["outlet_name"]
        outlet_items = items_merged[items_merged["outlet_name"] == outlet_name]
        if not outlet_items.empty:
            top_items = (
                outlet_items.groupby("item_name")["quantity"]
                .sum().reset_index()
                .sort_values("quantity", ascending=False)
                .head(5)
            )
            with st.expander(f"🏪 {outlet_name} - Top 5 Items"):
                st.dataframe(
                    top_items.rename(columns={"item_name": "Item", "quantity": "Qty Sold"}),
                    use_container_width=True, hide_index=True
                )

# ----------------------------
# Stock Health Across Outlets
# ----------------------------
st.markdown("---")
st.subheader("📦 Stock Health Across Outlets")

for _, outlet_row in outlets_df.iterrows():
    outlet_id = int(outlet_row["outlet_id"])
    outlet_name = outlet_row["outlet_name"]
    stock_df = get_items_for_outlet(outlet_id)

    if not stock_df.empty:
        low_stock_count = len(stock_df[stock_df["current_stock"] <= stock_df["reorder_level"]])
        total_items = len(stock_df)
        col_x, col_y = st.columns([1, 3])
        with col_x:
            st.metric(f"{outlet_name}", f"{low_stock_count}/{total_items} low stock")
        with col_y:
            if low_stock_count > 0:
                low_items = stock_df[stock_df["current_stock"] <= stock_df["reorder_level"]]
                st.warning(f"Low stock items: {', '.join(low_items['item_name'].tolist())}")
            else:
                st.success("All items sufficiently stocked.")
