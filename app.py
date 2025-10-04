from flask import Flask, render_template, request
import os

from data.fetch import get_stock_data
from indicators import calculate_sma, calculate_ema, calculate_rsi, calculate_macd
from plotting.plot_prices import plot_close_prices
from utils.validation import allowed_file, validate_csv_columns

app = Flask(__name__)

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
IMG_FOLDER = os.path.join(BASE_DIR, 'static', 'images')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMG_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker1 = (request.form.get('ticker1') or '').strip() or None
        ticker2 = (request.form.get('ticker2') or '').strip() or None
        file1 = request.files.get('file1')
        file2 = request.files.get('file2')
        selected_indicators = request.form.getlist('indicator') # list like ['sma','rsi']

        dfs = []
        labels = []


        def add_stock(ticker, file_obj, hint_label):
            # Returns (df, label) or (None, error_message)
            if file_obj and file_obj.filename != '':
                if not allowed_file(file_obj.filename):
                    return None, f"File {file_obj.filename} is not allowed. Only CSV accepted."
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file_obj.filename)
                file_obj.save(filepath)
                ok = validate_csv_columns(filepath)
                if not ok:
                    print('Data Columns did not pass validation checks')
                    return None
                df = get_stock_data(filepath=filepath)
                label = file_obj.filename
                return df, label
            elif ticker:
                try:
                    df = get_stock_data(ticker=ticker)
                    return df, ticker.upper()
                except Exception as e:
                    return None, f"Error fetching {ticker}: {e}"
            else:
                return None, None


        for (t, f, hint) in [(ticker1, file1, 'Ticker1'), (ticker2, file2, 'Ticker2')]:
            df_label = add_stock(t, f, hint)
            if df_label is None:
                continue
            df, label_or_msg = df_label
            if df is None and label_or_msg:
                return render_template('index.html', error=label_or_msg)
            if df is not None:
                dfs.append(df)
                labels.append(label_or_msg)


        if not dfs:
            return render_template('index.html', error='Provide at least one ticker or CSV file.')


        # Apply selected indicators to each data frame
        indicator_map = {
            'sma': lambda df: calculate_sma(df, window=20),
            'ema': lambda df: calculate_ema(df, window=20),
            'rsi': lambda df: calculate_rsi(df, period=14),
            'macd': lambda df: calculate_macd(df)
        }


        for i, df in enumerate(dfs):
            for ind_key in selected_indicators:
                fn = indicator_map.get(ind_key)
                if fn:
                    dfs[i] = fn(dfs[i])


        # Gather indicator columns present (to pass to plotter)
        indicator_columns = []
        for df in dfs:
            for col in df.columns:
                if col.startswith(('SMA_', 'EMA_', 'RSI_', 'MACD')) and col not in indicator_columns:
                    indicator_columns.append(col)


        plot_path = os.path.join(IMG_FOLDER, 'plot.png')
        saved = plot_close_prices(dfs, labels, indicators=indicator_columns, save_path=plot_path)
        return render_template('results.html', plot_url=os.path.join('images', os.path.basename(saved)))


    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)