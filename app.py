from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import plotly.graph_objs as go

app = Flask(__name__)

# Predefined list of popular stocks for autocomplete
POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "JNJ", "V",
    "WMT", "PG", "UNH", "HD", "DIS", "BAC", "MA", "PYPL", "CMCSA", "XOM",
    "NFLX", "ADBE", "CSCO", "PFE", "VZ", "INTC", "ABT", "T", "CRM", "NKE"
]

@app.route('/')
def index():
    # optional query params to pre-load (kept compatible with your logs)
    symbol = request.args.get('symbol', 'AAPL').upper()
    period = request.args.get('period', '6mo')
    return render_template('index.html', popular_stocks=POPULAR_STOCKS, initial_symbol=symbol, initial_period=period)


@app.route('/search_stocks')
def search_stocks():
    query = request.args.get('q', '').upper()
    if not query:
        return jsonify([])
    # Filter from predefined first
    results = [s for s in POPULAR_STOCKS if query in s]
    # naive yfinance attempt if few results
    if len(results) < 5:
        try:
            info = yf.Ticker(query).info
            if info.get('shortName'):
                if query not in results:
                    results.append(query)
        except Exception:
            pass
    return jsonify(results[:10])


def _history_df(symbol: str, period: str) -> pd.DataFrame:
    """Fetch history, ensure we have Close column and clean index."""
    df = yf.Ticker(symbol).history(period=period)
    if df is None or df.empty:
        return pd.DataFrame()
    # Ensure index is timezone naive & convert to python datetime for Plotly
    if hasattr(df.index, "tz_localize"):
        try:
            df.index = df.index.tz_localize(None)
        except Exception:
            pass
    return df


def _line_with_sma_figure(df: pd.DataFrame, symbol: str) -> go.Figure:
    """Line chart with Close + SMA20 + SMA50."""
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines", name=f"{symbol} Close"
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df["SMA20"], mode="lines", name="SMA 20"
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df["SMA50"], mode="lines", name="SMA 50"
    ))

    fig.update_layout(
        margin=dict(l=30, r=10, t=40, b=40),
        title=f"{symbol} Stock Price with Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


@app.route('/get_stock_data')
def get_stock_data():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '6mo')
    if not symbol:
        return jsonify({'error': 'No symbol provided'})

    try:
        hist = _history_df(symbol, period)
        if hist.empty:
            return jsonify({'error': f'No data found for {symbol}'})

        # Moving averages (for small sparkline consumption by client; main chart uses /get_stock_chart)
        sma20 = hist["Close"].rolling(20).mean().fillna(0).tolist()
        sma50 = hist["Close"].rolling(50).mean().fillna(0).tolist()

        dates = [d.strftime('%Y-%m-%d') for d in hist.index]
        closes = hist["Close"].fillna(0).tolist()

        current_price = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100 if prev_close != 0 else 0.0

        info = {}
        try:
            info = yf.Ticker(symbol).info
        except Exception:
            pass
        company_name = info.get('longName', symbol)

        return jsonify({
            'symbol': symbol,
            'companyName': company_name,
            'dates': dates,
            'prices': closes,
            'sma20': sma20,
            'sma50': sma50,
            'currentPrice': round(current_price, 2),
            'change': round(change, 2),
            'changePercent': round(change_percent, 2),
            'error': None
        })
    except Exception as e:
        return jsonify({'error': f'Error fetching data: {str(e)}'})


@app.route('/get_stock_chart')
def get_stock_chart():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '6mo')
    if not symbol:
        return jsonify({'error': 'No symbol provided'})

    try:
        df = _history_df(symbol, period)
        if df.empty:
            return jsonify({'error': f'No data found for {symbol}'})
        fig = _line_with_sma_figure(df, symbol)
        return jsonify({'fig': json.loads(fig.to_json()), 'error': None})
    except Exception as e:
        return jsonify({'error': f'Error generating chart: {str(e)}'})


