import pandas as pd


def calculate_sma(df, window=20):
    df = df.copy()
    col = f'SMA_{window}'
    df[col] = df['Close'].rolling(window=window, min_periods=1).mean()
    return df