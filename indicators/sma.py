def calculate_sma(df, window=20):
    df[f"SMA_{window}"] = df['Close'].rolling(window=window).mean()
    return df
