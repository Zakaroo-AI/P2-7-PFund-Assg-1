import pandas as pd
import numpy as np

def find_streaks_vectorized_optimized(pct_changes,
                                     tolerance: int = 0,
                                     threshold_pct: float = None):
    """
    Vectorized O(n) approach using NumPy for maximum performance.
    Corrected to only record maximum when streaks are confirmed.
    """
    # LINE 1: Convert to numpy array for speed
    # Why: Direct array access is faster than pandas Series operations
    values = pct_changes.values
    n = len(values)
    
    # LINE 2: Handle edge case
    # Why: Cannot form streaks with less than 2 data points
    if n < 2:
        return 0, 0
    
    # LINE 3: Precompute boolean masks
    # Why: Vectorized operations are 10-100x faster than element-wise conditionals
    up_mask = values > 0
    down_mask = values < 0
    zero_mask = values == 0
    
    # LINE 4: Precompute threshold violations
    # Why: Single computation avoids repeated calculations in loop
    if threshold_pct is not None:
        threshold_mask = np.abs(values) > threshold_pct
    else:
        threshold_mask = np.zeros_like(values, dtype=bool)
    
    def vectorized_streak_length(is_up: bool):
        # LINE 5: Select direction mask
        # Why: Unified condition checking for entire streak calculation
        direction_mask = up_mask if is_up else down_mask
        
        # LINE 6: Initialize tracking variables
        max_len = 1  # Maximum confirmed streak length
        current_len = 0  # Current potential streak length
        current_tol = tolerance  # Remaining tolerance budget
        
        # LINE 7: Track the start of current potential streak
        # NEW: Helps with edge trimming later
        streak_start = 0
        
        # LINE 8: Single pass through all data points
        for i in range(n):
            # LINE 9: Check for threshold violation
            if threshold_mask[i]:
                # CRITICAL: Record maximum BEFORE resetting (streak is broken)
                if current_len > max_len:
                    max_len = current_len
                # Reset due to threshold violation
                current_len = 0
                current_tol = tolerance
                streak_start = i + 1  # Next potential start
                continue
                
            # LINE 10: Check if current point continues streak
            if direction_mask[i]:
                # Valid move in intended direction
                current_len += 1
                current_tol = tolerance  # Refresh tolerance
            # LINE 11: Check if we can use tolerance
            elif current_tol > 0 and not zero_mask[i]:
                # Opposite move within tolerance
                current_len += 1
                current_tol -= 1
            # LINE 12: Streak breaks (no tolerance and invalid move)
            else:
                # CRITICAL: Only update max_len when streak is confirmed broken
                if current_len > max_len:
                    max_len = current_len
                
                # Start new streak if current point is valid
                if direction_mask[i]:
                    current_len = 1
                    streak_start = i
                else:
                    current_len = 0
                    streak_start = i + 1
                current_tol = tolerance
        
        # LINE 13: Final check after loop completes
        # Why: The last streak might extend to end of data and be valid
        if current_len > max_len:
            max_len = current_len
        

        
        return max_len
    
    # LINE 19: Calculate streaks for both directions
    up_streak = vectorized_streak_length(True)
    down_streak = vectorized_streak_length(False)
    
    return up_streak, down_streak