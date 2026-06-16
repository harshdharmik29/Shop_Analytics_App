"""
ml/session_analysis.py
Session-wise analysis: groups bills by time-of-day "session"
(Morning / Afternoon / Evening / Night) and finds top-selling
items per session, so the app can recommend what to stock
ready for each session.
"""

import pandas as pd


def get_session(hour: int) -> str:
    """Map an hour (0-23) to a named session/shift."""
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"


def add_session_column(items_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a 'session' column to a bill_items_joined DataFrame based on
    the bill_time column (format HH:MM:SS).
    """
    if items_df.empty:
        items_df["session"] = []
        return items_df

    df = items_df.copy()
    df["hour"] = pd.to_datetime(df["bill_time"], format="%H:%M:%S").dt.hour
    df["session"] = df["hour"].apply(get_session)
    return df


def top_items_by_session(items_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: session, item_name, total_qty, total_sales
    showing the top_n items for each session, sorted by quantity sold.
    """
    if items_df.empty:
        return pd.DataFrame(columns=["session", "item_name", "total_qty", "total_sales"])

    df = add_session_column(items_df)

    grouped = (
        df.groupby(["session", "item_name"])
        .agg(total_qty=("quantity", "sum"), total_sales=("subtotal", "sum"))
        .reset_index()
    )

    # Get top_n per session
    result = (
        grouped.groupby("session", group_keys=False)
        .apply(lambda x: x.sort_values("total_qty", ascending=False).head(top_n))
        .reset_index(drop=True)
    )
    return result


def stock_recommendations(items_df: pd.DataFrame, current_stock_df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """
    Combine session-wise top sellers with current stock levels to flag
    items that are high-demand but running low.

    current_stock_df must have columns: item_name, current_stock, reorder_level
    """
    top_items = top_items_by_session(items_df, top_n=top_n)
    if top_items.empty:
        return top_items

    merged = top_items.merge(
        current_stock_df[["item_name", "current_stock", "reorder_level"]],
        on="item_name", how="left"
    )

    merged["recommendation"] = merged.apply(
        lambda row: "🔴 Restock Soon - High Demand" if row["current_stock"] <= row["reorder_level"]
        else "🟢 Stock OK",
        axis=1
    )

    return merged.sort_values(["session", "total_qty"], ascending=[True, False])
