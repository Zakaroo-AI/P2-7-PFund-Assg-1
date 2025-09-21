from flask import Flask, render_template, request, jsonify
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import io
import base64
import json
from datetime import datetime, timedelta
from io import BytesIO

app = Flask(__name__)

# Predefined list of popular stocks for autocomplete
POPULAR_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "JNJ", "V",
    "WMT", "PG", "UNH", "HD", "DIS", "BAC", "MA", "PYPL", "CMCSA", "XOM",
    "NFLX", "ADBE", "CSCO", "PFE", "VZ", "INTC", "ABT", "T", "CRM", "NKE"
]

@app.route('/')
def index():
    return render_template('index.html', popular_stocks=POPULAR_STOCKS)

@app.route('/search_stocks')
def search_stocks():
    query = request.args.get('q', '').upper()
    
    if not query:
        return jsonify([])
    
    # Filter popular stocks based on query
    results = [stock for stock in POPULAR_STOCKS if query in stock]
    
    # If we have less than 5 results, try to find more from yfinance
    if len(results) < 5:
        try:
            # This is a simple approach - in a real app you'd want a proper stock search API
            search_results = yf.Ticker(query)
            info = search_results.info
            if info.get('shortName'):
                results.append(query)
        except:
            pass
    
    return jsonify(results[:10])  # Return max 10 results

@app.route('/get_stock_data')
def get_stock_data():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '6mo')
    
    if not symbol:
        return jsonify({'error': 'No symbol provided'})
    
    try:
        # Get stock data
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        
        if hist.empty:
            return jsonify({'error': f'No data found for {symbol}'})
        
        # Calculate moving averages
        hist['SMA20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        
        # Prepare data for JSON response
        dates = hist.index.strftime('%Y-%m-%d').tolist()
        closes = hist['Close'].fillna(0).tolist()
        sma20 = hist['SMA20'].fillna(0).tolist()
        sma50 = hist['SMA50'].fillna(0).tolist()
        
        # Get current price and daily change
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
        change = current_price - prev_close
        change_percent = (change / prev_close) * 100
        
        # Get company info
        info = stock.info
        company_name = info.get('longName', symbol)
        
        response_data = {
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
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': f'Error fetching data: {str(e)}'})

@app.route('/get_stock_chart')
def get_stock_chart():
    symbol = request.args.get('symbol', '').upper()
    period = request.args.get('period', '6mo')
    
    if not symbol:
        return jsonify({'error': 'No symbol provided'})
    
    try:
        # Get stock data
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)
        
        if hist.empty:
            return jsonify({'error': f'No data found for {symbol}'})
        
        # Calculate moving averages
        hist['SMA20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        
        # Create plot
        plt.figure(figsize=(10, 6))
        plt.plot(hist.index, hist['Close'], label='Close Price', linewidth=2)
        plt.plot(hist.index, hist['SMA20'], label='20-Day SMA', linewidth=1.5)
        plt.plot(hist.index, hist['SMA50'], label='50-Day SMA', linewidth=1.5)
        
        plt.title(f'{symbol} Stock Price with Moving Averages')
        plt.xlabel('Date')
        plt.ylabel('Price ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Encode the image to base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        plt.close()
        
        return jsonify({'image': image_base64, 'error': None})
    
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
        # Get data for both stocks
        stock1 = yf.Ticker(symbol1)
        stock2 = yf.Ticker(symbol2)
        
        hist1 = stock1.history(period=period)
        hist2 = stock2.history(period=period)
        
        if hist1.empty or hist2.empty:
            return jsonify({'error': f'No data found for one or both symbols'})
        
        # Calculate moving averages for both stocks
        hist1['SMA20'] = hist1['Close'].rolling(window=20).mean()
        hist1['SMA50'] = hist1['Close'].rolling(window=50).mean()
        
        hist2['SMA20'] = hist2['Close'].rolling(window=20).mean()
        hist2['SMA50'] = hist2['Close'].rolling(window=50).mean()
        
        # Create comparison plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Plot first stock
        ax1.plot(hist1.index, hist1['Close'], label='Close Price', linewidth=2)
        ax1.plot(hist1.index, hist1['SMA20'], label='20-Day SMA', linewidth=1.5)
        ax1.plot(hist1.index, hist1['SMA50'], label='50-Day SMA', linewidth=1.5)
        ax1.set_title(f'{symbol1} Stock Price with Moving Averages')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Price ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot second stock
        ax2.plot(hist2.index, hist2['Close'], label='Close Price', linewidth=2)
        ax2.plot(hist2.index, hist2['SMA20'], label='20-Day SMA', linewidth=1.5)
        ax2.plot(hist2.index, hist2['SMA50'], label='50-Day SMA', linewidth=1.5)
        ax2.set_title(f'{symbol2} Stock Price with Moving Averages')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Price ($)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        
        # Encode the image to base64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        plt.close()
        
        # Get company info for both stocks
        info1 = stock1.info
        info2 = stock2.info
        
        company_name1 = info1.get('longName', symbol1)
        company_name2 = info2.get('longName', symbol2)
        
        # Get current prices and changes
        current_price1 = hist1['Close'].iloc[-1]
        prev_close1 = hist1['Close'].iloc[-2] if len(hist1) > 1 else current_price1
        change1 = current_price1 - prev_close1
        change_percent1 = (change1 / prev_close1) * 100
        
        current_price2 = hist2['Close'].iloc[-1]
        prev_close2 = hist2['Close'].iloc[-2] if len(hist2) > 1 else current_price2
        change2 = current_price2 - prev_close2
        change_percent2 = (change2 / prev_close2) * 100
        
        response_data = {
            'symbol1': symbol1,
            'symbol2': symbol2,
            'companyName1': company_name1,
            'companyName2': company_name2,
            'currentPrice1': round(current_price1, 2),
            'currentPrice2': round(current_price2, 2),
            'change1': round(change1, 2),
            'change2': round(change2, 2),
            'changePercent1': round(change_percent1, 2),
            'changePercent2': round(change_percent2, 2),
            'image': image_base64,
            'error': None
        }
        
        return jsonify(response_data)
    
    except Exception as e:
        return jsonify({'error': f'Error comparing stocks: {str(e)}'})
    
@app.route('/daily_returns', methods=['GET'])
def daily_returns():
    symbol = request.args.get('symbol')
    period = request.args.get('period', '6mo')

    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)

        if hist.empty:
            return jsonify({"error": f"No data for {symbol}"}), 400

        # Use 'Close' if 'Adj Close' is missing
        if 'Adj Close' not in hist.columns:
            hist['Adj Close'] = hist['Close']

        hist['Daily Return'] = hist['Adj Close'].pct_change()
        hist = hist.dropna()

        # Convert index to naive datetime (drop timezone)
        hist.index = hist.index.tz_localize(None)

        # Chart
        plt.switch_backend('Agg')  # Prevent GUI warnings
        plt.figure(figsize=(10, 5))
        plt.plot(hist.index, hist['Daily Return'], label="Daily Return")
        plt.title(f"Daily Returns for {symbol}")
        plt.xlabel("Date")
        plt.ylabel("Return")
        plt.legend()

        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        chart_data = base64.b64encode(buf.getvalue()).decode()
        plt.close()

        # Table data
        rows = [
            {
                "Date": idx.strftime("%Y-%m-%d"),
                "Adj Close": round(row["Adj Close"], 2),
                "Daily Return": round(row["Daily Return"] * 100, 2)
            }
            for idx, row in hist.iterrows()
        ]

        return jsonify({"chart": chart_data, "table": rows})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)