import plotly.graph_objs as go
import pandas as pd
from datetime import datetime

def generate_chart(data, coin_name, state_colors):
    state_mapping = {
        1: {'condition': 'Strong Bullish', 'color': state_colors[1]},
        2: {'condition': 'Bullish', 'color': state_colors[2]},
        3: {'condition': 'Bearish', 'color': state_colors[3]},
        4: {'condition': 'Strong Bearish', 'color': state_colors[4]}
    }

    fig = go.Figure()

    for state_index in range(1, 5):
        condition_info = state_mapping[state_index]
        condition = condition_info['condition']
        color = condition_info['color']
        condition_data = data[data['StateIndex'] == state_index]

        if not condition_data.empty:
            fig.add_trace(go.Candlestick(
                x=condition_data['time'],
                open=condition_data['open'],
                high=condition_data['high'],
                low=condition_data['low'],
                close=condition_data['close'],
                name=f"State{state_index}: {condition}",
                increasing_line_color=color,
                decreasing_line_color=color,
                showlegend=True
            ))
        else:
            fig.add_trace(go.Candlestick(
                x=[],
                open=[],
                high=[],
                low=[],
                close=[],
                name=f"State{state_index}: {condition}",
                increasing_line_color=color,
                decreasing_line_color=color,
                showlegend=True,
                visible=False 
            ))

    fig.update_layout(
        title=f"{coin_name}",
        xaxis_title="Date",
        yaxis_title="Price (Log Scale)",
        yaxis_type="log",
        xaxis_rangeslider_visible=False,
        plot_bgcolor='black',
        paper_bgcolor='black',
        font=dict(color='white'),
        uirevision='constant'
    )

    return fig

def process_relayout_data(relayoutData, clear_clicks, data, existing_figure, selected_file, triggered_input, state_colors):
    coin_name = selected_file.split('PriceData')[0]
    percent_change_text = ""

    # Lista inputów dla wyborów kolorów
    color_inputs = ['state-1-color', 'state-2-color', 'state-3-color', 'state-4-color']

    if existing_figure is None or triggered_input in ['coin-data', 'clear-shapes-button'] + color_inputs:
        fig = generate_chart(data, coin_name, state_colors)
        percent_change_text = ""
    else:
        fig = go.Figure(existing_figure)
        if triggered_input == 'price-chart':
            if relayoutData and 'shapes' in relayoutData:
                shapes = relayoutData['shapes']
                if isinstance(shapes, list) and len(shapes) > 0:
                    fig.update_layout(shapes=shapes)
                    new_shape = shapes[-1]
                    x0 = new_shape.get('x0')
                    x1 = new_shape.get('x1')
                    if x0 is not None and x1 is not None:
                        start_time = min(pd.to_datetime(x0), pd.to_datetime(x1))
                        end_time = max(pd.to_datetime(x0), pd.to_datetime(x1))
                        filtered_data = data[(data['time'] >= start_time) & (data['time'] <= end_time)]
                        if not filtered_data.empty:
                            start_price = filtered_data['close'].iloc[0]
                            end_price = filtered_data['close'].iloc[-1]
                            percent_change = ((end_price - start_price) / start_price) * 100
                            percent_change_text = f"Percent change from {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}: **{percent_change:.2f}%**"
                        else:
                            percent_change_text = "No data in the selected time range."
    return fig, percent_change_text