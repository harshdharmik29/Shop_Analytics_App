"""
pages/3_Inventory.py
Inventory management - view stock, low-stock alerts, add new items, restock.
"""

import streamlit as st
import pandas as pd

from utils import (
    require_login,
    get_accessible_outlets,
    get_items_for_outlet,
    add_item,
    restock_item,
)

st.set_page_config(page_title="Inventory", page_icon="📦", layout="wide")
require_login(st)

user = st.session_state["user"]
st.title("📦 Inventory Management")

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

items_df = get_items_for_outlet(outlet_id)

# ----------------------------
# Low Stock Alerts
# ----------------------------
st.markdown("---")
st.subheader("⚠️ Low Stock Alerts")

if not items_df.empty:
    low_stock = items_df[items_df["current_stock"] <= items_df["reorder_level"]]
    if not low_stock.empty:
        st.error(f"{len(low_stock)} item(s) need restocking!")
        st.dataframe(
            low_stock.rename(columns={
                "item_name": "Item", "category": "Category",
                "current_stock": "Current Stock", "reorder_level": "Reorder Level"
            })[["Item", "Category", "Current Stock", "Reorder Level"]],
            use_container_width=True, hide_index=True
        )
    else:
        st.success("All items are sufficiently stocked. ✅")
else:
    st.info("No items added yet for this outlet.")

# ----------------------------
# Current Stock Table
# ----------------------------
st.markdown("---")
st.subheader("📋 Current Stock")

if not items_df.empty:
    st.dataframe(
        items_df.rename(columns={
            "item_name": "Item", "category": "Category", "price": "Price (₹)",
            "current_stock": "Current Stock", "reorder_level": "Reorder Level"
        })[["item_id", "Item", "Category", "Price (₹)", "Current Stock", "Reorder Level"]],
        use_container_width=True, hide_index=True
    )

# ----------------------------
# Restock Existing Item
# ----------------------------
st.markdown("---")
st.subheader("🔄 Restock Item")

if not items_df.empty:
    with st.form("restock_form"):
        item_choice = st.selectbox("Select Item", items_df["item_name"].tolist())
        add_qty = st.number_input("Quantity to Add", min_value=1, value=10)
        restock_submitted = st.form_submit_button("Restock")

    if restock_submitted:
        item_id = int(items_df[items_df["item_name"] == item_choice]["item_id"].iloc[0])
        restock_item(item_id, add_qty)
        st.success(f"Added {add_qty} units to {item_choice}.")
        st.rerun()

# ----------------------------
# Add New Item
# ----------------------------
st.markdown("---")
st.subheader("➕ Add New Item")

with st.form("add_item_form"):
    col1, col2 = st.columns(2)
    with col1:
        new_item_name = st.text_input("Item Name")
        new_category = st.text_input("Category")
    with col2:
        new_price = st.number_input("Price (₹)", min_value=0.0, step=0.5)
        new_stock = st.number_input("Initial Stock", min_value=0, step=1)
        new_reorder = st.number_input("Reorder Level", min_value=0, step=1, value=10)

    add_submitted = st.form_submit_button("Add Item")

if add_submitted:
    if not new_item_name.strip():
        st.error("Item name cannot be empty.")
    else:
        add_item(outlet_id, new_item_name.strip(), new_category.strip(), new_price, new_stock, new_reorder)
        st.success(f"Item '{new_item_name}' added successfully.")
        st.rerun()
