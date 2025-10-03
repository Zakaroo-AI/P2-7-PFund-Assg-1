import pandas as pd


def calculate_macd(df, span_short=12, span_long=26, span_signal=9):
    df = df.copy()
    ema_short = df['Close'].ewm(span=span_short, adjust=False).mean()
    ema_long = df['Close'].ewm(span=span_long, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=span_signal, adjust=False).mean()
    df['MACD'] = macd
    df['MACD_signal'] = signal
    df['MACD_hist'] = macd - signal
    return df