import pandas as pd


def calculate_rsi(df, period=14):
    df = df.copy()
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)


    # Simple rolling average (Wilder smoothing could be used later)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()


    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    df[f'RSI_{period}'] = rsi
    return df