import pandas as pd
import numpy as np

def calculate_sma(df, window = 5):
    """ Calculates the average closing price over a user defined period for the specified stock

    Args:
        data (pd.Series): stock close prices for specified ticker over user-defined period
        window (int): the amount of data points being calculated, defaults to 5
    
    Returns:
        rolling_sma (list[np.nan, np.float]): list of floats representing average of close prices of last 5 entries (including self)
    """
    data = df["Close"].copy()

    # validating invalid inputs
    if window < 1:
        raise ValueError("Window size must be at least 1")
    if data.size < window:
        raise IndexError(f'Insufficient data, only {data.size} points selected for window size of {window}')

    # calculates first window sum, for efficient sliding window calculation
    window_sum = data.iloc[:window].sum()
    # starts with NaN values for initial values
    rolling_sma = [np.nan] * (window - 1) + [window_sum / window]

    # roll across remaining data points
    for i in range(window, data.size):
        # removes old data point, adds new data point to sliding window
        window_sum = window_sum + data.iloc[i] - data.iloc[i - window]
        rolling_sma.append(window_sum / window)

    df[f'SMA_{window}'] = rolling_sma
    return df