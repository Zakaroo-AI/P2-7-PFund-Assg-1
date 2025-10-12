# plotting/plot_prices.py
from typing import List
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

#========================================= Presets =========================================#
def _ensure_date_index(df: pd.DataFrame):
    """
    Ensure the DataFrame contains a 'Date' column and is sorted by date.

    This helper is used to normalize input data before plotting.  
    It resets the index if necessary and ensures that 'Date' exists and is sorted chronologically.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame that should contain a 'Date' column or have datetime index.

    Returns
    -------
    pd.DataFrame
        Cleaned and sorted DataFrame with a 'Date' column in ascending order.

    Raises
    ------
    ValueError
        If the input DataFrame has no 'Date' column and the index cannot be reset properly.
    """
    if "Date" not in df.columns:
        if hasattr(df.index, "astype"):
            df = df.reset_index()
        else:
            raise ValueError("DataFrame must contain a 'Date' column")
    df = df.sort_values("Date").reset_index(drop=True)
    return df
#========================================= Presets =========================================#

#========================================= Plot & Graph Generation =========================================#
def plot_close_prices(
    dfs: List[pd.DataFrame],
    labels: List[str],
    indicator_key: str | None = None,
    indicator_params: dict | None = None,
) -> str:
    """
    Generate an interactive Plotly chart for stock prices and indicators.

    This function takes one or more price DataFrames, applies optional technical indicators,
    and returns an HTML string containing an interactive Plotly plot.  
    The plot supports overlays like SMA, EMA, RSI, MACD, and Daily Returns visualization.

    Parameters
    ----------
    dfs : list of pd.DataFrame
        List of DataFrames, each containing at least 'Date' and 'Close' columns.
    labels : list of str
        List of labels corresponding to each DataFrame for legend display.
    indicator_key : str, optional
        Type of indicator to display. Supported values:
        - ``'sma'`` : Simple Moving Average
        - ``'ema'`` : Exponential Moving Average
        - ``'rsi'`` : Relative Strength Index
        - ``'macd'`` : Moving Average Convergence Divergence
        - ``'dailyr'`` : Daily Returns visualization
        - ``None`` : Plot raw close prices only.
    indicator_params : dict, optional
        Extra parameters passed to indicator computation (e.g., window size, period, etc.).

    Returns
    -------
    str
        HTML fragment containing the generated Plotly figure.
        This can be directly embedded in web pages or rendered in notebooks.

    Notes
    -----
    - The function dynamically adjusts subplot layout depending on the indicator.
    - For ``'dailyr'`` mode, positive and negative returns are color-coded (green/red),
      and a hover tooltip summarizes each day’s change.
    - RSI and MACD modes add secondary plots below the price chart.
    - A small checkbox control panel is inserted above the plot (for non-dailyr modes)
      to toggle visibility of traces interactively.
    """
    indicator_key = indicator_key or None
    indicator_params = indicator_params or {}

    # Normalize dataframes
    clean_dfs = []
    for df in dfs:
        """
        Normalize and prepare each DataFrame before plotting.

        - Ensures the presence of a 'Date' column.
        - Converts non-datetime date columns into datetime (UTC-safe).
        - Sorts all records by date ascending.

        Output
        ------
        clean_dfs : list of pd.DataFrame
            List of preprocessed DataFrames ready for plotting.
        """
        dfc = _ensure_date_index(df.copy())
        # Convert date to string or to datetime is fine for plotly
        if not pd.api.types.is_datetime64_any_dtype(dfc["Date"]):
            dfc["Date"] = pd.to_datetime(dfc["Date"], errors="coerce", utc=True)
        clean_dfs.append(dfc)

#========================================= Create Layout Based on Key Type =========================================#
    # Choose layout depending on indicator
    if indicator_key in ("rsi", "macd"):
        """
        Decide subplot configuration based on the selected indicator.

        - RSI and MACD require two rows (main price chart + indicator below).
        - Other indicators or plain Close plots use a single row.
        """
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.4, 0.6],
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        )
    else:
        # single plot: price + optional overlay indicators
        fig = make_subplots(rows=1, cols=1)

#========================================= Add Base Close Price Trace =========================================#
    for df, label in zip(clean_dfs, labels):
        """
        Plot the base 'Close' price line for each dataset.

        Behavior
        --------
        - If `indicator_key == "dailyr"`, hover info is hidden
        (since hover details are handled by a separate overlay line).
        - Otherwise, show date and price on hover.

        Each trace is added as a line in the first subplot.
        """
        close_hover_args = (
            dict(hoverinfo="skip") if indicator_key == "dailyr"
            else dict(hovertemplate="%{x|%Y-%m-%d}<br>Close: %{y:.2f}<extra></extra>")
        )

        fig.add_trace(
            go.Scatter(
                x=df["Date"],
                y=df["Close"],
                mode="lines",
                name=f"{label} Close",
                **close_hover_args,   # ✅ Let this fully control hover behavior
                showlegend=(indicator_key != "dailyr"),
            ),
            row=1,
            col=1,
        )

