import pandas as pd
import pytest
from indicators.updown import calculate_updown

# --- Helper: make small test data quickly ---
def make_df(changes):
    """Creates a small DataFrame with 'Date' and 'DailyR' columns."""
    dates = pd.date_range("2024-01-01", periods=len(changes))
    return pd.Series(changes, index=dates)

# --- Basic Tests ---
def test_simple_up_streak():
    s = make_df([1, 2, 3, 4, 5])
    result = calculate_updown(s, tolerance=0, threshold=1)
    assert result["up_streak"] == 5
    assert pd.to_datetime(result["up_start"]).date() == pd.Timestamp("2024-01-01").date()
    assert pd.to_datetime(result["up_end"]).date() == pd.Timestamp("2024-01-05").date()

def test_simple_down_streak():
    s = make_df([-1, -2, -3, -4])
    result = calculate_updown(s, tolerance=0, threshold=1)
    assert result["down_streak"] == 4
    assert "January 2024" in result["down_start"]
    assert "January 2024" in result["down_end"]

# --- Tolerance Logic ---
def test_small_opposite_within_tolerance():
    # Upward streak, small down moves (within threshold) allowed
    s = make_df([2, 3, -0.5, 4, -0.3, 5])
    result = calculate_updown(s, tolerance=2, threshold=1)
    # Should not break because small drops are tolerated
    assert result["up_streak"] == len(s)

def test_large_opposite_breaks_streak():
    s = make_df([1, 2, -2.5, 3, 4])
    result = calculate_updown(s, tolerance=2, threshold=1)
    # Big negative move should break the upward streak
    assert result["up_streak"] < len(s)

# --- Flat & alternating ---
def test_flat_days_continue_streak():
    s = make_df([1, 0, 0, 2, 3])
    result = calculate_updown(s, tolerance=1, threshold=1)
    assert result["up_streak"] == 5  # flats don't break streak

def test_alternating_moves():
    s = make_df([1, -1, 1, -1, 1])
    result = calculate_updown(s, tolerance=1, threshold=0.5)
    # Frequent flips should limit streaks
    assert result["up_streak"] <= 3
    assert result["down_streak"] <= 3

# --- Edge cases ---
def test_empty_series():
    s = pd.Series([], dtype=float)
    result = calculate_updown(s, tolerance=1, threshold=1)
    assert result["up_streak"] == 0
    assert result["down_streak"] == 0

def test_all_zero_changes():
    s = make_df([0, 0, 0, 0])
    result = calculate_updown(s, tolerance=1, threshold=1)
    assert result["up_streak"] == 4
    assert result["down_streak"] == 4