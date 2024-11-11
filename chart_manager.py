import pandas as pd
from chart_utils import process_relayout_data

class ChartManager:
    def __init__(self):
        self.state_colors = {}

    def update_chart(self, relayoutData, clear_clicks, coin_data, state_1_color, state_2_color, state_3_color, state_4_color, existing_figure, selected_file):
        data = pd.DataFrame(coin_data)
        data['time'] = pd.to_datetime(data['time'])

        self.state_colors = {
            1: state_1_color,
            2: state_2_color,
            3: state_3_color,
            4: state_4_color
        }

        fig, percent_change_text = process_relayout_data(
            relayoutData, clear_clicks, data, existing_figure, selected_file, self.state_colors
        )

        return fig, percent_change_text