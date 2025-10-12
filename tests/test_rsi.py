import pandas as pd
import numpy as np
import pytest
import talib
from indicators.registry import apply_indicator

@pytest.fixture
def sample_data():
    np.random.seed(0)
    data = pd.DataFrame({
        "Date": pd.date_range("2023-01-01", periods=50),
        "Close": np.random.rand(50) * 100
    })
    return data

def test_macd_matches_talib(sample_data):
    fast_period = 12
    slow_period = 26
    signal_period = 9
    
    # Calculate MACD using your implementation
    my_macd_df = apply_indicator(sample_data, "macd", {
        "fast_period": fast_period, 
        "slow_period": slow_period, 
        "signal_period": signal_period
    })
    
    my_macd_line = my_macd_df['MACD']
    my_signal_line = my_macd_df['MACD_signal']
    my_histogram = my_macd_df['MACD_hist']
    
    # Calculate MACD using TA-Lib
    talib_macd_line, talib_signal_line, talib_histogram = talib.MACD(
        sample_data["Close"], 
        fastperiod=fast_period, 
        slowperiod=slow_period, 
        signalperiod=signal_period
    )
    
    # Convert TA-Lib results to pandas Series with the same index
    talib_macd_line = pd.Series(talib_macd_line, index=sample_data.index)
    talib_signal_line = pd.Series(talib_signal_line, index=sample_data.index)
    talib_histogram = pd.Series(talib_histogram, index=sample_data.index)
    
    tolerance = 1e-5

    # Test MACD line
    pd.testing.assert_series_equal(
        my_macd_line, 
        talib_macd_line, 
        check_names=False,
        rtol=tolerance,  # Allow for small floating point differences
        atol=tolerance
    )
    
    # Test signal line
    pd.testing.assert_series_equal(
        my_signal_line, 
        talib_signal_line, 
        check_names=False,
        rtol=tolerance,
        atol=tolerance
    )
    
    # Test histogram
    pd.testing.assert_series_equal(
        my_histogram, 
        talib_histogram, 
        check_names=False,
        rtol=tolerance,
        atol=tolerance
    )