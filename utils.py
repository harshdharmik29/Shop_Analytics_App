"""
utils.py
Helper functions used across the app: authentication, common DB queries,
and small calculation helpers.
"""

import pandas as pd
from datetime import datetime
from database import get_connection, hash_password


# ----------------------------
# AUTHENTICATION
# ----------------------------
def authenticate_user(username: str, password: str):
    """
    Check username/password against the users table.
    Returns a dict with user info if valid, else None.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT user_id, username, role, outlet_id FROM users "
        "WHERE username = ? AND password_hash = ?",
        (username, hash_password(password)),
    )
    row = cur.fetchone()
    conn.close()

    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "role": row[2],
            "outlet_id": row[3],
        }
    return None


def is_logged_in(st):
    """Return True if a user is logged in via session_state."""
    return st.session_state.get("user") is not None


def require_login(st):
    """
    Use at the top of every page. Stops execution and shows a
    message if the user is not logged in.
    """
    if not is_logged_in(st):
        st.warning("Please login first from the main page (app.py).")
        st.stop()


# ----------------------------
# OUTLET HELPERS
# ----------------------------
def get_all_outlets():
    """Return all outlets as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM outlets", conn)
    conn.close()
    return df


def get_outlet_name(outlet_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT outlet_name FROM outlets WHERE outlet_id = ?", (outlet_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else "Unknown Outlet"


def get_accessible_outlets(user):
    """
    Owner -> all outlets.
    Manager -> only their own outlet.
    Returns DataFrame with outlet_id, outlet_name.
    """
    if user["role"] == "owner":
        return get_all_outlets()
    else:
        conn = get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM outlets WHERE outlet_id = ?", conn, params=(user["outlet_id"],)
        )
        conn.close()
        return df


# ----------------------------
# ITEM / STOCK HELPERS
# ----------------------------
def get_items_for_outlet(outlet_id):
    """Return all items for a given outlet as a DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM items WHERE outlet_id = ? ORDER BY item_name", conn, params=(outlet_id,)
    )
    conn.close()
    return df


def update_stock(item_id, quantity_sold):
    """Reduce stock for an item by quantity_sold."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE items SET current_stock = current_stock - ? WHERE item_id = ?",
        (quantity_sold, item_id),
    )
    conn.commit()
    conn.close()


def add_item(outlet_id, item_name, category, price, current_stock, reorder_level):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO items (outlet_id, item_name, category, price, current_stock, reorder_level) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (outlet_id, item_name, category, price, current_stock, reorder_level),
    )
    conn.commit()
    conn.close()


def restock_item(item_id, add_quantity):
    """Increase stock for an item by add_quantity."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE items SET current_stock = current_stock + ? WHERE item_id = ?",
        (add_quantity, item_id),
    )
    conn.commit()
    conn.close()


# ----------------------------
# BILLING HELPERS
# ----------------------------
def create_bill(outlet_id, cart_items, payment_mode):
    """
    cart_items: list of dicts -> {item_id, item_name, quantity, price}
    Saves a bill, its line items, and reduces stock.
    Returns the new bill_id and total amount.
    """
    conn = get_connection()
    cur = conn.cursor()

    total_amount = sum(ci["quantity"] * ci["price"] for ci in cart_items)
    now = datetime.now()

    cur.execute(
        "INSERT INTO bills (outlet_id, bill_date, bill_time, total_amount, payment_mode) "
        "VALUES (?, ?, ?, ?, ?)",
        (outlet_id, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"), total_amount, payment_mode),
    )
    bill_id = cur.lastrowid

    for ci in cart_items:
        subtotal = ci["quantity"] * ci["price"]
        cur.execute(
            "INSERT INTO bill_items (bill_id, item_id, quantity, price_at_sale, subtotal) "
            "VALUES (?, ?, ?, ?, ?)",
            (bill_id, ci["item_id"], ci["quantity"], ci["price"], subtotal),
        )
        # Reduce stock
        cur.execute(
            "UPDATE items SET current_stock = current_stock - ? WHERE item_id = ?",
            (ci["quantity"], ci["item_id"]),
        )

    conn.commit()
    conn.close()
    return bill_id, total_amount


def get_bill_details(bill_id):
    """Return bill header + line items for printing/invoice."""
    conn = get_connection()
    bill = pd.read_sql_query("SELECT * FROM bills WHERE bill_id = ?", conn, params=(bill_id,))
    items = pd.read_sql_query(
        """
        SELECT bi.quantity, bi.price_at_sale, bi.subtotal, i.item_name
        FROM bill_items bi
        JOIN items i ON bi.item_id = i.item_id
        WHERE bi.bill_id = ?
        """,
        conn,
        params=(bill_id,),
    )
    conn.close()
    return bill, items


# ----------------------------
# REVENUE / ANALYTICS HELPERS
# ----------------------------
def get_bills(outlet_ids=None, start_date=None, end_date=None):
    """
    Return bills as a DataFrame, optionally filtered by a list of
    outlet_ids and a date range (YYYY-MM-DD strings).
    """
    conn = get_connection()
    query = "SELECT * FROM bills WHERE 1=1"
    params = []

    if outlet_ids:
        placeholders = ",".join(["?"] * len(outlet_ids))
        query += f" AND outlet_id IN ({placeholders})"
        params.extend(outlet_ids)

    if start_date:
        query += " AND bill_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND bill_date <= ?"
        params.append(end_date)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_bill_items_joined(outlet_ids=None, start_date=None, end_date=None):
    """
    Return a joined DataFrame of bill_items + bills + items for
    deeper analysis (top items, session analysis, forecasting).
    """
    conn = get_connection()
    query = """
        SELECT b.bill_id, b.outlet_id, b.bill_date, b.bill_time, b.payment_mode,
               bi.item_id, bi.quantity, bi.price_at_sale, bi.subtotal,
               i.item_name, i.category
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.bill_id
        JOIN items i ON bi.item_id = i.item_id
        WHERE 1=1
    """
    params = []

    if outlet_ids:
        placeholders = ",".join(["?"] * len(outlet_ids))
        query += f" AND b.outlet_id IN ({placeholders})"
        params.extend(outlet_ids)

    if start_date:
        query += " AND b.bill_date >= ?"
        params.append(start_date)

    if end_date:
        query += " AND b.bill_date <= ?"
        params.append(end_date)

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
