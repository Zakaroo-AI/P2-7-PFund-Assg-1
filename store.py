# plotting/plot_prices.py
from typing import List
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _ensure_date_index(df: pd.DataFrame):
    # Keep Date column (not index) to make template-independent
    if "Date" not in df.columns:
        if hasattr(df.index, "astype"):
            df = df.reset_index()
        else:
            raise ValueError("DataFrame must contain a 'Date' column")
    df = df.sort_values("Date").reset_index(drop=True)
    return df


def plot_close_prices(
    dfs: List[pd.DataFrame],
    labels: List[str],
    indicator_key: str | None = None,
    indicator_params: dict | None = None,
) -> str:
    """
    Build an interactive Plotly chart and return HTML div fragment.

    - dfs: list of DataFrames (each must contain 'Date' and 'Close')
    - labels: list of labels for legends
    - indicator_key: 'sma', 'ema', 'rsi', 'macd' or None
    - indicator_params: indicator-specific params (window, period, etc.)
    """
    indicator_key = indicator_key or None
    indicator_params = indicator_params or {}

    # Normalize dataframes
    clean_dfs = []
    for df in dfs:
        dfc = _ensure_date_index(df.copy())
        # Convert date to string or to datetime is fine for plotly
        if not pd.api.types.is_datetime64_any_dtype(dfc["Date"]):
            dfc["Date"] = pd.to_datetime(dfc["Date"], errors="coerce", utc=True)
        clean_dfs.append(dfc)

    # Choose layout depending on indicator
    if indicator_key in ("rsi", "macd"):
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        )
    else:
        # single plot: price + optional overlay indicators
        fig = make_subplots(rows=1, cols=1)

    # Add price traces
    for df, label in zip(clean_dfs, labels):
        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name=f"{label} Close",
                hovertemplate="%{x}<br>Close: %{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

    # Add indicator traces
    if indicator_key in ("sma", "ema"):
        # overlay a single line per df; indicator column named by convention 'SMA_<n>' or 'EMA_<n>'
        key = indicator_key.upper()
        window = indicator_params.get("window") or (indicator_params.get("period") or 20)
        colname = f"{key}_{window}"
        for df, label in zip(clean_dfs, labels):
            if colname in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["Date"],
                        y=df[colname],
                        mode="lines",
                        name=f"{label} {colname}",
                        hovertemplate="%{x}<br>%{y:.2f}<extra></extra>",
                    ),
                    row=1,
                    col=1,
                )

    elif indicator_key == "rsi":
        # RSI: add lines in row 2
        period = indicator_params.get("period", 14)
        rsi_col = f"RSI_{period}"
        for df, label in zip(clean_dfs, labels):
            if rsi_col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["Date"],
                        y=df[rsi_col],
                        mode="lines",
                        name=f"{label} {rsi_col}",
                        hovertemplate="%{x}<br>%{y:.2f}<extra></extra>",
                    ),
                    row=2,
                    col=1,
                )
        # add horizontal lines at 30/70
        fig.add_hline(y=70, line_dash="dash", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", row=2, col=1)
        fig.update_yaxes(range=[0, 100], row=2, col=1, title_text="RSI")

    elif indicator_key == "macd":
        # MACD: add MACD line and signal line + histogram in row 2
        for df, label in zip(clean_dfs, labels):
            if "MACD" in df.columns and "MACD_signal" in df.columns and "MACD_hist" in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df["Date"],
                        y=df["MACD"],
                        mode="lines",
                        name=f"{label} MACD",
                        hovertemplate="%{x}<br>%{y:.4f}<extra></extra>",
                    ),
                    row=2,
                    col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        x=df["Date"],
                        y=df["MACD_signal"],
                        mode="lines",
                        name=f"{label} MACD_signal",
                        hovertemplate="%{x}<br>%{y:.4f}<extra></extra>",
                    ),
                    row=2,
                    col=1,
                )
                fig.add_trace(
                    go.Bar(
                        x=df["Date"],
                        y=df["MACD_hist"],
                        name=f"{label} MACD_hist",
                        marker_line_width=0,
                        opacity=0.6,
                        hovertemplate="%{x}<br>%{y:.4f}<extra></extra>",
                    ),
                    row=2,
                    col=1,
                )

    # Layout tweaks
    fig.update_layout(
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",  # This is the key setting for shared hover
        margin=dict(l=50, r=20, t=50, b=50),
        template="plotly_white",
    )
    
    # Configure x-axes for cross-subplot interaction
    fig.update_xaxes(
        rangeslider_visible=False,
        showspikes=True,
        spikemode='across',
        spikesnap='cursor',
        spikethickness=1,
        spikedash='solid',
        spikecolor='gray'
    )
    
    # Also update y-axes to show spikes
    fig.update_yaxes(showspikes=True, spikemode='across', spikethickness=1)

    # Return an HTML fragment you can place directly into the Jinja template
    return fig.to_html(full_html=False, include_plotlyjs="cdn")