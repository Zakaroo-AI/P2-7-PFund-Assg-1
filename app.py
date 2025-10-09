# app.py (FINAL — multi-dataset plotting + full preprocessed preview + summaries)
from flask import Flask, render_template, request
import os, copy
from werkzeug.utils import secure_filename
import pandas as pd
import yfinance as yf

from data.fetch import get_stock_data
from data.preprocess import preprocess_stock_data, align_dfs
from indicators.registry import apply_indicator, get_indicator_keys, get_indicator_spec
from plotting.plot_prices import plot_close_prices
from utils.validation import allowed_file, validate_csv_columns
from utils.helpers import filter_dataframe

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Cache for uploaded files
uploaded_cache = {
    "file1": None,
    "file2": None,
    "labels": {"file1": None, "file2": None},
    "filenames": {"file1": None, "file2": None},
}

# Indicator parameter tracking
indicator_params = {"viewing": None, "timeframe": None}

# Auto populate defaults
try:
    for indicator in get_indicator_keys():
        indicator_params[indicator] = copy.deepcopy(
            get_indicator_spec(indicator)["default_params"]
        )
except Exception as e:
    print("[WARN] Could not initialize indicators:", e)
    indicator_params = {}


@app.route("/", methods=["GET", "POST"])
def index():
    preprocessed_html = None
    show_preprocessed = None
    ticker_summaries = []

    if request.method == "POST":
        print("REQUEST METHOD:", request.method)
        print("FORM keys:", list(request.form.keys()))

        # Read form inputs 
        ticker1 = request.form.get("ticker1", "").strip() or None
        ticker2 = request.form.get("ticker2", "").strip() or None
        time_range = request.form.get("time_range") or indicator_params["timeframe"]
        indicator_key = request.form.get("indicator")
        show_preprocessed = request.form.get("show_preprocessed")

        if indicator_key:
            indicator_params["viewing"] = indicator_key
        else:
            indicator_key = indicator_params["viewing"]
        indicator_params["timeframe"] = time_range

        dfs, labels = [], []

        # Handle Uploaded CSVs 
        for file_field in ["file1", "file2"]:
            uploaded = request.files.get(file_field)
            if uploaded and uploaded.filename:
                filename = secure_filename(uploaded.filename)
                if not allowed_file(filename):
                    return render_template(
                        "index.html",
                        shown_indicator=indicator_key,
                        error=f"File not allowed: {filename}",
                    )

                save_path = os.path.join(UPLOAD_FOLDER, filename)
                uploaded.save(save_path)

                try:
                    validate_csv_columns(save_path, required_cols=["Date", "Close"])
                except Exception as e:
                    return render_template(
                        "index.html", shown_indicator=indicator_key, error=str(e)
                    )

                df, label = get_stock_data(filepath=save_path)
                if not label or label.lower() in ["data", "stock data"]:
                    label = os.path.splitext(filename)[0]

                df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True)
                df = df.sort_values("Date").reset_index(drop=True)
                df = preprocess_stock_data(df)

                uploaded_cache[file_field] = df
                uploaded_cache["labels"][file_field] = label

                display_name = label.replace("_", " ").title()
                ticker_summaries.append({
                    "name": display_name,
                    "symbol": label.upper(),
                    "price": None,
                    "change": None,
                    "pct": None,
                    "logo": None,
                })
            elif uploaded_cache[file_field] is not None:
                df = uploaded_cache[file_field]
                label = uploaded_cache["labels"][file_field]
                display_name = label.replace("_", " ").title()
                ticker_summaries.append({
                    "name": display_name,
                    "symbol": label.upper(),
                    "price": None,
                    "change": None,
                    "pct": None,
                    "logo": None,
                })
            else:
                continue

            df_filtered = filter_dataframe(df, source="file", option=time_range)
            dfs.append(df_filtered)
            labels.append(label)

        # Handle Tickers (AAPL, MSFT, etc.)
        for ticker in [ticker1, ticker2]:
            if ticker:
                try:
                    df, label = get_stock_data(ticker=ticker)
                    df = preprocess_stock_data(df)

                    # Fetch stock info summary 
                    try:
                        tk = yf.Ticker(ticker)
                        info = tk.info
                        short_name = info.get("shortName", label)
                        current_price = info.get("currentPrice")
                        previous_close = info.get("previousClose")
                        logo_url = info.get("logo_url")

                        change, pct_change = None, None
                        if current_price and previous_close:
                            change = round(current_price - previous_close, 2)
                            pct_change = round((change / previous_close) * 100, 2)

                        ticker_summaries.append({
                            "name": short_name,
                            "symbol": ticker.upper(),
                            "price": current_price,
                            "change": change,
                            "pct": pct_change,
                            "logo": logo_url,
                        })
                    except Exception as e:
                        print(f"[WARN] Could not fetch summary for {ticker}: {e}")

                except Exception as e:
                    return render_template(
                        "index.html",
                        shown_indicator=indicator_key,
                        error=f"Error fetching {ticker}: {e}",
                    )

                df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True)
                df = df.sort_values("Date").reset_index(drop=True)
                df_filtered = filter_dataframe(df, source="ticker", option=time_range)
                dfs.append(df_filtered)
                labels.append(ticker.upper())

        if not dfs:
            return render_template(
                "index.html",
                shown_indicator=indicator_key,
                error="No data provided. Please provide a ticker or upload a CSV.",
            )

        # Update Indicator Parameters 
        try:
            for key in request.form.keys():
                if indicator_key and key.startswith(indicator_key):
                    param = key.split("_", 1)[1]
                    indicator_params[indicator_key][param] = int(request.form.get(key))
        except Exception as e:
            print(f"[WARN] Parameter update error: {e}")

        #  Apply indicators per dataset (each CSV/ticker)
        applied = []
        for df, label in zip(dfs, labels):
            if df is None or df.empty:
                continue

            if indicator_key not in [None, "close"]:
                try:
                    df_with_ind = apply_indicator(
                        df,
                        indicator_key,
                        params=indicator_params.get(indicator_key, {}),
                    )
                except Exception as e:
                    print(f"[WARN] Indicator error on {label}: {e}")
                    df_with_ind = df.copy()
            else:
                df_with_ind = df.copy()

            applied.append(df_with_ind)

        # Align all processed DataFrames for consistent Date index 
        aligned_df = align_dfs(applied)

        # Ensure unique and descriptive labels
        cleaned_labels = []
        for i, label in enumerate(labels):
            if not label or label.lower() in ["data", "stock data"]:
                label = f"dataset_{i+1}"
            if label in cleaned_labels:
                label = f"{label}_{i+1}"
            cleaned_labels.append(label)
        labels = cleaned_labels

        
        if show_preprocessed:
            try:
                stacked_df = pd.concat(dfs, keys=labels, names=["Source", "Row"]).reset_index(level="Source")

                
                preview_list = []
                for label in labels:
                    subset = stacked_df[stacked_df["Source"] == label].head(20)
                    preview_list.append(subset)
                stacked_preview = pd.concat(preview_list)

                preprocessed_html = stacked_preview.to_html(classes="data-table", index=False)

                debug_path = os.path.join(BASE_DIR, "debug_stacked_preview.csv")
                stacked_df.to_csv(debug_path, index=False)
                print(f"[INFO] Stacked preview saved to: {debug_path}")
                print(f"[DEBUG] Sources included: {labels}")
            except Exception as e:
                print(f"[WARN] Could not generate stacked preview: {e}")

        # Plot (all datasets) 
        try:
            plot_div = plot_close_prices(
                applied,
                labels,
                indicator_key=indicator_key,
                indicator_params=indicator_params.get(indicator_key, {}),
            )
        except Exception as e:
            return render_template(
                "index.html", shown_indicator=indicator_key, error=f"Plotting error: {e}"
            )

        # Render Page 
        return render_template(
            "index.html",
            shown_indicator=indicator_key,
            params=indicator_params.get(indicator_key, {}),
            plot_div=plot_div,
            labels=labels,
            time_range=time_range,
            summaries=ticker_summaries,
            preprocessed_html=preprocessed_html,
            show_preprocessed=show_preprocessed,
        )

    # GET Request
    return render_template("index.html")


@app.route("/clear_cache")
def clear_cache():
    uploaded_cache["file1"] = None
    uploaded_cache["file2"] = None
    uploaded_cache["labels"] = {"file1": None, "file2": None}
    return "Cache cleared."


if __name__ == "__main__":
    app.run(debug=True)
