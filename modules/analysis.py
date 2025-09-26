import pandas as pd

class StockAnalysis:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        if "Date" in self.df.columns:
            self.df["Date"] = pd.to_datetime(self.df["Date"])

    def get_sma(self, window=5):
        self.df["SMA"] = self.df["Close"].rolling(window=window).mean()
        return {
            "dates": self.df["Date"].dt.strftime("%Y-%m-%d").tolist(),
            "close": self.df["Close"].round(2).tolist(),
            "sma": self.df["SMA"].round(2).fillna(0).tolist()
        }

    def get_runs(self):
        self.df["Change"] = self.df["Close"].diff()
        self.df["Run"] = self.df["Change"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        return {
            "dates": self.df["Date"].dt.strftime("%Y-%m-%d").tolist(),
            "runs": self.df["Run"].tolist()
        }

    def get_returns(self):
        self.df["Return"] = self.df["Close"].pct_change() * 100
        self.df.dropna(inplace=True)
        return {
            "dates": self.df["Date"].dt.strftime("%Y-%m-%d").tolist(),
            "returns": self.df["Return"].round(2).tolist()
        }

    def get_profit(self):
        prices = self.df["Close"].tolist()
        profit = 0
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                profit += prices[i] - prices[i - 1]
        return {"profit": round(profit, 2)}
