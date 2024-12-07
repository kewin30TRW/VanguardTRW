# callback_handler.py

import dash
from dash import Input, Output, State
import pandas as pd
from datetime import datetime
from chart_utils import process_relayout_data
import dash

class CallbackHandler:
    def __init__(self, app, data_manager):
        """
        Inicjalizuje handler callbacków dla aplikacji Dash.

        :param app: Instancja aplikacji Dash.
        :param data_manager: Instancja DataManager.
        """
        self.app = app
        self.data_manager = data_manager
        self._register_callbacks()

    def _register_callbacks(self):
        self._register_update_leverage_options()
        self._register_update_file_path()
        self._register_sync_data()
        self._register_update_coin_data()
        self._register_update_chart()

    def _register_update_leverage_options(self):
        @self.app.callback(
            Output('leverage-selector', 'options'),
            Input('crypto-selector', 'value')
        )
        def update_leverage_options(crypto):
            """
            Aktualizuje dostępne opcje dźwigni w zależności od wybranej kryptowaluty.
            """
            options = [{'label': '2X', 'value': '2X'}, {'label': '3X', 'value': '3X'}]
            if crypto.lower() == 'btc':
                options.append({'label': '4X', 'value': '4X'})
            return options

    def _register_update_file_path(self):
        @self.app.callback(
            [Output('selected-file', 'data'), Output('leverage-selector', 'value')],
            [Input('crypto-selector', 'value'), Input('leverage-selector', 'value')]
        )
        def update_file_path(crypto, leverage):
            """
            Aktualizuje ścieżkę pliku i wybraną dźwignię na podstawie wybranego kryptowaluty i dźwigni.
            """
            key = f"{crypto}{leverage}PriceData.csv"
            if key in self.data_manager.addresses:
                file_path = key
                return file_path, leverage
            else:
                default_leverage = '2X'
                default_key = f"{crypto}{default_leverage}PriceData.csv"
                return default_key, default_leverage

    def _register_sync_data(self):
        @self.app.callback(
            Output('data-sync-trigger', 'data'),
            Input('sync-data-button', 'n_clicks'),
            prevent_initial_call=True
        )
        def sync_data(n_clicks):
            """
            Synchronizuje dane po kliknięciu przycisku synchronizacji.
            """
            if n_clicks:
                self.data_manager.update_all_data()
                sync_time = datetime.now().isoformat()
                return {'sync_time': sync_time}
            else:
                return dash.no_update

    def _register_update_coin_data(self):
        @self.app.callback(
            Output('coin-data', 'data'),
            [Input('selected-file', 'data'),
             Input('data-sync-trigger', 'data')]
        )
        def update_coin_data(file_path, sync_trigger):
            """
            Aktualizuje dane monety na podstawie wybranego pliku i synchronizacji danych.
            """
            smoothing_on = True
            if file_path:
                data = self.data_manager.process_data(file_path, smoothing_on)
                return data.to_dict('records')
            else:
                return dash.no_update

    def _register_update_chart(self):
        @self.app.callback(
            [Output('price-chart', 'figure'), Output('output-percent-change', 'children')],
            [Input('price-chart', 'relayoutData'),
             Input('clear-shapes-button', 'n_clicks'),
             Input('coin-data', 'data')],
            [State('price-chart', 'figure'), State('selected-file', 'data')],
            prevent_initial_call=True
        )
        def update_chart(relayoutData, clear_clicks, coin_data, existing_figure, selected_file):
            """
            Aktualizuje wykres cenowy na podstawie zmian w układzie wykresu, kliknięcia przycisku czyszczenia kształtów lub aktualizacji danych monety.
            """
            ctx = dash.callback_context
            triggered_input = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

            if not coin_data:
                return dash.no_update, dash.no_update

            data = pd.DataFrame(coin_data)
            data['time'] = pd.to_datetime(data['time'])

            default_state_colors = {
                1: '#009664',
                2: '#ADFF2F',
                3: '#FF8C00',
                4: '#B22222'
            }

            fig, percent_change_text = process_relayout_data(
                relayoutData, clear_clicks, data, existing_figure, selected_file, triggered_input, default_state_colors
            )
            return fig, percent_change_text
