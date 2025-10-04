import pandas as pd
import numpy as np

# def calculate_rsi(df, period=14):
#     df = df.copy()
#     delta = df['Close'].diff()
#     gain = delta.clip(lower=0)
#     loss = -delta.clip(upper=0)


#     # Simple rolling average (Wilder smoothing could be used later)
#     avg_gain = gain.rolling(window=period, min_periods=period).mean()
#     avg_loss = loss.rolling(window=period, min_periods=period).mean()


#     rs = avg_gain / avg_loss
#     rsi = 100 - (100 / (1 + rs))
#     df[f'RSI_{period}'] = rsi
#     return df

def calculate_rsi(df, interval = 14):
    """ Measures the speed and magnitude of recent price changes to detect overbought/oversold conditions

    Args:
        data (pd.Series): stock close prices for specified ticker over user-defined period
        interval (int): the amount of data points being calculated, defaults to 5
    
    Returns:
        rsi_values (list[np.nan, np.float]): list of floats signalling a trend upwards or downwards
    """
    data = df["Close"].copy()

    # validating invalid inputs    
    if interval < 1:
        raise ValueError("Window size must be at least 1")
    if data.size < interval:
        raise IndexError(f'Insufficient data, only {data.size} points selected for window size of {interval}')

    # calculate close price differences
    differences = data[1:].values - data.values[:-1]  # contains length - 1 elements

    gains = 0
    losses = 0
    for i in differences[:interval]:
        gains += max(i, 0)     # if i is positive, use i else use 0
        losses += max(-i, 0)   # if i is negative, use i else use 0
    
    avg_gain = gains / interval
    avg_loss = losses / interval
    if avg_loss == 0:
        rsi = 100
    else:
        rsi = 100 - 100/(1 + avg_gain / avg_loss)

    rsi_values = [np.nan] * interval + [rsi]

    # we use smoothing as it counters having a period of no losses, which may cause avg_loss to be 0, causing divide by zero error
    # as long as there is one entry > 0, it will never divide by zero (if there is none, we use rsi = 100)
    for i in differences[interval:]:
        # obvious thing to do here is to loop thru differences every time, but we can use sliding window here again
        # use remainder as index?
        avg_gain = (avg_gain * (interval - 1) + max(i, 0)) / interval # i-1 because differences has one less entry than truncated
        avg_loss = (avg_loss * (interval - 1) + max(-i, 0)) / interval

        if avg_loss == 0:
            rsi = 100
        else:
            rsi = 100 - 100/(1 + avg_gain/avg_loss)

        # try:    # shud replace this with proper handling later, currently meant to weed out dividing by zero errors -> no loss = strength is max
        #     #rs = ( sum(gains) / len(gains) ) / ( sum(losses) / len(losses) )
        #     rs = sum(gains) / sum(losses)
        #     rsi = 100 - 100/(1 + rs) 
        # except:
        #     rsi = 100
        rsi_values.append(rsi)

    #to implement smoothing

    df[f'RSI_{interval}'] = rsi_values
    return df