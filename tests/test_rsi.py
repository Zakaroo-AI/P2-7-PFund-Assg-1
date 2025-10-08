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

def test_rsi_matches_talib(sample_data):
    interval = 14
    my_rsi = apply_indicator(sample_data, "rsi", {"interval": interval})[f'RSI_{interval}']
    talib_rsi = talib.RSI(sample_data['Close'], timeperiod=interval)
    pd.testing.assert_series_equal(my_rsi, talib_rsi, check_names=False)

