import pandas as pd
import numpy as np

def calculate_dailyr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the daily percentage returns from the 'Close' price.

    Args:
        df (pd.DataFrame): DataFrame containing at least a 'Close' column.

    Returns:
        pd.DataFrame: Original DataFrame with an added 'DailyR' column (in percent).
    """

    if "Close" not in df.columns:
        raise ValueError("DataFrame must contain a 'Close' column.")

    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()

    # Compute percentage change
    df["DailyR"] = df["Close"].pct_change() * 100

    # Handle any NaN values (first row will always be NaN)
    df["DailyR"] = df["DailyR"].replace([np.inf, -np.inf], np.nan)

    # --- 💰 Max Profit logic ---
    try:
        min_idx = df["Close"].idxmin()
        max_idx_after_min = df["Close"].iloc[min_idx:].idxmax()

        df["Buy_Date"] = df.loc[min_idx, "Date"]
        df["Sell_Date"] = df.loc[max_idx_after_min, "Date"]
        df["Buy_Price"] = df.loc[min_idx, "Close"]
        df["Sell_Price"] = df.loc[max_idx_after_min, "Close"]
        df["Price_Diff"] = df["Sell_Price"] - df["Buy_Price"]
        df["Max_Profit_Pct"] = ((df["Sell_Price"] - df["Buy_Price"]) / df["Buy_Price"]) * 100
    except Exception:
        df["Buy_Date"] = pd.NaT
        df["Sell_Date"] = pd.NaT
        df["Buy_Price"] = None
        df["Sell_Price"] = None
        df["Price_Diff"] = 0
        df["Max_Profit_Pct"] = 0

    return df