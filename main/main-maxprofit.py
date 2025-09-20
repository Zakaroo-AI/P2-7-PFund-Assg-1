from flask import Flask, request, jsonify
import yfinance as yf

app = Flask(__name__)

# --- Max profit function (single buy/sell) ---
def max_profit(prices):
    min_price = float('inf')
    max_profit = 0
    for price in prices:
        min_price = min(min_price, price)
        max_profit = max(max_profit, price - min_price)
    return max_profit

# --- Max Profit Endpoint ---
@app.route('/maxprofit', methods=['GET'])
def calculate_profit():
    """
    Example: /maxprofit?ticker=AAPL&period=30d
    """
    ticker_symbol = request.args.get("ticker", "AAPL")
    period = request.args.get("period", "30d")

    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period=period)

        if data.empty:
            return jsonify({"error": f"No data found for {ticker_symbol}"}), 404

        prices = data['Close'].tolist()
        profit = max_profit(prices)

        return jsonify({
            "ticker": ticker_symbol,
            "period": period,
            "max_profit": profit,
            "prices_used": len(prices)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Daily Returns Endpoint ---
@app.route('/dailyreturns', methods=['GET'])
def daily_returns():
    """
    Example: /dailyreturns?ticker=AAPL&period=30d
    """
    ticker_symbol = request.args.get("ticker", "AAPL")
    period = request.args.get("period", "30d")

    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period=period)

        if data.empty:
            return jsonify({"error": f"No data found for {ticker_symbol}"}), 404

        # Calculate daily returns
        data["Daily Return"] = data["Close"].pct_change()

        # Convert to JSON-friendly format
        results = []
        for date, row in data.iterrows():
            results.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(row["Close"], 2),
                "daily_return": None if pd.isna(row["Daily Return"]) else round(row["Daily Return"], 6)
            })

        return jsonify({
            "ticker": ticker_symbol,
            "period": period,
            "data": results
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    import pandas as pd  # needed for NaN check
    app.run(debug=True)