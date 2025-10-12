import pandas as pd
import numpy as np

def align_dfs():

    return


def preprocess_stock_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform data preprocessing on a single stock DataFrame.
    Steps:
    1. Parse and sort date
    2. Handle missing / invalid values
    3. Remove extreme outliers
    4. Add derived columns for analysis (e.g. Daily_Return, Close_Smoothed)
    """
    df = df.copy()

    # Ensure valid datetime 
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce', utc=True)
        df = df.sort_values('Date').dropna(subset=['Date']).reset_index(drop=True)

    # Fill missing values 
    if 'Close' in df.columns:
        df['Close'] = df['Close'].replace([np.inf, -np.inf], np.nan)
        # bridges NaN gaps with left and right values, then ffill and bfill to fill up trailing and leading NaNs
        df['Close'] = df['Close'].interpolate(method='linear').ffill().bfill()

    if 'Volume' in df.columns:
        df['Volume'] = df['Volume'].fillna(0)

    # Remove unrealistic outliers in Close 
    if 'Close' in df.columns and len(df) > 10:
        q1, q3 = df['Close'].quantile([0.01, 0.99])
        df = df[(df['Close'] >= q1) & (df['Close'] <= q3)]
  
    # Safety net if got remaining NaNs (probably not)
    df = df.dropna(subset=['Close']).reset_index(drop=True)

    return df


def preprocess_multiple_dfs(dfs):
    """
    Preprocess and align multiple DataFrames.
    Returns: list of preprocessed DataFrames aligned by Date.
    """
    if not dfs:
        return []

    cleaned = [preprocess_stock_data(df) for df in dfs]
    aligned = align_dfs(cleaned, on='Date')
    return aligned
