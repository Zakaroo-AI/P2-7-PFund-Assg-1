import pandas as pd

def timestamp_to_words(timestamp: str):
    try:
        timestamp = pd.Timestamp(timestamp)
        month_year = timestamp.strftime('%B %Y')
        day = timestamp.day
        suffixes = ('st', 'nd', 'rd')

        if (4 <= day <= 20) or (24 <= day <= 30):
            suffix = 'th'
        else:
            suffix = suffixes[(day % 10) - 1]

        return f'{day}{suffix} {month_year}'
    except Exception as e:
        return timestamp


def calculate_updown(pct_changes: pd.Series, tolerance: int = 1, threshold: float = 0.5):
    """
    Calculate the longest upward and downward streaks in daily percent changes.

    Logic:
      * Same direction → continue, reset tolerance
      * Flat (0%) → continue, do NOT reset tolerance
      * Small opposite (<= threshold) → continue, consume 1 tolerance
      * Large opposite (> threshold) → break streak immediately
      * If tolerance == 0 → no forgiveness, any opposite move breaks streak
    """

    # --- Validate inputs ---
    if pct_changes is None or len(pct_changes) == 0:
        return {
            "up_streak": 0, "up_start": None, "up_end": None,
            "down_streak": 0, "down_start": None, "down_end": None,
        }

    if tolerance < 0:
        raise ValueError("tolerance must be >= 0")

    pct = pct_changes.dropna()
    n = len(pct)
    values = pct.values
    idx = pct.index

    def calc(direction: str):
        current = 0
        max_streak = 0
        tol_left = tolerance
        current_start = None
        best_start = None
        best_end = None

        for i, v in enumerate(values):
            # Determine direction
            if direction == "up":
                same_dir = v > 0
                opposite_dir = v < 0
            else:  # down
                same_dir = v < 0
                opposite_dir = v > 0

            # --- Same direction ---
            if same_dir:
                if current == 0:
                    current_start = i
                current += 1
                tol_left = tolerance  # reset tolerance
                continue

            # --- Flat (0%) ---
            if abs(v) < 1e-9:
                if current == 0:
                    current_start = i
                current += 1
                continue

            # --- Opposite direction ---
            if opposite_dir:
                if abs(v) > threshold:
                    # Big opposite move breaks streak
                    if current > max_streak:
                        max_streak = current
                        best_start = current_start
                        best_end = i - 1
                    current = 0
                    tol_left = tolerance
                    current_start = None
                    continue

                # Handle small opposite move
                if tolerance == 0:
                    # No forgiveness allowed — break immediately
                    if current > max_streak:
                        max_streak = current
                        best_start = current_start
                        best_end = i - 1
                    current = 0
                    current_start = None
                    continue

                # Consume tolerance if available
                if tol_left > 0:
                    if current == 0:
                        current_start = i
                    current += 1
                    tol_left -= 1
                else:
                    if current > max_streak:
                        max_streak = current
                        best_start = current_start
                        best_end = i - 1
                    current = 0
                    tol_left = tolerance
                    current_start = None

        # Finalize last streak
        if current > max_streak:
            max_streak = current
            best_start = current_start
            best_end = n - 1

        if best_start is None:
            return 0, None, None

        start_date = timestamp_to_words(idx[best_start])
        end_date = timestamp_to_words(idx[best_end])
        return max_streak, start_date, end_date

    # Compute both
    up_len, up_start, up_end = calc("up")
    down_len, down_start, down_end = calc("down")

    return {
        "up_streak": up_len,
        "up_start": up_start,
        "up_end": up_end,
        "down_streak": down_len,
        "down_start": down_start,
        "down_end": down_end,
    }