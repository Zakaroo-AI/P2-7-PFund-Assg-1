import pandas as pd
import numpy as np

def calculate_ema(df, interval = 10, smoothing = 2.0, for_macd = False):
    """ Calculates a weighted moving average of closing prices that gives more importance to recent prices

    Args:
        ticker (str): stock ticker
        start (str): first entry in interval
        end (str): last entry in interval
        interval (int): amount of preceding data points to use in calculating EMA, defaults to 10
        smoothing (float): strength of weightage for recent data points, defaults to 2.0
        ticker_dict (dict: str[df]): dictionary, with key-value pairs of ticker to dataframe containing stock history, defaults to ticker_dict
    
    Returns:
        rolling_ema (list[np.float]): list of floats representing weighted average of close prices
        or
        rolling_ema (list[np.nan, np.float]): list of floats representing weighted average of close prices
    """
    # MACD function passes in data only, no df
    if for_macd:
        data = df
    else:
        data = df["Close"].copy()

    # validating invalid inputs
    if smoothing <= 0:
        raise ValueError("Smoothing factor must be positive")
    if interval < 1:
        raise ValueError("Interval size must be at least 1")
    if data.size < interval:
        raise IndexError(f'Insufficient data, only {data.size} points selected for interval size of {interval}')
    
    # weight -> % of ema represented by the most recent entry
    # weighting more recent entries is greater for shorter intervals
    weight = smoothing / (interval + 1)     

    # using sma as an initial state, afterwards we can implement EMA
    sma = data.iloc[:interval].mean()    
    # check if need to use interval or interval-1
    rolling_ema = [np.nan] * (interval-1) + [sma]

    # calculate following EMA values
    for i in range(interval, data.size):
        ema = data.iloc[i] * weight + rolling_ema[-1] * (1 - weight)
        rolling_ema.append(ema)

    # MACD function has no need for whole df
    if for_macd:
        return rolling_ema

    df[f'EMA_{interval}'] = rolling_ema
    return df