import pandas as pd
import numpy as np

def calculate_dailyr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate daily percentage returns and the maximum achievable profit window.

    Adds the following columns:
    ----------------------------
    - DailyR          : Daily return in percent (%)
    - Buy_Date        : Optimal buy date for max profit
    - Sell_Date       : Optimal sell date for max profit
    - Buy_Price       : Buy price at Buy_Date
    - Sell_Price      : Sell price at Sell_Date
    - Price_Diff      : Absolute profit in dollars ($)
    - Max_Profit_Pct  : Profit percentage relative to buy price (%)
    """

    if "Close" not in df.columns:
        raise ValueError("DataFrame must contain a 'Close' column.")

    df = df.copy()
    df["DailyR"] = df["Close"].pct_change() * 100
    df["DailyR"] = df["DailyR"].replace([np.inf, -np.inf], np.nan)

    # --- 💰 Max Profit (single trade) ---
    try:
        prices = df["Close"].values
        dates = df["Date"].values

        if len(prices) < 2:
            raise ValueError("Not enough data to compute max profit.")

        min_price = prices[0]
        min_date = dates[0]
        max_profit = 0
        buy_date = sell_date = min_date
        buy_price = sell_price = min_price

        for i in range(1, len(prices)):
            profit = prices[i] - min_price
            if profit > max_profit:
                max_profit = profit
                buy_date = min_date
                sell_date = dates[i]
                buy_price = min_price
                sell_price = prices[i]
            if prices[i] < min_price:
                min_price = prices[i]
                min_date = dates[i]

        df["Buy_Date"] = buy_date
        df["Sell_Date"] = sell_date
        df["Buy_Price"] = buy_price
        df["Sell_Price"] = sell_price
        df["Price_Diff"] = max_profit
        df["Max_Profit_Pct"] = (max_profit / buy_price * 100) if buy_price > 0 else 0

    except Exception:
        df["Buy_Date"] = pd.NaT
        df["Sell_Date"] = pd.NaT
        df["Buy_Price"] = None
        df["Sell_Price"] = None
        df["Price_Diff"] = 0
        df["Max_Profit_Pct"] = 0

    return df