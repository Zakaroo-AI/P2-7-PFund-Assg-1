# app.py (updated)
from flask import Flask, render_template, request, session
import os, json, copy
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
    "labels": {"file1": None, "file2": None},   # ticker labels
    "filenames": {"file1": None, "file2": None}
}

# viewing: current indicator, retrievable across requests
indicator_params = {
    'viewing': None
}
# auto populating uploaded_cache's params dictionary with default parameters for each indicator
try:
    for indicator in get_indicator_keys():
        indicator_params[indicator] = copy.deepcopy(get_indicator_spec(indicator)["default_params"])
except:
    indicator_params = {}

#print('zkdebug', indicator_params)

@app.route('/', methods=['GET', 'POST'])
def index():
    # indicators = get_indicator_keys()

    if request.method == 'POST':
        print("REQUEST METHOD:", request.method)
        print("FORM keys:", list(request.form.keys()))
        print("RAW form:", request.form)   # shows MultiDict

        # continue with your normal logic...

        # Read form inputs
        ticker1 = request.form.get('ticker1', '').strip() or None
        ticker2 = request.form.get('ticker2', '').strip() or None
        time_range = request.form.get('time_range', '1Y')  # '1M','3M','6M','1Y','2Y'
        
        indicator_key = request.form.get('indicator')# 'sma', 'ema', ...

        if indicator_key:
            indicator_params['viewing'] = indicator_key
        else:
            indicator_key = indicator_params['viewing']

        # collect datasets (list of DataFrames) and labels
        dfs = []
        labels = []

        # handle uploaded files
        for file_field in ['file1', 'file2']:
            uploaded = request.files.get(file_field)
            if uploaded and uploaded.filename:
                filename = secure_filename(uploaded.filename)
                if not allowed_file(filename):
                    return render_template('index.html', shown_indicator=indicator_key, error=f'File not allowed: {filename}')
                
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                uploaded.save(save_path)

                # basic validation
                try:
                    validate_csv_columns(save_path, required_cols=['Date', 'Close'])
                except Exception as e:
                    return render_template('index.html', shown_indicator=indicator_key, error=str(e))

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
                    return render_template('index.html', shown_indicator=indicator_key, error=f'Error fetching {ticker}: {e}')
                # ensure Date parsed and sorted
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce', utc=True)
                df = df.sort_values('Date').reset_index(drop=True)
                # apply filtering for ticker (latest N months)
                df_filtered = filter_dataframe(df, source='ticker', option=time_range)
                dfs.append(df_filtered)
                labels.append(label)

        if not dfs:
            return render_template('index.html', shown_indicator=indicator_key, error='No data provided. Provide a ticker or upload a CSV.')
        
        # Update parameters with user's inputs
        for key in request.form.keys():
            # all parameters in request.form start with indicator_
            if key.startswith(indicator_key):
                # extract only the parameter name (some parameters have _ in their name)
                param = key.split('_', 1)[1]
                # all parameters have to be integer
                indicator_params[indicator_key][param] = int(request.form.get(key))

        print('zkdebug3', indicator_params, indicator_key)

        applied = []
        for df in dfs:
            if indicator_key:
                try:
                    df_with_ind = apply_indicator(df, indicator_key, params=indicator_params[indicator_key])
                except Exception as e:
                    return render_template('index.html', shown_indicator=indicator_key, error=f'Indicator error: {e}')
            else:
                df_with_ind = df.copy()
            applied.append(df_with_ind)

        # Build plot
        try:
            plot_div = plot_close_prices(applied, labels, indicator_key=indicator_key, indicator_params=indicator_params[indicator_key])
        except Exception as e:
            return render_template('index.html', shown_indicator=indicator_key, error=f'Plotting error: {e}')

        # Render the SAME index.html but include the plot fragment and labels.
        return render_template('index.html',
                               shown_indicator=indicator_key,
                               params=indicator_params[indicator_key],
                               plot_div=plot_div,
                               labels=labels,
                               time_range=time_range
        )

    # GET
    return render_template('index.html', shown_indicator=get_indicator_keys())

@app.route('/clear_cache')
def clear_cache():
    uploaded_cache["file1"] = None
    uploaded_cache["file2"] = None
    uploaded_cache["labels"] = {"file1": None, "file2": None}
    return "Cache cleared."

if __name__ == '__main__':
    app.run(debug=True)
