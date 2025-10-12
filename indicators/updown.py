import pandas as pd
import numpy as np
from datetime import datetime

def timestamp_to_words(timestamp: str):
    try:
        timestamp = pd.Timestamp(timestamp)
        month_year = timestamp.strftime('%B %Y')  # eg January 2025
        
        day = timestamp.day
        suffixes = ('st', 'nd', 'rd')

        if (4 <= day <= 20) or (24 <= day <= 30):
            suffix = 'th'
        else:
            suffix = suffixes[(day % 10) - 1]   # -1 since dates dont start from 0

        date_in_words = f'{day}{suffix} {month_year}'
        return date_in_words
    except Exception as e:
        print('zkdebug timestamp error', e)
        return timestamp


def calculate_updown(pct_changes: pd.Series, tolerance: int = 0, threshold: float = 0):
    """ Calculates the average closing price over a user defined period for the specified stock

    Args:
        data (pd.Series): stock close prices for specified ticker over user-defined period
        window (int): the amount of data points being calculated, defaults to 5
        tolerance only exceeds when its in a row
    Returns:
        (dict): contains
    """
    try:
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
        up_mask = values > 0
        down_mask = values < 0
        zero_mask = values == 0

        # Check if abs(value) exceeds threshold percentage
        if threshold is not None and threshold != 0:
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
            current_streak = 1          # Streak counter
            tolerance_left = tolerance  # Tolerance remaining, 0 means out of tolerance

            streak_start = 0            # Start of best streak
            streak_end = 0              # End of best streak

            # Single pass through
            for i in range(n):
                # print(f'{i}, value= {values[i]}')
                # Check if exceeds threshold in opposite direction
                if threshold_mask[i] and not direction_mask[i]:
                    print(f'{i}, {values[i]}, threshold exceeded')
                    # Record new max only when resetting streak
                    if current_streak > max_streak:
                        max_streak = current_streak
                        # Record start+end date
                        streak_end = i
                        streak_start = max(i - max_streak + 1, 0)
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
                    print(f'{i}, {values[i]}, continue and refresh, streak of {current_streak+1}')
                    current_streak += 1
                    tolerance_left = tolerance  # Reset tolerance
                # check if element i is 0, treat as neutral value
                elif zero_mask[i]:
                    print(f'{i}, {values[i]}, continue but 0, streak of {current_streak+1}')
                    current_streak += 1         # No resetting of tolerance
                # check if we can forgive the opposite direction
                elif tolerance_left > 0:
                    print(f'{i}, {values[i]}, continue but tolerate with {tolerance_left}, streak of {current_streak+1}')
                    current_streak += 1   
                    tolerance_left -= 1         # consume one tolerance
                # check if streak breaks
                else:
                    #current_streak += 1
                    print(f'{i}, {values[i]}, ends at {current_streak}, reset streak, wrong direction and no toleration')
                    # Trimming leading and trailing 0s, opposite directions
                    try:
                        streak_end = i - 1
                        streak_start = max(i - current_streak -1, 0)
                        print("#============================================")
                        print(f"testing out, current:{current_streak}, streak breaking for is_up = {is_up}")
                        print(f"streak start: {streak_start} and streak end: {streak_end}")
                        for j in range(streak_start, streak_end + 1):
                            print(f'element index: {j} with {values[j]}')
                        print("#============================================")

                    except Exception as e:
                        print(f'zkdebug trying to fix', e)
                    
                    
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
                    streak_start = max(i - max_streak + 1, 0)

            # Final check after loop completes
            if current_streak > max_streak:
                max_streak = current_streak

            # pct_changes.index gives a pd.Timestamp in string format
            streak_start = timestamp_to_words(pct_changes.index[streak_start])
            streak_end = timestamp_to_words(pct_changes.index[streak_end])

            return max_streak, streak_start, streak_end

        up_streak, up_start, up_end = calculate_streak(True)
        down_streak, down_start, down_end = calculate_streak(False)

        return {
            'up_streak': up_streak,
            'up_start': up_start,
            'up_end': up_end,
            'down_streak': down_streak,
            'down_start': down_start,
            'down_end': down_end
        }
    except Exception as e:
        print('zkdebuginsideexcept', e)