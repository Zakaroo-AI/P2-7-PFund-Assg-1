import os
import matplotlib
matplotlib.use('Agg') # headless backend
import matplotlib.pyplot as plt




def plot_close_prices(dfs, labels, indicators=None, save_path=None, figsize=(12,6)):
    """
    Plot close prices for a list of DataFrames. Optionally overlay indicator columns (list of column names).


    - dfs: list of pd.DataFrame (each must contain 'Date' and 'Close')
    - labels: list of labels same length as dfs
    - indicators: list of column names (strings) to try to plot if present
    - save_path: if provided, saves the figure to that path and returns the path
    """
    plt.figure(figsize=figsize)


    for df, label in zip(dfs, labels):
        plt.plot(df['Date'], df['Close'], label=f'{label} Close')
        # if indicators:
        #     for ind in indicators:
        #         if ind in df.columns:

        for df, label in zip(dfs, labels):
            if "Close" in df.columns:
                plt.plot(df.index, df["Close"], label=f"{label} Close")
            if "SMA" in df.columns:
                plt.plot(df.index, df["SMA"], linestyle="--", label=f"{label} SMA")
            if "EMA" in df.columns:
                plt.plot(df.index, df["EMA"], linestyle="--", label=f"{label} EMA")
            if "RSI" in df.columns:
                # RSI usually goes on separate axis, but placeholder here
                plt.plot(df.index, df["RSI"], label=f"{label} RSI")
            if "MACD" in df.columns:
                plt.plot(df.index, df["MACD"], label=f"{label} MACD")

        plt.title("Stock Prices & Indicators")
        plt.xlabel("Date")
        plt.ylabel("Price")
        plt.legend()
        plt.tight_layout()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        plt.close()
        return save_path