#========================================= SMA & EMA =========================================#
    if indicator_key in ("sma", "ema"):
        """
        Plot overlay indicators for Simple Moving Average (SMA) or
        Exponential Moving Average (EMA).

        Each DataFrame is expected to contain a column:
            - SMA_<window>  or  EMA_<window>
        where <window> comes from `indicator_params["window"]` or `["period"]`.

        Example
        -------
        If `indicator_key="sma"` and `window=20`,
        column name should be 'SMA_20'.
        """
        key = indicator_key.upper()
        
        if indicator_key == 'sma':
            window = indicator_params.get('window', 5)
        else:
            window = indicator_params.get('interval', 5)
        colname = f"{key}_{int(window)}"
        print('zkdebug10', df[colname])
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

#========================================= RSI =========================================#
    elif indicator_key == "rsi":
        """
        Plot MACD (Moving Average Convergence Divergence) indicator.

        Expected Columns
        ----------------
        - MACD
        - MACD_signal
        - MACD_hist

        Behavior
        --------
        - Line plots for MACD and signal.
        - Bar plot for histogram (positive/negative divergence).
        """
        period = indicator_params.get("interval", 14)
        rsi_col = f"RSI_{int(period)}"
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

#========================================= MACD =========================================#
    elif indicator_key == "macd":
        """
        Plot MACD (Moving Average Convergence Divergence) indicator.

        Expected Columns
        ----------------
        - MACD
        - MACD_signal
        - MACD_hist

        Behavior
        --------
        - Line plots for MACD and signal.
        - Bar plot for histogram (positive/negative divergence).
        """
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

