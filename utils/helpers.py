# utils/helpers.py
import pandas as pd

# mapping for uploaded files -> approximate number of trading days
UPLOAD_ROWS_MAP = {
    '1M': 21,
    '3M': 63,
    '6M': 126,
    '1Y': 252,
    '2Y': 504,
}

# mapping for ticker time windows in months
TICKER_MONTHS_MAP = {
    '1M': 1,
    '3M': 3,
    '6M': 6,
    '1Y': 12,
    '2Y': 24,
}

def filter_dataframe(df: pd.DataFrame, source: str, option: str) -> pd.DataFrame:
    """Filter dataframe according to source and option.

    - For source='ticker': return the *latest* N months worth of data (based on Date.max()).
    - For source='file': return the *first* N rows approximating the chosen timeframe.

    Args:
        df: DataFrame that must contain a 'Date' column of dtype datetime64[ns].
        source: 'ticker' or 'file'
        option: one of the keys in UPLOAD_ROWS_MAP / TICKER_MONTHS_MAP ('1M','3M','6M','1Y','2Y')

    Returns:
        Filtered DataFrame preserving 'Date' and 'Close' at minimum.
    """
    if option not in TICKER_MONTHS_MAP:
        # default to 1 year if unknown
        option = '1Y'

    months = TICKER_MONTHS_MAP[option]
    try:
        cutoff = df['Date'].max() - pd.DateOffset(months=months)
        filtered = df[df['Date'] >= cutoff].copy()
    except Exception:
        # fallback: return the last N rows using approximate trading days
        rows = UPLOAD_ROWS_MAP.get(option, 252)
        filtered = df.tail(rows).copy()
    return filtered.reset_index(drop=True)