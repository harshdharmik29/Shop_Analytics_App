"""
pages/2_Billing.py
Bill entry page - add items to a cart, generate a bill, auto-deduct stock.
"""

import streamlit as st
import pandas as pd

from utils import (
    require_login,
    get_accessible_outlets,
    get_items_for_outlet,
    create_bill,
    get_bill_details,
)

st.set_page_config(page_title="Billing", page_icon="🧾", layout="wide")
require_login(st)

user = st.session_state["user"]
st.title("🧾 New Bill")

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

# ----------------------------
# Cart in session state
# ----------------------------
cart_key = f"cart_{outlet_id}"
if cart_key not in st.session_state:
    st.session_state[cart_key] = []

items_df = get_items_for_outlet(outlet_id)

if items_df.empty:
    st.warning("No items found for this outlet. Add items from the Inventory page.")
    st.stop()

st.markdown("---")
st.subheader("Add Item to Bill")

col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    item_choice = st.selectbox(
        "Select Item",
        items_df["item_name"] + " (Stock: " + items_df["current_stock"].astype(str) + ")"
    )
    selected_item_name = item_choice.split(" (Stock:")[0]
    item_row = items_df[items_df["item_name"] == selected_item_name].iloc[0]

with col2:
    qty = st.number_input("Quantity", min_value=1, max_value=int(item_row["current_stock"]) if item_row["current_stock"] > 0 else 1, value=1)

with col3:
    st.write("")
    st.write("")
    add_clicked = st.button("➕ Add to Cart")

if add_clicked:
    if item_row["current_stock"] <= 0:
        st.error(f"{selected_item_name} is out of stock!")
    elif qty > item_row["current_stock"]:
        st.error(f"Only {item_row['current_stock']} units of {selected_item_name} available.")
    else:
        st.session_state[cart_key].append({
            "item_id": int(item_row["item_id"]),
            "item_name": item_row["item_name"],
            "quantity": int(qty),
            "price": float(item_row["price"]),
        })
        st.success(f"Added {qty} x {selected_item_name} to cart.")
        st.rerun()

# ----------------------------
# Cart Display
# ----------------------------
st.markdown("---")
st.subheader("🛒 Current Bill")

cart = st.session_state[cart_key]

if not cart:
    st.info("Cart is empty. Add items above.")
else:
    cart_df = pd.DataFrame(cart)
    cart_df["subtotal"] = cart_df["quantity"] * cart_df["price"]
    st.dataframe(
        cart_df.rename(columns={
            "item_name": "Item", "quantity": "Qty",
            "price": "Price (₹)", "subtotal": "Subtotal (₹)"
        })[["Item", "Qty", "Price (₹)", "Subtotal (₹)"]],
        use_container_width=True, hide_index=True
    )

    total = cart_df["subtotal"].sum()
    st.markdown(f"### Total: ₹{total:,.2f}")

    col_a, col_b = st.columns(2)
    with col_a:
        payment_mode = st.selectbox("Payment Mode", ["Cash", "UPI", "Card", "Credit"])
    with col_b:
        st.write("")
        st.write("")
        clear_clicked = st.button("🗑️ Clear Cart")

    if clear_clicked:
        st.session_state[cart_key] = []
        st.rerun()

    if st.button("✅ Generate Bill", type="primary"):
        bill_id, total_amount = create_bill(outlet_id, cart, payment_mode)
        st.session_state[cart_key] = []
        st.session_state["last_bill_id"] = bill_id
        st.success(f"Bill #{bill_id} generated successfully! Total: ₹{total_amount:,.2f}")
        st.rerun()

# ----------------------------
# Last Generated Bill (Invoice View)
# ----------------------------
if "last_bill_id" in st.session_state and st.session_state["last_bill_id"]:
    st.markdown("---")
    st.subheader("🧾 Last Invoice")

    bill_header, bill_items = get_bill_details(st.session_state["last_bill_id"])

    if not bill_header.empty:
        b = bill_header.iloc[0]
        st.write(f"**Bill ID:** {b['bill_id']}  |  **Date:** {b['bill_date']}  |  **Time:** {b['bill_time']}")
        st.write(f"**Payment Mode:** {b['payment_mode']}")
        st.dataframe(
            bill_items.rename(columns={
                "item_name": "Item", "quantity": "Qty",
                "price_at_sale": "Price (₹)", "subtotal": "Subtotal (₹)"
            })[["Item", "Qty", "Price (₹)", "Subtotal (₹)"]],
            use_container_width=True, hide_index=True
        )
        st.write(f"**Grand Total: ₹{b['total_amount']:,.2f}**")
