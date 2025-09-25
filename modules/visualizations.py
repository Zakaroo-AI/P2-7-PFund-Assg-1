import plotly.graph_objs as go

class StockVisualizer:
    def plot_price_and_sma(self, df, sma_values, symbol, window):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["close"], name="Close Price"))
        fig.add_trace(go.Scatter(x=df.index, y=sma_values, name=f"SMA {window}"))
        return fig

    def plot_runs_highlighted(self, df, runs_data, symbol):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["close"], name="Close Price"))
        return fig

    def plot_daily_returns(self, returns, symbol):
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=returns, nbinsx=50))
        return fig

    def plot_profit_analysis(self, df, profit_data, symbol):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["close"], name="Close Price"))
        return fig
