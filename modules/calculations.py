import pandas as pd
import numpy as np

class StockAnalytics:
    def __init__(self, stock_data: pd.DataFrame):
        self.data = stock_data

    def get_summary_statistics(self):
        return {
            "total_days": len(self.data),
            "start_price": self.data["close"].iloc[0],
            "end_price": self.data["close"].iloc[-1],
            "total_return": (self.data["close"].iloc[-1] / self.data["close"].iloc[0]) - 1
        }

    def calculate_sma(self, window):
        return self.data["close"].rolling(window=window).mean()

    def identify_runs(self):
        return (self.data["close"].diff() > 0).astype(int)

    def calculate_daily_returns(self):
        return self.data["close"].pct_change().dropna()

    def calculate_max_profit(self):
        prices = self.data["close"].values
        min_price = float("inf")
        max_profit = 0
        for price in prices:
            min_price = min(min_price, price)
            profit = price - min_price
            max_profit = max(max_profit, profit)
        return {"max_profit": max_profit, "num_transactions": 1 if max_profit > 0 else 0}
