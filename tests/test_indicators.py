import pandas as pd
from indicators import calculate_sma

def test_sma():
    data = {"Date": pd.date_range("2023-01-01", periods=10),
            "Close": [i for i in range(10)]}
    df = pd.DataFrame(data)
    df = calculate_sma(df, window=3)
    assert "SMA_3" in df.columns
    assert df["SMA_3"].iloc[2] == 1  # average of 0,1,2
