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
        df["Date"] = pd.to_datetime(df["Date"])
        df.sort_values("Date", inplace=True)
        label = os.path.splitext(os.path.basename(filepath))[0]
        return df, label

    elif ticker:
        data = yf.download(ticker, progress=False)
        if data.empty:
            raise ValueError(f"No data found for ticker '{ticker}'.")
        data.reset_index(inplace=True)
        label = ticker.upper()
        return data, label

    else:
        raise ValueError("Either ticker or filepath must be provided.")





# def get_stock_data(ticker=None, filepath=None, period='1y', start=None, end=None):
#     """
#     Returns a standardized DataFrame with columns: Date, Open, High, Low, Close, Adj Close, Volume
#     Provide either ticker (string) or filepath (CSV) but not both.
#     """
#     if filepath:
#         df = pd.read_csv(filepath, parse_dates=['Date'])
#     elif ticker:
#         try:
#             import yfinance as yf
#         except Exception as e:
#             raise RuntimeError('yfinance is required to fetch data from the internet. Install it via pip.')
#         try:
#             df = yf.download(ticker, period=period, start=start, end=end, progress=False)
#             if df.empty:
#                 raise RuntimeError(f'No data returned for {ticker}')
#             df = df.reset_index()
#         except Exception as e:
#             raise RuntimeError(f"yFinance failed for {ticker}: {e}")
#     else:
#         raise ValueError('Provide either ticker or filepath')


#     # Normalize column names
#     df.columns = [c.strip().title() for c in df.columns]


#     # Ensure Date exists
#     if 'Date' not in df.columns:
#         if df.index.name == 'Date':
#             df = df.reset_index()
#         else:
#             raise ValueError('No Date column found in data')


#     # Ensure common columns exist
#     for col in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
#         if col not in df.columns:
#             df[col] = pd.NA


#     df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']]
#     df = df.sort_values('Date').reset_index(drop=True)
#     df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
#     return df