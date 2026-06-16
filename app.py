"""
app.py
Main entry point - Login page.

Default credentials (created automatically on first run):
  Owner   -> username: admin     | password: admin123
  Manager -> username: manager1  | password: manager123 (Outlet 1 only)
"""

import streamlit as st
from database import init_db
from utils import authenticate_user, get_outlet_name

st.set_page_config(page_title="Shop Analytics - Login", page_icon="🏪", layout="centered")

# Initialize database (creates tables + seed data if first run)
init_db()

# Initialize session state
if "user" not in st.session_state:
    st.session_state["user"] = None


def login_page():
    st.title("🏪 Multi-Outlet Shop Analytics")
    st.caption("AI-powered billing, stock & revenue analytics for your outlets")

    st.markdown("---")
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        user = authenticate_user(username, password)
        if user:
            st.session_state["user"] = user
            st.success(f"Welcome, {user['username']}! Role: {user['role'].title()}")
            st.rerun()
        else:
            st.error("Invalid username or password.")

    with st.expander("Default Demo Credentials"):
        st.write("**Owner (all outlets):** admin / admin123")
        st.write("**Manager (Outlet 1 only):** manager1 / manager123")


def logged_in_view():
    user = st.session_state["user"]

    st.title("🏪 Multi-Outlet Shop Analytics")
    st.success(f"Logged in as **{user['username']}** ({user['role'].title()})")

    if user["role"] == "manager":
        st.info(f"Outlet: **{get_outlet_name(user['outlet_id'])}**")
    else:
        st.info("You have access to **all outlets** as the owner.")

    st.markdown("---")
    st.markdown(
        """
        ### 👈 Use the sidebar to navigate:
        - **Dashboard** – Daily revenue analysis & charts
        - **Billing** – Create new bills (auto stock deduction)
        - **Inventory** – Manage stock & low-stock alerts
        - **Recommendations** – Session-wise AI recommendations
        - **Outlet Comparison** – Compare outlets (Owner only)
        """
    )

    if st.button("Logout"):
        st.session_state["user"] = None
        st.rerun()


# ----------------------------
# MAIN
# ----------------------------
if st.session_state["user"] is None:
    login_page()
else:
    logged_in_view()
