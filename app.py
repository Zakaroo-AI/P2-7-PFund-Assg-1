# app.py (your version + News added at the end)
from flask import Flask, render_template, request, jsonify
import os, copy, requests, timeit
import pandas as pd
import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from data.fetch import get_stock_data
from data.preprocess import preprocess_stock_data, align_dfs
from indicators.registry import apply_indicator, get_indicator_keys, get_indicator_spec
from plotting.plot_prices import plot_close_prices
from utils.upload_handler import upload_handling
from utils.helpers import filter_dataframe

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Cache for uploaded files
uploaded_cache = {
    "file1": None,  # the uploaded file itself
    "file2": None,  
    "labels": {"file1": None, "file2": None},    # the label attached to the data
    "filenames": {"file1": None, "file2": None}, # the corresponding filename
}

ticker_cache = {}   #  ticker symbol: dataframe 

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
        ticker1 = request.form.get('ticker1', '').strip() or None
        ticker2 = request.form.get('ticker2', '').strip() or None
        time_range = request.form.get('time_range') or indicator_params['timeframe']
        remove_file = request.form.get('remove_file') or None

        indicator_key = request.form.get('indicator')
        show_preprocessed = request.form.get("show_preprocessed")

        if indicator_key:
            indicator_params["viewing"] = indicator_key
        else:
            indicator_key = indicator_params["viewing"]
        indicator_params["timeframe"] = time_range

        if remove_file:
            uploaded_cache[f'file{remove_file[-1]}'] = None
            uploaded_cache['filenames'][f'file{remove_file[-1]}'] = None

        dfs, labels = [], []

        # Handle Uploaded CSVs 
        for file_field in ["file1", "file2"]:   
            uploaded = request.files.get(file_field)
            if uploaded and uploaded.filename:
                save_path = os.path.join(UPLOAD_FOLDER, uploaded.filename)

                try:
                    df, label = upload_handling(uploaded, save_path)
                except Exception as e:
                    return render_template(
                        "index.html",
                        shown_indicator=indicator_key,
                        error = e,
                    )

                # if not allowed_file(filename):
                #     return render_template(
                #         "index.html",
                #         shown_indicator=indicator_key,
                #         error=f"File not allowed: {filename}",
                #     )

                # try:
                #     validate_csv_columns(save_path, required_cols=["Date", "Close"])
                # except Exception as e:
                #     return render_template(
                #         "index.html", shown_indicator=indicator_key, error=str(e)
                #     )

                # df, label = get_stock_data(filepath=save_path)
                # if not label or label.lower() in ["data", "stock data"]:
                #     label = os.path.splitext(filename)[0]

                # df["Date"] = pd.to_datetime(df["Date"], errors="coerce", utc=True)
                # df = df.sort_values("Date").reset_index(drop=True)
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
                    if ticker in ticker_cache.keys():
                        print(f'zkdebug: retrieving ticker {ticker} from ticker_cache')
                        df, label = ticker_cache[ticker], ticker
                    else:
                        print(f'zkdebug: query ticker {ticker} from yfinance api')
                        df, label = get_stock_data(ticker=ticker)
                        df = preprocess_stock_data(df)
                        ticker_cache[ticker] = df

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

        # Apply indicators 
        applied = []
        for df, label in zip(dfs, labels):
            if df is None or df.empty:
                continue
            if indicator_key not in [None, "close"]:
                try:
                    df_with_ind = apply_indicator(
                        df, indicator_key, params=indicator_params.get(indicator_key, {})
                    )
                except Exception as e:
                    print(f"[WARN] Indicator error on {label}: {e}")
                    df_with_ind = df.copy()
            else:
                df_with_ind = df.copy()
            applied.append(df_with_ind)

        aligned_df = align_dfs(applied)

        try:
            plot_div = plot_close_prices(
                applied, labels,
                indicator_key=indicator_key,
                indicator_params=indicator_params.get(indicator_key, {}),
            )
        except Exception as e:
            return render_template(
                "index.html", shown_indicator=indicator_key, error=f"Plotting error: {e}"
            )

        return render_template(
            "index.html",
            shown_indicator=indicator_key,
            params=indicator_params.get(indicator_key, {}),
            plot_div=plot_div,
            labels=labels,
            time_range=time_range,
            summaries=ticker_summaries,
            preprocessed_html=None,
        )

    return render_template("index.html")


@app.route("/clear_cache")
def clear_cache():
    uploaded_cache["file1"] = None
    uploaded_cache["file2"] = None
    uploaded_cache["labels"] = {"file1": None, "file2": None}
    return "Cache cleared."


# Auto Refresh Feature 
def _last_two_closes(ticker: str):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="5d", interval="1d").dropna()
        if len(hist) >= 2:
            return float(hist["Close"].iloc[-1]), float(hist["Close"].iloc[-2])
        elif len(hist) == 1:
            val = float(hist["Close"].iloc[-1])
            return val, val
        else:
            info = tk.info
            return info.get("currentPrice"), info.get("previousClose")
    except Exception:
        return None, None

@app.route("/auto_refresh")
def auto_refresh():
    ticker = (request.args.get("ticker") or "").upper()
    if not ticker:
        return jsonify({"error": "No ticker"}), 400
    last, prev = _last_two_closes(ticker)
    if not last:
        return jsonify({"error": "No data"}), 200
    change = round(last - prev, 2) if prev else None
    pct = round((change / prev) * 100, 2) if prev and prev != 0 else None
    return jsonify({"symbol": ticker, "price": last, "change": change, "pct": pct})


# News API 
@app.route("/get_news")
def news_feed():
    ticker = (request.args.get("ticker") or "").upper()
    if not ticker:
        return jsonify({"error": "No ticker"}), 400
    try:
        url = (
            "https://newsapi.org/v2/everything"
            f"?q={ticker}&language=en&pageSize=6&sortBy=publishedAt&apiKey=aa05b2ccb4c64460b52d26b97df74928"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        analyzer = SentimentIntensityAnalyzer()
        articles = []
        for a in data.get("articles", []):
            txt = f"{a.get('title','')} {a.get('description','')}"
            s = analyzer.polarity_scores(txt)
            articles.append({
                "title": a.get("title"),
                "url": a.get("url"),
                "description": a.get("description"),
                "source": (a.get("source") or {}).get("name"),
                "publishedAt": a.get("publishedAt"),
                "sentiment": s["compound"]
            })
        return jsonify({"articles": articles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
