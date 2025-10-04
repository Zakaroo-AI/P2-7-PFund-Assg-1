# app.py
from flask import Flask, render_template, request
import os
from werkzeug.utils import secure_filename

from data.fetch import get_stock_data
from indicators.registry import apply_indicator, get_indicator_keys, get_indicator_spec
from plotting.plot_prices import plot_close_prices
from utils.validation import allowed_file, validate_csv_columns

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _save_upload(file_storage):
    """
    Save uploaded file and return file path.
    """
    if file_storage and file_storage.filename:
        filename = secure_filename(file_storage.filename)
        if not allowed_file(filename):
            raise ValueError("File type not allowed")
        path = os.path.join(UPLOAD_FOLDER, filename)
        file_storage.save(path)
        return path
    return None


def _collect_data_sources(form, files):
    """
    Return lists: dfs, labels
    Accepts up to two sources (file1/ticker1 and file2/ticker2)
    """
    sources = [
        ("file1", "ticker1", "source 1"),
        ("file2", "ticker2", "source 2"),
    ]
    dfs = []
    labels = []

    for file_key, ticker_key, default_label in sources:
        uploaded = files.get(file_key)
        ticker = form.get(ticker_key, "").strip() or None
        if uploaded and uploaded.filename:
            # save and validate
            path = _save_upload(uploaded)
            # raise on invalid CSV columns
            validate_csv_columns(path)
            df, label = get_stock_data(filepath=path)
            dfs.append(df)
            labels.append(label or os.path.basename(path))
        elif ticker:
            df, label = get_stock_data(ticker=ticker)
            dfs.append(df)
            labels.append(label or ticker.upper())

    return dfs, labels


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            indicator_key = request.form.get("indicator")  # e.g. 'sma', 'rsi'
            # optional params (if you want to expose these in the UI later)
            indicator_params = {}
            # For example, you could accept a window input with name 'window'
            if "window" in request.form:
                try:
                    indicator_params["window"] = int(request.form.get("window"))
                except Exception:
                    pass
            if "period" in request.form:
                try:
                    indicator_params["period"] = int(request.form.get("period"))
                except Exception:
                    pass

            dfs, labels = _collect_data_sources(request.form, request.files)
            if not dfs:
                return render_template(
                    "index.html",
                    error="Please upload at least one CSV or enter at least one ticker.",
                    indicators=get_indicator_keys(),
                )

            # Apply indicator to each df (idempotent)
            processed_dfs = [
                apply_indicator(df, indicator_key, indicator_params) for df in dfs
            ]

            # Build interactive plot (HTML fragment)
            plot_div = plot_close_prices(
                processed_dfs, labels, indicator_key=indicator_key, indicator_params=indicator_params
            )

            return render_template(
                "results.html",
                plot_div=plot_div,
                indicator=indicator_key,
                labels = labels
            )
        except Exception as e:
            return render_template(
                "index.html",
                error=str(e),
                indicators=get_indicator_keys(),
            )

    # GET
    return render_template("index.html", indicators=get_indicator_keys())


if __name__ == "__main__":
    app.run(debug=True)
