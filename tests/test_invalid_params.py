import pandas as pd
import numpy as np
import pytest
from indicators.registry import apply_indicator

@pytest.fixture
def sample_data():
    np.random.seed(0)
    data = pd.DataFrame({
        "Date": pd.date_range("2023-01-01", periods=50),
        "Close": np.random.rand(50) * 100
    })
    return data

def test_invalid_params_sma(sample_data):
    period = 0

    with pytest.raises(ValueError, match="Invalid parameter 'window'=0 for indicator 'sma'. Must be > 0."):
        apply_indicator(sample_data, "sma", {"window": period})[f'SMA_{period}']

def test_invalid_params_ema_nonpositive(sample_data):
    # EMA period must be > 0
    period = -5
    with pytest.raises(ValueError, match="Invalid parameter 'interval'=-5 for indicator 'ema'. Must be > 0."):
        apply_indicator(sample_data, "ema", {"interval": period})[f'EMA_{period}']

def test_invalid_params_rsi_nonpositive(sample_data):
    # RSI period must be > 0
    period = 0
    with pytest.raises(ValueError, match="Invalid parameter 'interval'=0 for indicator 'rsi'. Must be > 0."):
        apply_indicator(sample_data, "rsi", {"interval": period})[f'RSI_{period}']

def test_invalid_params_macd_nonpositive_fast(sample_data):
    # MACD fast must be > 0
    fast = 0
    slow = 26
    signal = 9
    with pytest.raises(ValueError, match="Invalid parameter 'fast_period'=0 for indicator 'macd'. Must be > 0 and less than 'slow_period'."):
        apply_indicator(sample_data, "macd", {"fast_period": fast, "slow_period": slow, "signal_period": signal})

def test_invalid_params_macd_fast_ge_slow(sample_data):
    # MACD fast must be less than slow
    fast = 26
    slow = 26
    signal = 9
    with pytest.raises(ValueError, match="Invalid parameter 'fast_period'=26 for indicator 'macd'. Must be > 0 and less than 'slow_period'."):
        apply_indicator(sample_data, "macd", {"fast_period": fast, "slow_period": slow, "signal_period": signal})

def test_invalid_params_macd_signal_nonpositive(sample_data):
    # MACD signal must be > 0
    fast = 12
    slow = 26
    signal = -1
    with pytest.raises(ValueError, match="Invalid parameter 'signal_period'=-1 for indicator 'macd'. Must be > 0."):
        apply_indicator(sample_data, "macd", {"fast_period": fast, "slow_period": slow, "signal_period": signal})