import dash
from dash import Input, Output, State
import pandas as pd
from datetime import datetime
from chart_utils import process_relayout_data
from hmm_processor import process_data
from fetchData import update_all_data

class CallbackHandler:
    def __init__(self, app, addresses):
        self.app = app
        self.addresses = addresses
        self._register_callbacks()

    def _register_callbacks(self):
        self._register_update_file_path()
        self._register_update_leverage_options()
        self._register_sync_data()
        self._register_update_coin_data()
        self._register_update_chart()

    def _register_update_file_path(self):
        self.app.callback(
            [Output('selected-file', 'data'), Output('leverage-selector', 'value')],
            [Input('crypto-selector', 'value'), Input('leverage-selector', 'value')]
        )(self.update_file_path)

    def update_file_path(self, crypto, leverage):
        key = f"{crypto}{leverage}"
        if key in self.addresses:
            file_path = self.addresses[key]
            return file_path, leverage
        else:
            default_key = f"{crypto}2X"
            file_path = self.addresses.get(default_key, '')
            return file_path, '2X'

    def _register_update_leverage_options(self):
        self.app.callback(
            Output('leverage-selector', 'options'),
            Input('crypto-selector', 'value')
        )(self.update_leverage_options)

    def update_leverage_options(self, crypto):
        options = [{'label': '2X', 'value': '2X'}, {'label': '3X', 'value': '3X'}]
        if crypto == 'btc':
            options.append({'label': '4X', 'value': '4X'})
        return options

    def _register_sync_data(self):
        self.app.callback(
            Output('data-sync-trigger', 'data'),
            Input('sync-data-button', 'n_clicks'),
            prevent_initial_call=True
        )(self.sync_data)

    def sync_data(self, n_clicks):
        if n_clicks:
            update_all_data()
            return {'sync_time': datetime.now().isoformat()}
        else:
            return dash.no_update

    def _register_update_coin_data(self):
        self.app.callback(
            Output('coin-data', 'data'),
            [Input('selected-file', 'data'),
             Input('data-sync-trigger', 'data'),
             Input('rsi-length-input', 'value'),
             Input('ema-length-input', 'value'),
             Input('smoothing-switch', 'value')]
        )(self.update_coin_data)

    def update_coin_data(self, file_path, sync_trigger, rsi_length, ema_length, smoothing_value):
        smoothing_on = 'ON' in smoothing_value
        data = process_data(file_path, rsi_length, ema_length, smoothing_on)
        return data.to_dict('records')

    def _register_update_chart(self):
        self.app.callback(
            [Output('price-chart', 'figure'), Output('output-percent-change', 'children')],
            [Input('price-chart', 'relayoutData'),
             Input('clear-shapes-button', 'n_clicks'),
             Input('coin-data', 'data'),
             Input('state-1-color', 'value'),
             Input('state-2-color', 'value'),
             Input('state-3-color', 'value'),
             Input('state-4-color', 'value')],
            [State('price-chart', 'figure'), State('selected-file', 'data')],
            prevent_initial_call=True
        )(self.update_chart)

    def update_chart(self, relayoutData, clear_clicks, coin_data, state_1_color, state_2_color, state_3_color, state_4_color, existing_figure, selected_file):
        ctx = dash.callback_context
        triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]

        data = pd.DataFrame(coin_data)
        data['time'] = pd.to_datetime(data['time'])

        state_colors = {
            1: state_1_color,
            2: state_2_color,
            3: state_3_color,
            4: state_4_color
        }

        fig, percent_change_text = process_relayout_data(
            relayoutData, clear_clicks, data, existing_figure, selected_file, triggered_input, state_colors
        )

        return fig, percent_change_text
