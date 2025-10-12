import pandas as pd

def timestamp_to_words(timestamp: str):
    try:
        timestamp = pd.Timestamp(timestamp)
        month_year = timestamp.strftime('%B %Y')  # eg January 2025
        
        day = timestamp.day
        suffixes = ('st', 'nd', 'rd')

        if (4 <= day <= 20) or (24 <= day <= 30):
            suffix = 'th'
        else:
            suffix = suffixes[(day % 10) - 1]

        return f'{day}{suffix} {month_year}'
    except Exception as e:
        print('zkdebug timestamp error', e)
        return timestamp


def calculate_updown(pct_changes: pd.Series, tolerance: int = 1, threshold: float = 0.5):
    """
    Calculates the longest upward and downward streaks in daily returns.

    Logic
    -----
    - Same direction → continue, reset tolerance
    - Flat (0%) → continue, no tolerance reset
    - Opposite and small (≤ threshold) → continue, consume 1 tolerance
    - Opposite and big (> threshold) → end streak immediately
    - If tolerance == 0 and opposite move → end streak immediately

    Parameters
    ----------
    pct_changes : pd.Series
        Daily % changes in closing price.
    tolerance : int
        Number of tolerated small opposite moves before streak breaks.
    threshold : float
        Defines what counts as a “big opposite move” (%).

    Returns
    -------
    dict
        {
            'up_streak': int,
            'up_start': str,
            'up_end': str,
            'down_streak': int,
            'down_start': str,
            'down_end': str
        }
    """

    def calculate_streak(direction='up'):
        current_streak = 0
        max_streak = 0
        tolerance_left = tolerance
        start_idx = 0
        best_start = None
        best_end = None

        for i, r in enumerate(pct_changes):
            # Same direction
            if (direction == 'up' and r > 0) or (direction == 'down' and r < 0):
                current_streak += 1
                tolerance_left = tolerance
                continue

            # Flat move
            if abs(r) < 1e-9:
                current_streak += 1
                continue

            # Opposite direction
            if (direction == 'up' and r < 0) or (direction == 'down' and r > 0):
                if abs(r) > threshold:
                    # Big move → break immediately
                    if current_streak > max_streak:
                        max_streak = current_streak
                        best_start = start_idx
                        best_end = i - 1
                    current_streak = 0
                    tolerance_left = tolerance
                    start_idx = i + 1
                    continue

                # Small opposite move (within threshold)
                if tolerance_left > 0:
                    tolerance_left -= 1
                    current_streak += 1
                else:
                    # No tolerance left → break
                    if current_streak > max_streak:
                        max_streak = current_streak
                        best_start = start_idx
                        best_end = i - 1
                    current_streak = 0
                    tolerance_left = tolerance
                    start_idx = i + 1

        # Final check after loop
        if current_streak > max_streak:
            max_streak = current_streak
            best_start = start_idx
            best_end = len(pct_changes) - 1

        # Convert to friendly format
        start_date = timestamp_to_words(pct_changes.index[best_start]) if best_start is not None else None
        end_date = timestamp_to_words(pct_changes.index[best_end]) if best_end is not None else None

        return max_streak, start_date, end_date

    # Compute both directions
    up_streak, up_start, up_end = calculate_streak('up')
    down_streak, down_start, down_end = calculate_streak('down')

    return {
        'up_streak': up_streak,
        'up_start': up_start,
        'up_end': up_end,
        'down_streak': down_streak,
        'down_start': down_start,
        'down_end': down_end,
    }