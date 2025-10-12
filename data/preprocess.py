import pandas as pd
import numpy as np

def align_dfs(dfs, on='Date'):
    """
    Align multiple DataFrames on the same 'Date' column.

    Performs an outer join across all dates, and forward-fills
    missing values within each DataFrame individually.

    Returns
    -------
    list of pd.DataFrame
        A list of aligned DataFrames (not merged).
    """
    if not dfs:
        return []

    # --- Step 1: Collect all unique dates from every DataFrame ---
    all_dates = pd.Index([])
    for df in dfs:
        if on in df.columns:
            all_dates = all_dates.union(df[on])
    all_dates = all_dates.sort_values()

    # --- Step 2: Reindex each DataFrame to this full date range ---
    aligned_dfs = []
    for df in dfs:
        if on not in df.columns:
            raise ValueError(f"Missing '{on}' column in one of the DataFrames.")
        
        temp = df.set_index(on).reindex(all_dates)  # outer join on all dates
        temp = temp.ffill()                         # forward-fill missing values
        temp = temp.reset_index().rename(columns={'index': on})
        aligned_dfs.append(temp)

    return aligned_dfs


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
