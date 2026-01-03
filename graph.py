from plotly import graph_objects as go
from helper import fix_name, REVERSE_METRICS


def get_hover_format(metric):
    metric = metric.lower()

    if any([
        metric.endswith('revenue'),
        metric.endswith('aov'),
        metric.endswith('cpc'),
        metric.endswith('cac'),
        metric.endswith('spend')]):
        return '$.2s'
    elif any([
        metric.endswith('rate'),
        metric.endswith('cvr'),
        metric.endswith('ctr'),
        metric.lower == 'acos',
        '__to__' in metric]):
        return '0.2s%'
    else:
        return '.2s'


def get_color(anomaly_type, metric):
    if metric.lower() in REVERSE_METRICS:
        anomaly_type *= -1

    if anomaly_type == 1:
        return 'green'
    elif anomaly_type == -1:
        return 'red'
    else:
        return '#46B1FF'


def get_graph(metric, xaxis_data, yaxis_data, trend_data, yhat_upper_data, yhat_lower_data, anomaly_type_data):
    fact = go.Scatter(
        x=xaxis_data,
        y=yaxis_data,
        mode='lines+markers',
        showlegend=False,
        line=dict(color="#46B1FF"),
        marker=dict(color=list(anomaly_type_data.apply(lambda x: get_color(x, metric)))),
        hoverinfo='skip'
    )

    trend = go.Scatter(
        x=xaxis_data,
        y=trend_data,
        mode='lines',
        showlegend=False,
        line=dict(color="#768591", dash='dash'),
        hoverinfo='skip'
    )

    upper_bound = go.Scatter(
        x=xaxis_data,
        y=yhat_upper_data,
        mode='lines',
        showlegend=False,
        fill='tonexty',
        line=dict(color="#ADD8E6"),
        hoverinfo='skip'
    )

    lower_bound = go.Scatter(
        x=xaxis_data,
        y=yhat_lower_data,
        mode='lines',
        showlegend=False,
        line=dict(color="#ADD8E6"),
        hoverinfo='skip'
    )

    data = [lower_bound, upper_bound, trend, fact]

    tickformat = get_hover_format(metric)

    layout = go.Layout(
        yaxis_tickformat=tickformat,
        yaxis=dict(rangemode='tozero'),
        autosize=False,
        width=536,
        height=362,
        margin=go.layout.Margin(
            l=0,
            r=0,
            b=0,
            t=0,
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )

    fig = go.Figure(data, layout)

    return fig
