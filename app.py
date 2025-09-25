from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
from modules.analysis import StockAnalysis

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        period = request.form.get("period", "6mo")

        # CASE 1: CSV upload
        if "csvFile" in request.files and request.files["csvFile"].filename != "":
            file = request.files["csvFile"]
            df = pd.read_csv(file)

            if df.empty:
                return jsonify({"error": "Uploaded CSV is empty"}), 400

            df.columns = [c.lower() for c in df.columns]
            required_cols = {"date", "open", "high", "low", "close", "volume"}
            if not required_cols.issubset(df.columns):
                return jsonify({"error": f"CSV must include columns: {required_cols}"}), 400

            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)

        # CASE 2: Yahoo Finance fetch
        else:
            symbol = request.form.get("symbol", "").upper().strip()
            if not symbol:
                return jsonify({"error": "Please provide a stock symbol or upload a CSV"}), 400

            print(f"📊 Analyzing {symbol} for period {period}")
            df = yf.download(symbol, period=period, progress=False)
            if df.empty:
                return jsonify({"error": f"No data found for {symbol}"}), 400

            df = df.reset_index()

            # 🔹 Flatten MultiIndex into single-level lowercase names
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ["_".join([str(c) for c in col if c]).lower() for col in df.columns.values]
            else:
                df.columns = [str(c).lower() for c in df.columns]

            # Normalize date column
            if "date" not in df.columns:
                df.rename(columns={df.columns[0]: "date"}, inplace=True)

            # Ensure datetime type
            df["date"] = pd.to_datetime(df["date"])

        # 🔹 Debug: print cleaned columns
        print(f"✅ Final normalized columns: {df.columns.tolist()}")

        # Run analysis
        sa = StockAnalysis(df)
        results = {
            "sma": sa.get_sma(window=5),
            "runs": sa.get_runs(),
            "returns": sa.get_returns(),
            "profit": sa.get_max_profit(),
            "rsi": sa.get_rsi(),
            "ema": sa.get_ema(),
            "macd": sa.get_macd()
        }
        return jsonify(results)

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
