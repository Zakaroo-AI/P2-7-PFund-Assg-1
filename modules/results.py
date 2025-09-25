import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt
import io
import base64

class StockResults:
    def _plot_to_html(self, fig):
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")
        plt.close(fig)
        return f"<img src='data:image/png;base64,{encoded}'/>"

    def plot_sma(self, data, symbol):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(data["date"], data["close"], label="Close Price")
        ax.plot(data["date"], data["sma"], label="SMA (20)")
        ax.set_title(f"{symbol} - Simple Moving Average")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price ($)")
        ax.legend()
        return self._plot_to_html(fig)

    def plot_returns(self, data, symbol):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(data["date"], data["daily_return"], label="Daily Return")
        ax.set_title(f"{symbol} - Daily Returns")
        ax.set_xlabel("Date")
        ax.set_ylabel("Return")
        ax.legend()
        return self._plot_to_html(fig)

    def plot_profit(self, data, symbol):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(data["date"], data["cumulative_return"], label="Cumulative Return")
        ax.set_title(f"{symbol} - Cumulative Profit")
        ax.set_xlabel("Date")
        ax.set_ylabel("Growth")
        ax.legend()
        return self._plot_to_html(fig)
