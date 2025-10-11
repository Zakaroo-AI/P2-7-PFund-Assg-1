# plotting/plot_prices.py
from typing import List
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from indicators.registry import apply_indicator
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
        1. Compute Daily Return via `apply_indicator(df, "dailyr")`.
        2. Color code:
            - Green if positive
            - Red if negative
        3. Draw color-changing line segments (visual only).
        4. Add an invisible overlay line for hover info with
        stylized tooltips (white box, black border).
        5. Optionally highlight Max Profit range (Buy → Sell window).

        Output
        ------
        - The y-axis title is updated to "Close Price (colored by Daily Return)".
        """
        for df, label in zip(clean_dfs, labels):
            # Apply the indicator
            df = apply_indicator(df, "dailyr", indicator_params)
            if "DailyR" not in df.columns:
                continue

            # --- Color coding ---
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
            if not pd.isna(df["Buy_Date"].iloc[-1]) and not pd.isna(df["Sell_Date"].iloc[-1]):
                buy_date = df["Buy_Date"].iloc[-1]
                sell_date = df["Sell_Date"].iloc[-1]
                buy_price = df["Buy_Price"].iloc[-1]
                sell_price = df["Sell_Price"].iloc[-1]
                price_diff = df["Price_Diff"].iloc[-1]
                profit_pct = df["Max_Profit_Pct"].iloc[-1]

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
                        f"Buy: {buy_date.date()} @ ${buy_price:.2f}<br>"
                        f"Sell: {sell_date.date()} @ ${sell_price:.2f}<br>"
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
   
    post_script = r"""
    (function() {
    var gd = document.getElementById('{plot_id}');
    if (!gd) return;

    var MAX_CHECKBOXES = 40; // threshold to switch to grouped UI for large plots

    // Save original shapes & annotations for Max Profit toggle
    try {
        gd._orig_shapes = gd.layout && gd.layout.shapes ? JSON.parse(JSON.stringify(gd.layout.shapes)) : [];
        gd._orig_annos  = gd.layout && gd.layout.annotations ? JSON.parse(JSON.stringify(gd.layout.annotations)) : [];
    } catch (e) {
        gd._orig_shapes = [];
        gd._orig_annos  = [];
    }

    // Helper to create a styled wrapper for controls
    var ctrl = document.createElement('div');
    ctrl.id = '{plot_id}-controls';
    ctrl.style.margin = '8px 0';
    ctrl.style.fontFamily = 'Arial, sans-serif';
    ctrl.style.fontSize = '13px';

    // toggleable entries: {id, checkbox, indices}
    var toggleables = [];

    // Select all / Clear all buttons
    var btnAll = document.createElement('button');
    btnAll.textContent = 'Select all';
    btnAll.style.marginRight = '8px';
    btnAll.onclick = function(e) {
        e.preventDefault();
        toggleables.forEach(function(entry) {
        Plotly.restyle(gd, {'visible': true}, entry.indices);
        entry.checkbox.checked = true;
        });
    };
    var btnNone = document.createElement('button');
    btnNone.textContent = 'Clear all';
    btnNone.style.marginRight = '12px';
    btnNone.onclick = function(e) {
        e.preventDefault();
        toggleables.forEach(function(entry) {
        // use 'legendonly' so traces are hidden but legend remains consistent
        Plotly.restyle(gd, {'visible': 'legendonly'}, entry.indices);
        entry.checkbox.checked = false;
        });
    };

    ctrl.appendChild(btnAll);
    ctrl.appendChild(btnNone);

    // helper to create a checkbox + label
    function mkCheckbox(id, label, checked, onchange) {
        var wrap = document.createElement('label');
        wrap.style.marginRight = '12px';
        wrap.style.display = 'inline-flex';
        wrap.style.alignItems = 'center';

        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.id = id;
        cb.checked = checked;
        cb.style.marginRight = '6px';
        cb.addEventListener('change', onchange);

        var txt = document.createTextNode(label);
        wrap.appendChild(cb);
        wrap.appendChild(txt);
        return {wrap: wrap, checkbox: cb};
    }

    // Build groups from meta.component if present; otherwise fall back to name-based grouping
    var groups = {}; // key -> {indices: [], sampleName: string}
    for (var i = 0; i < gd.data.length; i++) {
        var tr = gd.data[i];
        var key = (tr && tr.meta && tr.meta.component) ? tr.meta.component : null;
        if (!key) {
        // try a conservative name-based heuristic for legacy plots
        if (tr && typeof tr.name === 'string' && /daily\s*return/i.test(tr.name)) {
            key = 'dailyr_unknown';
        } else {
            key = 'trace_by_index';
        }
        }
        if (!groups[key]) groups[key] = {indices: [], sampleName: (tr && tr.name) || null};
        groups[key].indices.push(i);
    }

    // Decide how to render controls:
    // - If 'segments' group exists and it's large, create a single grouped toggle for it.
    // - For other small groups or small total trace counts, create per-trace checkboxes.
    var totalTraces = gd.data.length;

    // If we have an explicit 'segments' group in meta, prefer grouped control
    if (groups['segments']) {
        var segIndices = groups['segments'].indices;
        var segLabel = 'Segments (' + segIndices.length + ')';
        var segDefaultChecked = (gd.data[segIndices[0]].visible !== 'legendonly' && gd.data[segIndices[0]].visible !== false);
        var segEntry = mkCheckbox('{plot_id}-segments', segLabel, segDefaultChecked, function() {
        var vis = this.checked ? true : false;
        Plotly.restyle(gd, {'visible': vis}, segIndices);
        });
        ctrl.appendChild(segEntry.wrap);
        toggleables.push({id: '{plot_id}-segments', checkbox: segEntry.checkbox, indices: segIndices});
    }

    // If a hover group exists, add an explicit hover toggle (usually small)
    if (groups['hover']) {
        var hovIdx = groups['hover'].indices;
        var hovDefaultChecked = (gd.data[hovIdx[0]].visible !== 'legendonly' && gd.data[hovIdx[0]].visible !== false);
        var hovEntry = mkCheckbox('{plot_id}-hover', 'Hover overlay', hovDefaultChecked, function() {
        var vis = this.checked ? true : false;
        Plotly.restyle(gd, {'visible': vis}, hovIdx);
        });
        ctrl.appendChild(hovEntry.wrap);
        toggleables.push({id: '{plot_id}-hover', checkbox: hovEntry.checkbox, indices: hovIdx});
    }

    // Add grouped toggles for any other groups that have many members,
    // and optionally per-trace checkboxes for small numbers.
    Object.keys(groups).forEach(function(k) {
        if (k === 'segments' || k === 'hover') return; // already handled
        var idxs = groups[k].indices;
        if (idxs.length === 0) return;
        if (idxs.length === 1 && totalTraces <= MAX_CHECKBOXES) {
        // small plot: create per-trace checkbox like the original behavior
        var i = idxs[0];
        var tr = gd.data[i];
        var name = tr && tr.name ? tr.name : 'trace ' + i;
        var defaultChecked = (tr.visible !== 'legendonly' && tr.visible !== false);
        var entry = mkCheckbox('{plot_id}-cb-' + i, name, defaultChecked, function() {
            var vis = this.checked ? true : 'legendonly';
            Plotly.restyle(gd, {'visible': vis}, [i]);
        });
        ctrl.appendChild(entry.wrap);
        toggleables.push({id: '{plot_id}-cb-' + i, checkbox: entry.checkbox, indices: [i]});
        } else if (idxs.length <= 6 && totalTraces <= MAX_CHECKBOXES) {
        // moderate group & small overall plot: per-trace checkboxes
        idxs.forEach(function(i) {
            var tr = gd.data[i];
            var name = tr && tr.name ? tr.name : 'trace ' + i;
            var defaultChecked = (tr.visible !== 'legendonly' && tr.visible !== false);
            var entry = mkCheckbox('{plot_id}-cb-' + i, name, defaultChecked, function() {
            var vis = this.checked ? true : 'legendonly';
            Plotly.restyle(gd, {'visible': vis}, [i]);
            });
            ctrl.appendChild(entry.wrap);
            toggleables.push({id: '{plot_id}-cb-' + i, checkbox: entry.checkbox, indices: [i]});
        });
        } else {
        // large group: add a grouped toggle that toggles all indices at once
        var label = (groups[k].sampleName ? groups[k].sampleName : k) + ' (' + idxs.length + ')';
        var defaultChecked = (gd.data[idxs[0]].visible !== 'legendonly' && gd.data[idxs[0]].visible !== false);
        var gEntry = mkCheckbox('{plot_id}-group-' + k, label, defaultChecked, function() {
            var vis = this.checked ? true : false;
            Plotly.restyle(gd, {'visible': vis}, idxs);
        });
        ctrl.appendChild(gEntry.wrap);
        toggleables.push({id: '{plot_id}-group-' + k, checkbox: gEntry.checkbox, indices: idxs});
        }
    });

    // Max Profit toggle (shapes + annotations) - always show if there were shapes/annos
    var hasShapes = (gd._orig_shapes && gd._orig_shapes.length > 0) || (gd._orig_annos && gd._orig_annos.length > 0);
    if (hasShapes) {
        var maxDefault = true;
        var maxEntry = mkCheckbox('{plot_id}-maxprofit', 'Max Profit', maxDefault, function() {
        if (this.checked) {
            Plotly.relayout(gd, {shapes: gd._orig_shapes, annotations: gd._orig_annos});
        } else {
            Plotly.relayout(gd, {shapes: [], annotations: []});
        }
        });
        ctrl.appendChild(maxEntry.wrap);
    }

    // insert the controls before the plot container
    gd.parentNode.insertBefore(ctrl, gd);
    })();
    """


    # Return HTML fragment; post_script will be injected with the correct plot div id.
    # include_plotlyjs="cdn" keeps the same behaviour as before (loads plotly from CDN)
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", post_script=post_script)