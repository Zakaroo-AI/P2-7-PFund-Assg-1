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
    # hy debug
    print("✅ calculate_dailyr called")

    if "Close" not in df.columns:
        raise ValueError("DataFrame must contain a 'Close' column.")

    # Create a copy to avoid modifying the original DataFrame
    df = df.copy()

    # Compute percentage change
    df["DailyR"] = df["Close"].pct_change() * 100

    # Handle any NaN values (first row will always be NaN)
    df["DailyR"] = df["DailyR"].replace([np.inf, -np.inf], np.nan)

    return df