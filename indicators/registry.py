# indicators/registry.py
from .sma import calculate_sma
from .ema import calculate_ema
from .rsi import calculate_rsi
from .macd import calculate_macd

# Registry: key -> metadata
INDICATORS = {
    "sma": {
        "func": calculate_sma,
        "default_params": {"window": 20},
        # columns function receives merged params and returns list of expected columns
        "columns": lambda p: [f"SMA_{p.get('window', 20)}"],
        "plot_kind": "overlay",  # overlay on price
    },
    "ema": {
        "func": calculate_ema,
        "default_params": {"interval": 20},
        "columns": lambda p: [f"EMA_{p.get('interval', 20)}"],
        "plot_kind": "overlay",
    },
    "rsi": {
        "func": calculate_rsi,
        "default_params": {"interval": 14},
        "columns": lambda p: [f"RSI_{p.get('interval', 14)}"],
        "plot_kind": "separate_rsi",  # draw in its own subplot with range 0-100
    },
    "macd": {
        "func": calculate_macd,
        "default_params": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
        "columns": lambda p: ["MACD", "MACD_signal", "MACD_hist"],
        "plot_kind": "separate_macd",  # macd histogram + signal in second subplot
    },
}


def get_indicator_keys():
    return list(INDICATORS.keys())


def get_indicator_spec(key: str):
    return INDICATORS.get(key)


def apply_indicator(df, key: str, params: dict | None = None):
    """
    Apply the indicator `key` to df if the expected columns are not present.
    This keeps the operation idempotent.
    Returns a new DataFrame (copy).
    """
    if key is None:
        return df
    spec = get_indicator_spec(key)
    if spec is None:
        raise ValueError(f"Unknown indicator: {key}")

    params = params or {}
    merged_params = {**spec["default_params"], **params}
    expected_cols = spec["columns"](merged_params)

    # if all expected columns already exist, skip
    if all(col in df.columns for col in expected_cols):
        return df.copy()

    # otherwise call the indicator function with merged params
    return spec["func"](df.copy(), **merged_params)
