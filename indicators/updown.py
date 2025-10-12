import pandas as pd
import numpy as np

def calculate_updown(pct_changes: pd.Series[float], tolerance: int = 0, threshold: float = 0):
    """ Calculates the average closing price over a user defined period for the specified stock

    Args:
        data (pd.Series): stock close prices for specified ticker over user-defined period
        window (int): the amount of data points being calculated, defaults to 5
        tolerance only exceeds when its in a row
    Returns:
        (dict): contains
    """
    # Convert to np array for speed
    values = pct_changes.values
    n = len(values)

    # Handling edge cases
    if n == 0:
        return {'up_streak': 0, 'up_start': -1, 'up_end': -1, 
                'down_streak': 0, 'down_start': -1, 'down_end': -1}
    if n == 1:
        return {'up_streak': 1, 'up_start': 0, 'up_end': 0, 
                'down_streak': 1, 'down_start': 0, 'down_end': 0}
    
    # Get boolean masks first
    up_mask = values < 0
    down_mask = values > 0
    zero_mask = values == 0

    # Check if abs(value) exceeds threshold percentage
    if threshold is not None:
        threshold_mask = np.abs(values) > threshold
    else:   # if no threshold, all pass (False)
        threshold_mask = np.zeros_like(values, dtype=bool)


    # defining fn to handle both upward & downward
    # define within for variable access
    def calculate_streak(is_up):
        # Choose which mask according to direction
        direction_mask = up_mask if is_up else down_mask

        # Tracked variables
        max_streak = 1              # Maximum found streak
        current_streak = 0          # Streak counter
        tolerance_left = tolerance  # Tolerance remaining, 0 means out of tolerance

        streak_start = 0            # Start of best streak
        streak_end = 0              # End of best streak

        # Single pass through
        for i in range(n):
            # Check if exceeds threshold in opposite direction
            if threshold_mask[i] and not direction_mask[i]:
                #resetStreak()
                # Record new max only when resetting streak
                if current_streak > max_streak:
                    max_streak = current_streak
                    # Record start+end date
                    streak_end = i
                    streak_start = i - max_streak
                # Reset variables for next streak
                # Start new streak if current point is valid
                if direction_mask[i]:
                    current_streak = 1
                else:
                    current_streak = 0
                tolerance_left = tolerance
                
                continue    # go to next loop

            # check if elememnt i continues streak
            if direction_mask[i]:
                current_streak += 1
                tolerance_left = tolerance  # Reset tolerance
            # check if element i is 0, treat as neutral value
            elif zero_mask[i]:
                current_streak += 1         # No resetting of tolerance
            # check if we can forgive the opposite direction
            elif tolerance_left > 0:
                current_streak += 1   
                tolerance_left -= 1         # consume one tolerance
            # check if streak breaks
            else:
                #resetStreak()
                if current_streak > max_streak:
                    max_streak = current_streak
                # Reset variables for next streak
                # Start new streak if current point is valid
                if direction_mask[i]:
                    current_streak = 1
                else:
                    current_streak = 0
                tolerance_left = tolerance
                # Record start+end date
                streak_end = i
                streak_start = i - max_streak

        # Final check after loop completes
        if current_streak > max_len:
            max_len = current_streak

        return max_len, streak_start, streak_end

    up_streak = calculate_streak(True)
    down_streak = calculate_streak(False)

    return up_streak, down_streak