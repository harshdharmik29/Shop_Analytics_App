"""
ml/demand_forecast.py
Simple demand forecasting using a moving-average / linear-trend
approach with scikit-learn's LinearRegression. Good enough for an
MVP - predicts next-day expected quantity sold per item.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


def daily_item_sales(items_df: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot bill_items_joined data into daily quantity sold per item.
    Returns DataFrame: bill_date, item_name, quantity
    """
    if items_df.empty:
        return pd.DataFrame(columns=["bill_date", "item_name", "quantity"])

    daily = (
        items_df.groupby(["bill_date", "item_name"])["quantity"]
        .sum()
        .reset_index()
    )
    return daily


def forecast_next_day(items_df: pd.DataFrame, min_days: int = 3) -> pd.DataFrame:
    """
    For each item, fit a simple linear regression on
    (day_index -> quantity_sold) and predict the next day's demand.

    If an item has fewer than `min_days` of history, fall back to
    its average daily quantity.

    Returns DataFrame: item_name, predicted_qty, avg_qty, data_points
    """
    daily = daily_item_sales(items_df)

    if daily.empty:
        return pd.DataFrame(columns=["item_name", "predicted_qty", "avg_qty", "data_points"])

    results = []

    for item_name, group in daily.groupby("item_name"):
        group = group.sort_values("bill_date").reset_index(drop=True)
        n = len(group)
        avg_qty = group["quantity"].mean()

        if n < min_days:
            predicted = round(avg_qty, 1)
        else:
            X = np.arange(n).reshape(-1, 1)
            y = group["quantity"].values
            model = LinearRegression()
            model.fit(X, y)
            next_day_index = np.array([[n]])
            pred = model.predict(next_day_index)[0]
            # Avoid negative predictions
            predicted = round(max(pred, 0), 1)

        results.append({
            "item_name": item_name,
            "predicted_qty": predicted,
            "avg_qty": round(avg_qty, 1),
            "data_points": n
        })

    result_df = pd.DataFrame(results)
    return result_df.sort_values("predicted_qty", ascending=False).reset_index(drop=True)


def items_to_restock(forecast_df: pd.DataFrame, current_stock_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compare predicted next-day demand vs current stock to flag items
    that may run out.

    current_stock_df must have columns: item_name, current_stock, reorder_level
    """
    if forecast_df.empty:
        return pd.DataFrame()

    merged = forecast_df.merge(
        current_stock_df[["item_name", "current_stock", "reorder_level"]],
        on="item_name", how="left"
    )

    merged["status"] = merged.apply(
        lambda row: "⚠️ May run out tomorrow"
        if row["current_stock"] < row["predicted_qty"]
        else "✅ Sufficient stock",
        axis=1
    )

    return merged.sort_values("predicted_qty", ascending=False)
