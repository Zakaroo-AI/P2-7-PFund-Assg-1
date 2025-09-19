import yfinance as yf

class StockDataFetcher:
    def get_data(self, symbol: str, period: str = "6mo"):
        try:
            df = yf.download(symbol, period=period)
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
