import pandas as pd
import pytest
import sys
import os

from data.preprocess import align_dfs

sys.path.append('..')


def test_align_dfs_basic():
    """Basic test that function works with sample data."""
    df1 = pd.read_csv('tests_data/sample_align1.csv')
    df2 = pd.read_csv('tests_data/sample_align2.csv')
    
    result = align_dfs([df1, df2])
    
    # Basic checks
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(df, pd.DataFrame) for df in result)
    assert all('Date' in df.columns for df in result)


def test_align_dfs_empty():
    """Test empty input."""
    assert align_dfs([]) == []


def test_align_dfs_error():
    """Test error for missing Date column."""
    df_bad = pd.DataFrame({'A': [1], 'B': [2]})
    
    with pytest.raises(ValueError):
        align_dfs([df_bad])