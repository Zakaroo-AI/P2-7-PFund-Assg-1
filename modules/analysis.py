import pandas as pd
import numpy as np

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
        close_values = self.df[self.close_col]
        window_sum = close_values.iloc[:window].sum()
        rolling_sma = [np.nan] * (window - 1) + [window_sum / window]

        for i in range(window, close_values.size):
            window_sum += close_values.iloc[i] - close_values.iloc[i - window]
            rolling_sma.append(window_sum / window)
        
        self.df["SMA"] = rolling_sma
        # sanity_list = [100] * len(rolling_sma)
        # self.df["SMA"] = sanity_list

        return {
            "dates": self.df["date"].astype(str).tolist(),
            "close": self.df[self.close_col].round(2).tolist(),
            "sma": self.df["SMA"].round(2).fillna(0).tolist()
        }

    def get_ema(self, interval = 10, smoothing = 2.0, starting_index = 0):
        close_values = self.df[self.close_col].iloc[starting_index:]
        weight = smoothing / (interval + 1)     # weighting more recent entries is greater for shorter intervals
        sma = close_values.iloc[:interval].sum() / interval    # using sma as an initial state, afterwards we can implement EMA
        
        #return rolling_ema should figure out why interval must minus one
        rolling_ema = [np.nan] * (interval-1) + [sma]
        #rolling_ema = [sma]

        for i in range(interval, close_values.size):
            ema = close_values.iloc[i] * weight + rolling_ema[-1] * (1 - weight)
            rolling_ema.append(ema)

        self.df["EMA"] = rolling_ema

        return {
            "dates": self.df["date"].astype(str).tolist(),
            "close": self.df[self.close_col].round(2).tolist(),
            "ema": self.df["EMA"].round(2).fillna(0).tolist()
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

    def get_rsi(self, interval = 14):
        close_values = self.df[self.close_col]
        differences = close_values[1:].values - close_values.values[:-1] # contains length - 1 elements

        gains, losses = 0, 0

        for i in differences[:interval]:
            gains += max(i, 0)     # if i is positive, use i else use 0
            losses += max(-i, 0)   # if i is negative, use i else use 0
        
        avg_gain = gains / interval
        avg_loss = losses / interval
        if avg_loss == 0:
            rsi = 100
        else:
            rsi = 100 - 100/(1 + avg_gain / avg_loss)

        rsi_values = [np.nan] * interval + [rsi]

        # we use smoothing as it counters having a period of no losses, which may cause avg_loss to be 0, causing divide by zero error
        # as long as there is one entry > 0, it will never divide by zero (if there is none, we use rsi = 100)
        for i in differences[interval:]:
            # obvious thing to do here is to loop thru differences every time, but we can use sliding window here again
            # use remainder as index?
            avg_gain = (avg_gain * (interval - 1) + max(i, 0)) / interval # i-1 because differences has one less entry than truncated
            avg_loss = (avg_loss * (interval - 1) + max(-i, 0)) / interval

            if avg_loss == 0:
                rsi = 100
            else:
                rsi = 100 - 100/(1 + avg_gain/avg_loss)

            rsi_values.append(rsi)
    
        self.df["RSI"] = rsi_values

        return {
            "dates": self.df["date"].astype(str).tolist(),
            "rsi": self.df["RSI"].round(2).fillna(50).tolist()  #fillna with 50 because 50 is the baseline value, 0 is an extreme
        }
    
    def get_macd(self, fast_period = 12, slow_period = 26, signal_period = 9):


        ema_fast = self.get_ema(interval = fast_period)
        ema_slow = self.get_ema(interval = slow_period)
        
        # ema_fast = talib.EMA(data, timeperiod = fast_period)
        # ema_slow = talib.EMA(data, timeperiod = slow_period)
        # macd_line = np.array(aligned_fast) - np.array(aligned_slow)
        macd_line = pd.Series(ema_fast["ema"]) - pd.Series(ema_slow["ema"])
        #signal_line = exponentialMovingAverage(macd_line, signal_period)
        first_non_nan = macd_line.first_valid_index()
        # print('first index:', first_non_nan)
        # print('length:', macd_line.size)
        #signal_line_vals = exponentialMovingAverage(macd_line[first_non_nan:], signal_period)
        signal_line_vals = self.get_ema(signal_period, starting_index = first_non_nan)
        signal_line = [np.nan] * first_non_nan + signal_line_vals["ema"]
        histogram = macd_line - signal_line

        return {
            "dates": self.df["date"].astype(str).tolist(),
            "macd": macd_line.astype(str).tolist(),
            "signal": signal_line,
            "histogram": histogram.astype(str).tolist()
        }