#========================================= Daily Returns =========================================#
    elif indicator_key == "dailyr":
        """
        Plot colored segments and hover tooltips showing daily returns.

        Steps
        -----
        1. Color code:
            - Green if positive
            - Red if negative
        2. Draw color-changing line segments (visual only).
        3. Add an invisible overlay line for hover info with
        stylized tooltips (white box, black border).
        4. Optionally highlight Max Profit range (Buy → Sell window).

        Output
        ------
        - The y-axis title is updated to "Close Price (colored by Daily Return)".
        """
        for df, label in zip(clean_dfs, labels):
            # Extract info for calculations from df's Info column
            try:
                info = df.pop('Info')   # pop out column for a cleaner df
            except Exception as e:
                print('Updown plotting fail:', e)
                info = False

            # --- Color coding ---
            if "DailyR" not in df.columns:
                print("Daily Returns cannot be found.")
                continue
            
            df["Color"] = df["DailyR"].apply(lambda x: "green" if x >= 0 else "red")

            # --- Build color-changing segments (visual only, no hover) ---
            for i in range(1, len(df)):
                prev = df.iloc[i - 1]
                curr = df.iloc[i]
                if pd.isna(prev["Close"]) or pd.isna(curr["Close"]):
                    continue

                fig.add_trace(
                    go.Scatter(
                        meta={'component': 'segments'},
                        x=[prev["Date"], curr["Date"]],
                        y=[prev["Close"], curr["Close"]],
                        mode="lines",
                        line=dict(color=curr["Color"], width=2),
                        showlegend=False,
                        hoverinfo="skip",  # prevent hover duplication
                    ),
                    row=1,
                    col=1,
                )

            # --- Compute daily change and hover text ---
            df["PriceChange"] = df["Close"].diff()

            df["HoverText"] = df.apply(
                lambda row: (
                    f"<b><span style='color:green'>📈 Daily Return: +{row['DailyR']:.2f}% (+${abs(row['PriceChange']):.2f})</span></b>"
                    if row["DailyR"] >= 0
                    else f"<b><span style='color:red'>📉 Daily Return: {row['DailyR']:.2f}% (-${abs(row['PriceChange']):.2f})</span></b>"
                ),
                axis=1
            )

            # --- Invisible overlay line for hover info only ---
            fig.add_trace(
                go.Scatter(
                    meta={'component': 'hover'},
                    x=df["Date"],
                    y=df["Close"],
                    mode="lines",
                    line=dict(color="rgba(0,0,0,0)", width=6),  # invisible hover line
                    name=f"{label} Daily Return",
                    customdata=df["HoverText"],
                    hovertemplate=(
                        "<b>Date:</b> %{x|%Y-%m-%d}<br>"
                        "<b>Close:</b> %{y:.2f}<br>"
                        "%{customdata}<extra></extra>"
                    ),
                    hoverlabel=dict(
                        bgcolor="white",
                        bordercolor="rgba(0,0,0,0.7)",
                        font=dict(color="black", size=14, family="Arial"),
                        align="left",
                        namelength=0,
                    ),
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

            # --- 💰 Max Profit annotation ---
            try:
                buy_date, sell_date, buy_price, sell_price, price_diff, profit_pct = info.head(6).tolist()
                buy_date = pd.Timestamp(buy_date)
                sell_date = pd.Timestamp(sell_date)

                if pd.notna(buy_date) and pd.notna(sell_date) and buy_date != sell_date:
                    fig.add_shape(
                        type="rect",
                        x0=buy_date,
                        x1=sell_date,
                        y0=buy_price,
                        y1=sell_price,
                        line=dict(color="green", dash="dot"),
                        fillcolor="rgba(0,255,0,0.08)",
                        layer="below",
                    )

                    fig.add_annotation(
                        x=sell_date,
                        y=sell_price,
                        text=(
                            f"💰 <b>Max Profit</b><br>"
                            f"Buy: {pd.to_datetime(buy_date).date()} @ ${buy_price:.2f}<br>"
                            f"Sell: {pd.to_datetime(sell_date).date()} @ ${sell_price:.2f}<br>"
                            f"Gain: <b>{profit_pct:.2f}% (${price_diff:.2f})</b>"
                        ),
                        showarrow=True,
                        arrowhead=2,
                        ax=0,
                        ay=-60,
                        bgcolor="rgba(255,255,255,0.9)",
                        bordercolor="green",
                        borderwidth=1,
                        font=dict(color="green", size=12),
                    )
            except Exception:
                print("Error, max profit not found!")


        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode='lines',
                line=dict(color='green', width=3),
                name='Positive return',
                hoverinfo='skip'
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode='lines',
                line=dict(color='red', width=3),
                name='Negative return',
                hoverinfo='skip'
            )
        )
    # ===== Add Up/Down Streak Visualization =====
        try:
            from indicators.updown import calculate_updown

            tolerance = indicator_params.get("tolerance", 0)
            threshold = indicator_params.get("threshold", 0)

            for df, label in zip(clean_dfs, labels):
                # Ensure we have Daily Return computed
                if "DailyR" not in df.columns:
                    df["DailyR"] = df["Close"].pct_change() * 100

                # Calculate streak info
                streaks = calculate_updown(df.set_index("Date")["DailyR"], tolerance, threshold)

                # Convert start/end timestamps back to datetime
                up_start = pd.to_datetime(streaks["up_start"], errors="coerce")
                up_end = pd.to_datetime(streaks["up_end"], errors="coerce")
                down_start = pd.to_datetime(streaks["down_start"], errors="coerce")
                down_end = pd.to_datetime(streaks["down_end"], errors="coerce")

                y_min, y_max = df["Close"].min(), df["Close"].max()


                # --- Highlight longest upward streak ---
                if pd.notna(up_start) and pd.notna(up_end):
                    fig.add_shape(
                        type="rect",
                        x0=up_start,
                        x1=up_end,
                        y0=y_min,
                        y1=y_max,
                        fillcolor="rgba(0, 255, 0, 0.15)",
                        line=dict(color="green", dash="dot"),
                        layer="below",
                    )
                    fig.add_annotation(
                        x=up_end,
                        y=y_max,
                        text=f"📈 Up Streak: {streaks['up_streak']} days<br>{streaks['up_start']} → {streaks['up_end']}",
                        showarrow=False,
                        font=dict(color="green", size=11),
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="green",
                        borderwidth=1,
                    )

                # --- Highlight longest downward streak ---
                if pd.notna(down_start) and pd.notna(down_end):
                    fig.add_shape(
                        type="rect",
                        x0=down_start,
                        x1=down_end,
                        y0=y_min,
                        y1=y_max,
                        fillcolor="rgba(255, 0, 0, 0.15)",
                        line=dict(color="red", dash="dot"),
                        layer="below",
                        row=1, col=1,
                    )
                    fig.add_annotation(
                        x=down_end,
                        y=y_min,
                        text=f"📉 Down Streak: {streaks['down_streak']} days<br>{streaks['down_start']} → {streaks['down_end']}",
                        showarrow=False,
                        font=dict(color="red", size=11),
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="red",
                        borderwidth=1,
                        row=1, col=1,
                    )

        except Exception as e:
            print(f"[plot_prices] Error adding up/down streaks: {e}")

        # Match other charts’ axis and hover feel
        fig.update_yaxes(title_text="Close Price (colored by Daily Return)", row=1, col=1)

#========================================= Update Layout =========================================#
        """
        Apply consistent layout settings:
        - Plot height and margins
        - Unified hover mode for all non-DailyR plots
        - White background template
        - Spike lines (vertical crosshair) on both axes
        """
    # Layout tweaks
    fig.update_layout(
        height=700,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="closest" if indicator_key == "dailyr" else "x unified",
        margin=dict(l=50, r=20, t=50, b=50),
        template="plotly_white",
    )
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

    # Add a small post_script that inserts a control panel of checkboxes before the plot.
    # It uses the '{plot_id}' placeholder which plotly.io.to_html replaces with the generated div id.
   
    post_script = f"""
    document.addEventListener("DOMContentLoaded", function() {{
        if (typeof setupPlotControls === "function") {{
            setupPlotControls("{'{plot_id}'}");
        }}
    }});
    """

    # Return HTML fragment; post_script will be injected with the correct plot div id.
    # include_plotlyjs="cdn" keeps the same behaviour as before (loads plotly from CDN)
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", post_script=post_script)