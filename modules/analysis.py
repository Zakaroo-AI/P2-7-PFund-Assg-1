import pandas as pd

class StockAnalysis:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

        # Detect column names dynamically
        self.close_col = self._get_col("close")
        self.open_col = self._get_col("open")
        self.high_col = self._get_col("high")
        self.low_col = self._get_col("low")
        self.volume_col = self._get_col("volume")

    def _get_col(self, keyword: str) -> str:
        """Finds the first column containing the keyword."""
        for col in self.df.columns:
            if keyword in col:
                return col
        raise KeyError(f"No column found for {keyword}")

    # 1. Simple Moving Average
    def get_sma(self, window=5):
        self.df["SMA"] = self.df[self.close_col].rolling(window=window).mean()
        return {
            "dates": self.df["date"].astype(str).tolist(),
            "close": self.df[self.close_col].round(2).tolist(),
            "sma": self.df["SMA"].round(2).fillna(0).tolist()
        }

    # 2. Runs (upward/downward streaks)
    def get_runs(self):
        changes = self.df[self.close_col].diff().fillna(0)
        runs = []
        streak = 0
        for ch in changes:
            if ch > 0:
                streak = streak + 1 if streak > 0 else 1
            elif ch < 0:
                streak = streak - 1 if streak < 0 else -1
            else:
                streak = 0
            runs.append(streak)

        return {
            "dates": self.df["date"].astype(str).tolist(),
            "runs": runs,
            "prices": self.df[self.close_col].round(2).tolist()
        }

    # 3. Daily Returns
    def get_returns(self):
        self.df["returns"] = self.df[self.close_col].pct_change().fillna(0)
        return {
            "dates": self.df["date"].astype(str).tolist(),
            "returns": (self.df["returns"] * 100).round(2).tolist()
        }

    # 4. Max Profit (Best Time to Buy and Sell Stock II)
    def get_max_profit(self):
        prices = self.df[self.close_col].tolist()
        profit = 0
        transactions = []
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                profit += prices[i] - prices[i - 1]
                transactions.append({
                    "buy": prices[i - 1],
                    "sell": prices[i],
                    "profit": round(prices[i] - prices[i - 1], 2)
                })
        return {"max_profit": round(profit, 2), "transactions": transactions}

