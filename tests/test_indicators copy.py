import pandas as pd
import numpy as np
import pytest
import talib
from indicators.registry import apply_indicator

@pytest.mark.parametrize(
    "indicator, form_data, expected_text",
    [
        ("SMA", {"indicator": "SMA", "window": 5}, b"SMA"),    # valid
        ("EMA", {"indicator": "EMA", "window": 5}, b"EMA"),    # valid
        ("RSI", {"indicator": "RSI", "window": 14}, b"RSI"),   # valid
        # You can add future indicators here easily:
        # ("MACD", {"indicator": "MACD", ...}, b"MACD")
    ],
)
def test_valid_indicators(client, indicator, form_data, expected_text):
    """
    Tests that each indicator route produces a valid response containing
    its indicator name. The client fixture comes from conftest.py.
    """
    response = client.post("/", data=form_data)
    assert response.status_code == 200
    assert expected_text in response.data


@pytest.mark.parametrize(
    "indicator, form_data, expected_error",
    [
        ("SMA", {"indicator": "SMA", "window": 0}, b"Invalid"),   # window 0 should fail
        ("EMA", {"indicator": "EMA", "window": -1}, b"Invalid"),
        ("RSI", {"indicator": "RSI", "window": 0}, b"Invalid"),
    ],
)
def test_invalid_indicator_inputs(client, indicator, form_data, expected_error):
    """
    Tests that invalid parameters trigger visible error messages.
    """
    response = client.post("/", data=form_data)
    assert response.status_code == 200
    assert expected_error in response.data
