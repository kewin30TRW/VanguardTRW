import plotly.graph_objs as go
import pandas as pd
from datetime import datetime

def generate_chart(data, coin_name):
    legend_colors = {
        'Strong Bullish': '#009664', 
        'Bullish': '#ADFF2F',         
        'Bearish': '#FF8C00',    
        'Strong Bearish': '#B22222' 
    }

    if "btc3X" in coin_name:
        candlestick_colors = {
            'Strong Bullish': '#009664', 
            'Bullish': '#ADFF2F',       
            'Bearish': '#FF8C00',    
            'Strong Bearish': '#B22222' 
        }
    elif "btc4X" in coin_name:
        candlestick_colors = {
            'Strong Bullish': '#009664', 
            'Bullish': '#ADFF2F',  
            'Bearish': '#B22222',        
            'Strong Bearish': '#FF8C00'
        }
    elif "sol3X" in coin_name:
        candlestick_colors = {
            'Strong Bullish': '#009664',  
            'Bullish': '#ADFF2F',        
            'Bearish': '#B22222',      
            'Strong Bearish': '#FF8C00' 
        }
    elif "sol2X" in coin_name:
        candlestick_colors = {
            'Strong Bullish': '#ADFF2F',  
            'Bullish': '#009664',        
            'Bearish': '#FF8C00',      
            'Strong Bearish': '#B22222' 
        }
    else:
        candlestick_colors = {
            'Strong Bullish': '#009664',  
            'Bullish': '#ADFF2F',        
            'Bearish': '#FF8C00',         
            'Strong Bearish': '#B22222'   
        }

    fig = go.Figure()

    for i, (condition, color) in enumerate(candlestick_colors.items(), start=1):
        condition_data = data[data['MarketCondition'] == condition]
        if not condition_data.empty:
            fig.add_trace(go.Candlestick(
                x=condition_data['time'],
                open=condition_data['open'],
                high=condition_data['high'],
                low=condition_data['low'],
                close=condition_data['close'],
                name=f"State{i}",
                increasing_line_color=color,
                decreasing_line_color=color,
                showlegend=True
            ))

    for condition, color in legend_colors.items():
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode='markers',
            marker=dict(size=10, color=color),
            legendgroup=condition,
            showlegend=True,
            name=condition
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

def process_relayout_data(relayoutData, clear_clicks, data, existing_figure, selected_file, triggered_input):
    coin_name = selected_file.split('PriceData')[0]
    percent_change_text = ""

    if existing_figure is None or triggered_input == 'coin-data' or triggered_input == 'clear-shapes-button':
        fig = generate_chart(data, coin_name)
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