@app.route('/compare_stocks')
def compare_stocks():
    symbol1 = request.args.get('symbol1', '').upper()
    symbol2 = request.args.get('symbol2', '').upper()
    period = request.args.get('period', '6mo')
    if not symbol1 or not symbol2:
        return jsonify({'error': 'Both symbols are required for comparison'})

    try:
        df1 = _history_df(symbol1, period)
        df2 = _history_df(symbol2, period)
        if df1.empty or df2.empty:
            return jsonify({'error': 'No data found for one or both symbols'})

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df1.index, y=df1["Close"], mode="lines", name=f"{symbol1} Close"))
        fig.add_trace(go.Scatter(x=df2.index, y=df2["Close"], mode="lines", name=f"{symbol2} Close"))

        fig.update_layout(
            margin=dict(l=30, r=10, t=40, b=40),
            title=f"{symbol1} vs {symbol2} — Close Price",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        # Company names + mini stats
        info1, info2 = {}, {}
        try:
            info1 = yf.Ticker(symbol1).info
            info2 = yf.Ticker(symbol2).info
        except Exception:
            pass

        current_price1 = float(df1["Close"].iloc[-1])
        prev_close1 = float(df1["Close"].iloc[-2]) if len(df1) > 1 else current_price1
        change1 = current_price1 - prev_close1
        change_percent1 = (change1 / prev_close1 * 100) if prev_close1 != 0 else 0.0

        current_price2 = float(df2["Close"].iloc[-1])
        prev_close2 = float(df2["Close"].iloc[-2]) if len(df2) > 1 else current_price2
        change2 = current_price2 - prev_close2
        change_percent2 = (change2 / prev_close2 * 100) if prev_close2 != 0 else 0.0

        return jsonify({
            'fig': json.loads(fig.to_json()),
            'symbol1': symbol1,
            'symbol2': symbol2,
            'companyName1': info1.get('longName', symbol1),
            'companyName2': info2.get('longName', symbol2),
            'currentPrice1': round(current_price1, 2),
            'currentPrice2': round(current_price2, 2),
            'change1': round(change1, 2),
            'change2': round(change2, 2),
            'changePercent1': round(change_percent1, 2),
            'changePercent2': round(change_percent2, 2),
            'error': None
        })
    except Exception as e:
        return jsonify({'error': f'Error comparing stocks: {str(e)}'})


@app.route('/daily_returns')
def daily_returns():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '6mo')
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400

    try:
        df = _history_df(symbol, period)
        if df.empty:
            return jsonify({"error": f"No data for {symbol}"}), 400

        if "Adj Close" not in df.columns:
            df["Adj Close"] = df["Close"]

        df["Daily Return"] = df["Adj Close"].pct_change()
        df = df.dropna()

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["Daily Return"], mode="lines", name="Daily Return"))
        fig.update_layout(
            margin=dict(l=30, r=10, t=40, b=40),
            title=f"Daily Returns for {symbol}",
            xaxis_title="Date",
            yaxis_title="Return",
            hovermode="x unified"
        )

        rows = [
            {
                "Date": idx.strftime("%Y-%m-%d"),
                "Adj Close": round(float(row["Adj Close"]), 2),
                "Daily Return": round(float(row["Daily Return"]) * 100, 2)
            }
            for idx, row in df.iterrows()
        ]

        return jsonify({"fig": json.loads(fig.to_json()), "table": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/max_profit')
def max_profit():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '6mo')
    if not symbol:
        return jsonify({"error": "No symbol provided"}), 400

    try:
        df = _history_df(symbol, period)
        if df.empty:
            return jsonify({"error": f"No data for {symbol}"}), 400

        prices = df["Close"].values
        dates = df.index.tolist()

        min_price = float('inf')
        min_idx = 0
        max_profit = 0.0
        buy_idx = sell_idx = 0

        for i, p in enumerate(prices):
            if p < min_price:
                min_price = p
                min_idx = i
            profit = p - min_price
            if profit > max_profit:
                max_profit = profit
                buy_idx = min_idx
                sell_idx = i

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines", name=f"{symbol} Close"))
        if max_profit > 0 and buy_idx < sell_idx:
            fig.add_trace(go.Scatter(
                x=[dates[buy_idx]], y=[prices[buy_idx]],
                mode="markers+text",
                name="Buy",
                text=["Buy"],
                textposition="top center",
                marker=dict(size=12, symbol="triangle-up")
            ))
            fig.add_trace(go.Scatter(
                x=[dates[sell_idx]], y=[prices[sell_idx]],
                mode="markers+text",
                name="Sell",
                text=["Sell"],
                textposition="bottom center",
                marker=dict(size=12, symbol="triangle-down")
            ))

        fig.update_layout(
            margin=dict(l=30, r=10, t=40, b=40),
            title=f"Max Profit Window — {symbol}",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            hovermode="x unified"
        )

        payload = {
            "fig": json.loads(fig.to_json()),
            "buyDate": dates[buy_idx].strftime("%Y-%m-%d"),
            "sellDate": dates[sell_idx].strftime("%Y-%m-%d"),
            "buyPrice": round(float(prices[buy_idx]), 2),
            "sellPrice": round(float(prices[sell_idx]), 2),
            "profit": round(float(max_profit), 2)
        }
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
