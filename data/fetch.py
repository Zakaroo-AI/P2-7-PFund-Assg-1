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
    if ticker:
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