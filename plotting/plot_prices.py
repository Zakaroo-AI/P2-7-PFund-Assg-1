import matplotlib.pyplot as plt

def plot_close_prices(dfs, labels, indicators=None):
    plt.figure(figsize=(10,6))
    for df, label in zip(dfs, labels):
        plt.plot(df["Date"], df["Close"], label=f"{label} Close")
        if indicators:
            for ind in indicators:
                if ind in df.columns:
                    plt.plot(df["Date"], df[ind], label=f"{label} {ind}")
    
    plt.legend()
    plt.title("Stock Prices & Indicators")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.show()
