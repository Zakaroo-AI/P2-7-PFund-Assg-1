# data/fetch.py
import pandas as pd
import os
import yfinance as yf

def get_stock_data(ticker=None, filepath=None):
    """
    Load stock data either from a CSV file or from Yahoo Finance.
    Always returns (df, label).
    - df: pandas DataFrame with at least ['Date', 'Close'] columns
    - label: string label for the dataset (e.g., ticker symbol or filename)
    """
    if filepath:
        df = pd.read_csv(filepath)
        if "Date" not in df.columns or "Close" not in df.columns:
            raise ValueError("CSV must contain 'Date' and 'Close' columns.")
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', utc=True)
        df.sort_values("Date", inplace=True)
        label = os.path.splitext(os.path.basename(filepath))[0]
        return df, label

    elif ticker:
        # data = yf.download(ticker, progress=False)
        data = yf.Ticker(ticker).history(period = '3y')
        if data.empty:
            raise ValueError(f"No data found for ticker '{ticker}'.")
        data.reset_index(inplace=True)
        # df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # df = df.sort_values('Date')
        label = ticker.upper()
        return data, label

    else:
        raise ValueError("Either ticker or filepath must be provided.")