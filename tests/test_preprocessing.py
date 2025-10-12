import pandas as pd
import numpy as np
import pytest
from data.preprocess import align_dfs, preprocess_stock_data


# ------------------------
#  Helper: sample DataFrame creator
# ------------------------
def make_df(dates, closes, volumes=None):
    data = {"Date": pd.to_datetime(dates), "Close": closes}
    if volumes is not None:
        data["Volume"] = volumes
    return pd.DataFrame(data)


# ------------------------
#  Tests for align_dfs()
# ------------------------

def test_align_dfs_merges_all_dates_and_fills():
    df_a = make_df(["2024-01-01", "2024-01-03", "2024-01-05"], [10, 20, 30])
    df_b = make_df(["2024-01-02", "2024-01-05"], [100, 200])

    aligned = align_dfs([df_a, df_b])
    assert len(aligned) == 2

    # Expect union of all dates
    expected_dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-05"])
    for df in aligned:
        assert list(df["Date"]) == list(expected_dates)

    # Check forward-fill and backfill
    df_a_filled = aligned[0]
    df_b_filled = aligned[1]

    # df_a should have filled 2024-01-02 = 10 (ffill)
    assert df_a_filled.loc[df_a_filled["Date"] == "2024-01-02", "Close"].iloc[0] == 10
    # df_b should have filled 2024-01-03 = 100 (ffill)
    assert df_b_filled.loc[df_b_filled["Date"] == "2024-01-03", "Close"].iloc[0] == 100


def test_align_dfs_handles_duplicate_dates():
    df_dup = make_df(["2024-01-01", "2024-01-01", "2024-01-02"], [10, 20, 30])
    result = align_dfs([df_dup])
    df_aligned = result[0]
    assert len(df_aligned["Date"].unique()) == len(df_aligned)
    assert not df_aligned["Date"].duplicated().any()


def test_align_dfs_empty_list_returns_empty():
    assert align_dfs([]) == []


def test_align_dfs_missing_date_column_raises():
    df = pd.DataFrame({"Close": [1, 2, 3]})
    with pytest.raises(ValueError):
        align_dfs([df])


# ------------------------
#  Tests for preprocess_stock_data()
# ------------------------

def test_preprocess_stock_data_sorts_and_fills_missing():
    df = make_df(
        ["2024-01-03", "2024-01-01", "2024-01-02"],
        [np.nan, 100, np.nan],
        [10, np.nan, 30]
    )
    cleaned = preprocess_stock_data(df)

    # Should be sorted by date
    assert list(cleaned["Date"]) == sorted(cleaned["Date"].tolist())

    # NaNs should be filled
    assert not cleaned["Close"].isna().any()

    # Volume NaNs filled with 0
    assert not cleaned["Volume"].isna().any()


def test_preprocess_stock_data_removes_outliers():
    np.random.seed(0)
    values = np.concatenate([np.random.normal(100, 1, 20), [1000]])  # one extreme outlier
    df = make_df(pd.date_range("2024-01-01", periods=21), values)

    cleaned = preprocess_stock_data(df)

    # Outlier should be removed
    assert cleaned["Close"].max() < 1000
    assert len(cleaned) < len(df)


def test_preprocess_stock_data_handles_missing_columns():
    """Should not crash if 'Volume' missing."""
    df = make_df(["2024-01-01", "2024-01-02"], [10, 20])
    cleaned = preprocess_stock_data(df)
    assert "Close" in cleaned.columns
    assert "Date" in cleaned.columns