# app.py (updated)
from flask import Flask, render_template, request, session
import os, json
from werkzeug.utils import secure_filename
import pandas as pd

from data.fetch import get_stock_data
from indicators.registry import apply_indicator, get_indicator_keys, get_indicator_spec
from plotting.plot_prices import plot_close_prices
from utils.validation import allowed_file, validate_csv_columns
from utils.helpers import filter_dataframe

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global cache to store uploaded data between requests
uploaded_cache = {
    "file1": None,
    "file2": None,
    "labels": {"file1": None, "file2": None}
}

@app.route('/', methods=['GET', 'POST'])
def index():
    indicators = get_indicator_keys()

    if request.method == 'POST':
        # Read form inputs
        ticker1 = request.form.get('ticker1', '').strip() or None
        ticker2 = request.form.get('ticker2', '').strip() or None
        indicator_key = request.form.get('indicator')  # 'sma', 'ema', ...
        time_range = request.form.get('time_range', '1Y')  # '1M','3M','6M','1Y','2Y'

        # collect datasets (list of DataFrames) and labels
        dfs = []
        labels = []

        # handle uploaded files
        for file_field in ['file1', 'file2']:
            uploaded = request.files.get(file_field)
            if uploaded and uploaded.filename:
                filename = secure_filename(uploaded.filename)
                if not allowed_file(filename):
                    return render_template('index.html', indicators=indicators, error=f'File not allowed: {filename}')
                
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                uploaded.save(save_path)

                # basic validation
                try:
                    validate_csv_columns(save_path, required_cols=['Date', 'Close'])
                except Exception as e:
                    return render_template('index.html', indicators=indicators, error=str(e))

                df, label = get_stock_data(filepath=save_path)
                # ensure Date parsed and sorted
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce', utc=True)
                df = df.sort_values('Date').reset_index(drop=True)

                # Update cache with uploaded data
                uploaded_cache[file_field] = df
                uploaded_cache["labels"][file_field] = label

            # retrieve pre-cached data if no data is uploaded
            elif uploaded_cache[file_field] is not None:
                df = uploaded_cache[file_field]
                label = uploaded_cache["labels"][file_field]

            else:
                continue

            df_filtered = filter_dataframe(df, source='file', option=time_range)
            dfs.append(df_filtered)
            labels.append(label)

        # handle tickers
        for ticker in [ticker1, ticker2]:
            if ticker:
                try:
                    df, label = get_stock_data(ticker=ticker)
                except Exception as e:
                    return render_template('index.html', indicators=indicators, error=f'Error fetching {ticker}: {e}')
                # ensure Date parsed and sorted
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce', utc=True)
                df = df.sort_values('Date').reset_index(drop=True)
                # apply filtering for ticker (latest N months)
                df_filtered = filter_dataframe(df, source='ticker', option=time_range)
                dfs.append(df_filtered)
                labels.append(label)

        if not dfs:
            return render_template('index.html', indicators=indicators, error='No data provided. Provide a ticker or upload a CSV.')

        # Apply indicator if provided
        try:
            indicator_params = get_indicator_spec(indicator_key)['default_params'] if indicator_key else {}
        except Exception:
            indicator_params = {}

        applied = []
        for df in dfs:
            if indicator_key:
                try:
                    df_with_ind = apply_indicator(df, indicator_key, params=indicator_params)
                except Exception as e:
                    return render_template('index.html', indicators=indicators, error=f'Indicator error: {e}')
            else:
                df_with_ind = df.copy()
            applied.append(df_with_ind)

        # Build plot
        try:
            plot_div = plot_close_prices(applied, labels, indicator_key=indicator_key, indicator_params=indicator_params)
        except Exception as e:
            return render_template('index.html', indicators=indicators, error=f'Plotting error: {e}')

        # Render the SAME index.html but include the plot fragment and labels.
        return render_template('index.html', indicators=indicators, plot_div=plot_div, labels=labels, time_range=time_range)

    # GET
    return render_template('index.html', indicators=get_indicator_keys())

@app.route('/clear_cache')
def clear_cache():
    uploaded_cache["file1"] = None
    uploaded_cache["file2"] = None
    uploaded_cache["labels"] = {"file1": None, "file2": None}
    return "Cache cleared."

if __name__ == '__main__':
    app.run(debug=True)
