# plotting/plot_prices.py
from typing import List
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from indicators.registry import apply_indicator
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
    - indicator_key: 'sma', 'ema', 'rsi', 'macd', 'close' or None (treat close and None the same)
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
            row_heights=[0.4, 0.6],
            specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        )
    else:
        # single plot: price + optional overlay indicators
        fig = make_subplots(rows=1, cols=1)

    # Add price traces
    for df, label in zip(clean_dfs, labels):
        # Conditional hover: hide when DailyR is active
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

#========================================= Daily Returns =========================================#
    elif indicator_key == "dailyr":
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
                        bordercolor="rgba(0,0,0,0.1)",
                        font=dict(color="black", size=12, family="Arial"),
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
#========================================= Daily Returns =========================================#


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

      // Create a controls container and simple styling
      var ctrl = document.createElement('div');
      ctrl.id = '{plot_id}-controls';
      ctrl.style.margin = '8px 0';
      ctrl.style.fontFamily = 'Arial, sans-serif';
      ctrl.style.fontSize = '13px';

      // Create Select All / Clear All buttons
      var btnAll = document.createElement('button');
      btnAll.textContent = 'Select all';
      btnAll.style.marginRight = '8px';
      btnAll.onclick = function(e) {
        e.preventDefault();
        for (var i = 0; i < gd.data.length; i++) {
          Plotly.restyle(gd, {'visible': true}, [i]);
          var cb = document.getElementById('{plot_id}-cb-' + i);
          if (cb) cb.checked = true;
        }
      };
      var btnNone = document.createElement('button');
      btnNone.textContent = 'Clear all';
      btnNone.style.marginRight = '12px';
      btnNone.onclick = function(e) {
        e.preventDefault();
        for (var i = 0; i < gd.data.length; i++) {
          Plotly.restyle(gd, {'visible': 'legendonly'}, [i]);
          var cb = document.getElementById('{plot_id}-cb-' + i);
          if (cb) cb.checked = false;
        }
      };

      ctrl.appendChild(btnAll);
      ctrl.appendChild(btnNone);

      // Create inline checkbox list for every trace (only traces are toggleable)
      for (var i = 0; i < gd.data.length; i++) {
        (function(i) {
          var tr = gd.data[i];
          var label = document.createElement('label');
          label.style.marginRight = '10px';
          label.style.whiteSpace = 'nowrap';
          label.style.display = 'inline-flex';
          label.style.alignItems = 'center';

          var cb = document.createElement('input');
          cb.type = 'checkbox';
          cb.id = '{plot_id}-cb-' + i;

          // Checked if trace is visible (not 'legendonly' or false)
          cb.checked = (tr.visible !== 'legendonly' && tr.visible !== false);

          cb.onchange = function() {
            var vis = this.checked ? true : 'legendonly';
            Plotly.restyle(gd, {'visible': vis}, [i]);
          };

          var txt = document.createTextNode(' ' + (tr.name || ('trace ' + i)));
          label.appendChild(cb);
          label.appendChild(txt);

          ctrl.appendChild(label);
        })(i);
      }

      // Insert the controls just before the plot
      gd.parentNode.insertBefore(ctrl, gd);
    })();
    """


    # Return HTML fragment; post_script will be injected with the correct plot div id.
    # include_plotlyjs="cdn" keeps the same behaviour as before (loads plotly from CDN)
    if indicator_key == "dailyr":
        return pio.to_html(fig, full_html=False, include_plotlyjs="cdn")
    
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", post_script=post_script)