import pandas as pd


def calculate_ema(df, window=20):
    df = df.copy()
    col = f'EMA_{window}'
    df[col] = df['Close'].ewm(span=window, adjust=False).mean()
    return df