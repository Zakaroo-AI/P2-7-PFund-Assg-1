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

def test_ema_matches_talib(sample_data):
    interval = 10
    my_ema = apply_indicator(sample_data, "ema", {"interval": interval})[f'EMA_{interval}']
    talib_ema = talib.EMA(sample_data["Close"], timeperiod = interval)
    pd.testing.assert_series_equal(my_ema, talib_ema, check_names=False)

def test_rsi_matches_talib(sample_data):
    interval = 14
    my_rsi = apply_indicator(sample_data, "rsi", {"interval": interval})[f'RSI_{interval}']
    talib_rsi = talib.RSI(sample_data['Close'], timeperiod=interval)
    pd.testing.assert_series_equal(my_rsi, talib_rsi, check_names=False)

