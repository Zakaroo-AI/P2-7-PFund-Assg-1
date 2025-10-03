import yfinance as yf
import pandas as pd

def get_stock_data(ticker=None, filepath=None):
    if ticker:
        df = yf.download(ticker, period="1y")  # default: last year
        df.reset_index(inplace=True)
    elif filepath:
        df = pd.read_csv(filepath, parse_dates=["Date"])
    else:
        raise ValueError("Must provide either ticker or filepath.")
    
    # Ensure consistent column names
    df = df.rename(columns=str.title)
    return df[["Date", "Open", "High", "Low", "Close", "Volume"]]
