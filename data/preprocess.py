import pandas as pd


def align_dfs(dfs, on='Date'):
    """Simple alignment: outer join on Date and forward-fill missing values. Returns list of aligned dfs."""
    if not dfs:
        return []
    merged = dfs[0].set_index(on)
    for df in dfs[1:]:
        merged = merged.join(df.set_index(on)[['Close']], how='outer', rsuffix='_r')
    merged = merged.sort_index().ffill().reset_index()
    return merged