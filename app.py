from flask import Flask, render_template, request, redirect, url_for
from data.fetch import get_stock_data
from indicators import calculate_sma, calculate_ema, calculate_rsi, calculate_macd
from plotting.plot_prices import plot_close_prices
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ticker = request.form.get("ticker")
        indicator = request.form.getlist("indicator")
        file = request.files.get("file")

        if file:
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)
            df = get_stock_data(filepath=filepath)
        elif ticker:
            df = get_stock_data(ticker=ticker)
        else:
            return render_template("index.html", error="Provide ticker or CSV.")

        # Apply indicators
        if "sma" in indicator:
            df = calculate_sma(df, window=20)
        if "ema" in indicator:
            df = calculate_ema(df, window=20)
        if "rsi" in indicator:
            df = calculate_rsi(df, period=14)
        if "macd" in indicator:
            df = calculate_macd(df)

        # Save or return plot
        plot_path = os.path.join("static", "images", "plot.png")
        plot_close_prices([df], [ticker or "CSV Upload"], indicators=df.columns, save_path=plot_path)

        return render_template("results.html", plot_url=plot_path)

    return render_template("index.html")
