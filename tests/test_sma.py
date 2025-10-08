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

def test_sma_matches_talib(sample_data):
    period = 10
    my_sma = apply_indicator(sample_data, "sma", {"window": period})[f'SMA_{period}']
    talib_sma = talib.SMA(sample_data["Close"], timeperiod = period)
    pd.testing.assert_series_equal(my_sma, talib_sma, check_names=False)

