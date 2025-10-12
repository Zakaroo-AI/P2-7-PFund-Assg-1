import pandas as pd
import numpy as np

from .ema import calculate_ema

def calculate_macd(df, fast_period = 12, slow_period = 26, signal_period = 9):
    """ A technical indicator used for identifying points for buying and selling

    Args:
        data ()
        fast_period (int) = 
        slow_period (int) = 
        signal_period (int) = 
    
    Returns:
        rolling_ema (list[np.float]): list of floats representing weighted average of close prices
        or
        rolling_ema (list[np.nan, np.float]): list of floats representing weighted average of close prices
    """

    data = df["Close"].copy()

    if fast_period >= slow_period:
        raise ValueError("Fast period must be less than slow period")
    if any(period < 1 for period in [fast_period, slow_period, signal_period]):
        raise ValueError("All periods must be at least 1")
    if len(data) < slow_period + signal_period:
        raise IndexError("Insufficient data for the given periods")
    
    # Calculate EMAs for fast and slow periods
    ema_fast = calculate_ema(data, interval = fast_period, for_macd = True)
    ema_slow = calculate_ema(data, interval = slow_period, for_macd = True)
    
    macd_line = pd.Series(ema_fast) - pd.Series(ema_slow)   # convert to pd.Series for operating across the list

    # finding where MACD line starts (ignoring NaN values)
    first_non_nan = macd_line.first_valid_index()
    if first_non_nan is None:
        raise ValueError("MACD line error")

    # Calculate signal_line
    signal_line_vals = calculate_ema(macd_line[first_non_nan:], signal_period, for_macd = True)
    signal_line = [np.nan] * first_non_nan + signal_line_vals
    histogram = macd_line - signal_line

    # print('My macd:', macd_line, 'My Signal:', signal_line, 'My histogram:', histogram)

    df['MACD'] = macd_line
    df['MACD_signal'] = signal_line
    df['MACD_hist'] = histogram
    return df