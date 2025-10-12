import pandas as pd

def checkDirection(val, threshold = 0):
    if abs(val) < threshold:
        return 0    # 0 = Neutral
    else:
        return 1 if val > 0 else -1     # 1 = Up, -1 = Down
    
    

def calculateStreaks(s1, tolerance_limit, threshold = 0):
    
    vals = list(s1)
    
    max_up = max_down = 0
    current_up = current_down = 0
    tolerance_up = tolerance_down = 0
    
    for val in vals:
        direction = checkDirection(val, threshold)

        # Up or Neutral
        if direction >= 0:  
            current_up += 1     # its an up day, increment
            #tolerance_up = 0
        # Down, and tolerance not exceeded yet
        elif tolerance_up < tolerance_limit:    
            tolerance_up += 1   # used one tolerance
            current_up += 1     # even though its a down day, tolerance forgives it
        # Down, but tolerance exceeded
        else:
            max_up = max(max_up, current_up)    # Change max_up if its surpassed
            current_up = tolerance_up = 0       # Reset for next streak

        # Down or Neutral
        if direction <= 0:
            current_down += 1   # its a down day, increment
            #tolerance_down = 0
        # Up, and tolerance not exceed yet
        elif tolerance_down < tolerance_limit:
            tolerance_down += 1
            current_down += 1
        # Up, but tolerance exceeded
        else:
            max_down = max(max_down, current_down)
            current_down = tolerance_down = 0

    # Check streaks for maximum at the last value
    max_up = max(max_up, current_up)
    max_down = max(max_down, current_down)

    return max_up, max_down

s = pd.Series([1, 2, -1, 3, 4, -2, -3, -4, 1, -1, -2, -3])
print(calculateStreaks(s, tolerance_limit=1, threshold = 0))
