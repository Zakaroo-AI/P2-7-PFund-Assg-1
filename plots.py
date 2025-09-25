import plotly.graph_objs as go

def plot_sma(data, sma):
    """Plot stock closing prices with SMA overlay."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data['Close'],
                             mode='lines', name='Close Price'))
    fig.add_trace(go.Scatter(x=sma.index, y=sma,
                             mode='lines', name='SMA'))
    fig.update_layout(title='Stock Prices with SMA',
                      xaxis_title='Date',
                      yaxis_title='Price')
    return fig
