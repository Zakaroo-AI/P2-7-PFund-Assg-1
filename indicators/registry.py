# indicators/registry.py
from .sma import calculate_sma
from .ema import calculate_ema
from .rsi import calculate_rsi
from .macd import calculate_macd
from .dailyr import calculate_dailyr
from .updown import calculate_updown

# Registry: key -> metadata
"""
Indicator registry and dispatcher for applying technical analysis indicators.

This module defines a centralized mapping of indicator keys (e.g., `"sma"`, `"ema"`,
`"rsi"`, `"macd"`, `"dailyr"`) to their calculation functions, default parameters,
and plotting metadata. It provides helper functions to retrieve indicator
specifications and safely apply indicators to a pandas DataFrame.

Typical usage example:
----------------------
    from indicators.registry import apply_indicator

    df = pd.read_csv("AAPL.csv")
    df_with_sma = apply_indicator(df, "sma", {"window": 20})
"""
INDICATORS = {
    "sma": {
        "func": calculate_sma,
        "default_params": {"window": 5},
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
    "dailyr": {
        "func": calculate_dailyr,
        "default_params": {"tolerance": 0, "threshold": 0.00},  # no parameters needed
        "columns": lambda p: ["DailyR"],
        "plot_kind": "separate_dailyr",  # show on its own subplot
    },
}


def get_indicator_keys():
    """
    Return a list of all available indicator keys.

    Returns
    -------
    list of str
        A list of indicator names (e.g. `["sma", "ema", "rsi", "macd", "dailyr"]`).
    """
    return list(INDICATORS.keys())


def get_indicator_spec(key: str):
    """
    Retrieve the metadata dictionary for a given indicator key.

    Parameters
    ----------
    key : str
        Indicator key name (e.g. `'sma'`, `'ema'`, `'rsi'`).

    Returns
    -------
    dict or None
        Dictionary containing:
            - `"func"`: Calculation function
            - `"default_params"`: Default parameters
            - `"columns"`: Function that returns expected output column names
            - `"plot_kind"`: Visualization type for plotting
        Returns `None` if the key is not found.
    """
    return INDICATORS.get(key)


def apply_indicator(df, key: str, params: dict | None = None):
    """
    Apply the specified indicator to a DataFrame.

    This function dynamically retrieves the correct calculation function and applies
    it to the given `df`, using either the default parameters or user-specified
    overrides. If the DataFrame already contains all expected output columns for
    that indicator, the function simply returns a copy (idempotent behavior) [.copy].

    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame containing price data (must include at least `'Close'`).
    key : str
        Indicator name, such as `'sma'`, `'ema'`, `'rsi'`, `'macd'`, or `'dailyr'`.
    params : dict, optional
        Dictionary of custom parameters for the indicator.
        Any provided parameters will override the defaults.

    Returns
    -------
    pandas.DataFrame
        New DataFrame including the computed indicator columns.
        If an error occurs or the key is unknown, returns the original DataFrame.

    Raises
    ------
    ValueError
        If the indicator key is unknown.

    Notes
    -----
    - Automatically merges user parameters with defaults.
    - Skips recalculation if expected columns already exist.
    - Logs a warning on failure but does not stop execution.

    Example
    -------
    >>> df = pd.read_csv("AAPL.csv")
    >>> df = apply_indicator(df, "rsi", {"interval": 14})
    >>> df.columns
    Index([... 'RSI_14'], dtype='object')
    """
    import pandas as pd

    # === Defensive checks ===
    if key is None:
        return df

    spec = get_indicator_spec(key)
    if spec is None:
        raise ValueError(f"Unknown indicator: {key}")

    if df is None or df.empty:
        print(f"[WARN] Empty DataFrame passed to apply_indicator('{key}').")
        return df

    if "Close" not in df.columns:
        print(f"[WARN] Missing 'Close' column in data — required for '{key}' indicator.")
        return df

    # === Merge default + user parameters ===
    params = params or {}
    merged_params = {**spec["default_params"], **params}
    expected_cols = spec["columns"](merged_params)

    # === Skip recalculation if already exists ===
    if all(col in df.columns for col in expected_cols):
        return df.copy()

    # === Validate numeric parameters ===
    ALLOW_ZERO = {"dailyr"}

    for k, v in merged_params.items():
        if isinstance(v, (int, float)):
            # Allow 0 for DailyR only
            if key in ALLOW_ZERO:
                if v < 0:
                    raise ValueError(
                        f"Invalid parameter '{k}'={v} for indicator '{key}'. Must be >= 0."
                    )
            else:
                if v <= 0:
                    # Special rule for MACD fast_period
                    if key == "macd" and k == "fast_period":
                        raise ValueError(
                            f"Invalid parameter '{k}'={v} for indicator '{key}'. Must be > 0 and less than 'slow_period'."
                        )
                    else:
                        raise ValueError(
                            f"Invalid parameter '{k}'={v} for indicator '{key}'. Must be > 0."
                        )

    # === Extra MACD-specific validation ===
    if key == "macd":
        fast = merged_params.get("fast_period")
        slow = merged_params.get("slow_period")
        if fast is not None and slow is not None and fast >= slow:
            raise ValueError(
                f"Invalid parameter 'fast_period'={fast} for indicator 'macd'. Must be > 0 and less than 'slow_period'."
            )
    try:
        # Call indicator function dynamically
        res = spec["func"](df.copy(), **merged_params)
        if res is None:
            raise ValueError(f"{key} function returned None or invalid output.")
        print(f"[INFO] {key.upper()} applied successfully with parameters: {merged_params}")
    except Exception as e:
        print(f"[ERROR] {key} function failure: {e}")
        # Return dataframe with error info embedded (for safe rendering)
        df = df.copy()
        df[f"{key.upper()}_ERROR"] = str(e)
        return df
    print('zkdebug5 retunring res')
    return res
