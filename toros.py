import os
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State
import pandas as pd
from chart_utils import process_relayout_data
from hmm_processor import process_data
from fetchData import update_all_data
from datetime import datetime
from flask import Flask, request, Response
from werkzeug.security import check_password_hash, generate_password_hash
from google.cloud import secretmanager

DATA_DIR = os.getenv('DATA_DIR', os.path.dirname(os.path.abspath(__file__)))

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

update_all_data()

addresses = {
    "sol2X": os.path.join(DATA_DIR, "sol2XPriceData.csv"),
    "sol3X": os.path.join(DATA_DIR, "sol3XPriceData.csv"),
    "btc2X": os.path.join(DATA_DIR, "btc2XPriceData.csv"),
    "btc3X": os.path.join(DATA_DIR, "btc3XPriceData.csv"),
    "btc4X": os.path.join(DATA_DIR, "btc4XPriceData.csv"),
    "eth2X": os.path.join(DATA_DIR, "eth2XPriceData.csv"),
    "eth3X": os.path.join(DATA_DIR, "eth3XPriceData.csv")
}

server = Flask(__name__)

app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.DARKLY])

ENV = os.getenv('ENV', 'development')

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        raise EnvironmentError("Missing GOOGLE_CLOUD_PROJECT environment variable.")
    
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

if ENV == 'production':
    VALID_USERNAME = get_secret("USERNAME")
    VALID_PASSWORD = get_secret("PASSWORD")

    VALID_PASSWORD_HASH = generate_password_hash(VALID_PASSWORD)

    def check_auth(username, password):
        """Check if the provided username and password are valid."""
        return username == VALID_USERNAME and check_password_hash(VALID_PASSWORD_HASH, password)

    def authenticate():
        """Send a 401 response that enables basic auth."""
        return Response(
            'Authentication required', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'}
        )

    def requires_auth():
        """Authenticate every request."""
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()

    @server.before_request
    def before_request():
        """Apply authentication to all routes."""
        return requires_auth()
else:
    def requires_auth():
        pass

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Vanguard Leverage Tool", className='text-center text-primary mb-4'),
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Label("Choose crypto"),
            dbc.Select(
                id='crypto-selector',
                options=[
                    {'label': 'BTC', 'value': 'btc'},
                    {'label': 'ETH', 'value': 'eth'},
                    {'label': 'SOL', 'value': 'sol'}
                ],
                value='btc'
            )
        ], xs=12, sm=6, md=4),
        dbc.Col([
            dbc.Label("Choose leverage"),
            dbc.RadioItems(
                id='leverage-selector',
                options=[],
                value='2X',
                inline=True
            )
        ], xs=12, sm=6, md=4)
    ], className='mb-4'),

    dbc.Row([
        dbc.Col([
            dbc.Label("RSI Length"),
            dbc.Input(id='rsi-length-input', type='number', min=1, value=14)
        ], xs=12, sm=4, md=3),
        dbc.Col([
            dbc.Label("EMA Length"),
            dbc.Input(id='ema-length-input', type='number', min=1, value=20)
        ], xs=12, sm=4, md=3),
        dbc.Col([
            dbc.Label("Smoothing"),
            dbc.Checklist(
                options=[{"label": "Smoothing", "value": "ON"}],
                value=["ON"],
                id="smoothing-switch",
                switch=True,
            )
        ], xs=12, sm=4, md=3)
    ], className='mb-4'),
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id='price-chart',
                config={
                    'modeBarButtonsToAdd': ['drawrect'],
                    'displayModeBar': True,
                    'editable': True,
                    'edits': {'shapePosition': True}
                },
                style={'height': '70vh'}
            )
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Button('Synchronize data', id='sync-data-button', n_clicks=0, color='secondary', className='mr-2'),
            dbc.Button('Clear layouts', id='clear-shapes-button', n_clicks=0, color='primary', className='mr-2'),
            html.Div(id='output-percent-change', className='mt-3')
        ], width=12)
    ]),
    dcc.Store(id='coin-data'),
    dcc.Store(id='selected-file'),
    dcc.Store(id='data-sync-trigger')
], fluid=True)

@app.callback(
    [Output('selected-file', 'data'), Output('leverage-selector', 'value')],
    [Input('crypto-selector', 'value'), Input('leverage-selector', 'value')]
)
def update_file_path(crypto, leverage):
    key = f"{crypto}{leverage}"
    if key in addresses:
        file_path = addresses[key]
        return file_path, leverage
    else:
        default_key = f"{crypto}2X"
        file_path = addresses.get(default_key, '')
        return file_path, '2X'

@app.callback(
    Output('leverage-selector', 'options'),
    Input('crypto-selector', 'value')
)
def update_leverage_options(crypto):
    options = [{'label': '2X', 'value': '2X'}, {'label': '3X', 'value': '3X'}]
    if crypto == 'btc':
        options.append({'label': '4X', 'value': '4X'})
    return options

@app.callback(
    Output('data-sync-trigger', 'data'),
    Input('sync-data-button', 'n_clicks'),
    prevent_initial_call=True
)
def sync_data(n_clicks):
    if n_clicks:
        update_all_data()
        return {'sync_time': datetime.now().isoformat()}
    else:
        return dash.no_update

@app.callback(
    Output('coin-data', 'data'),
    [Input('selected-file', 'data'),
     Input('data-sync-trigger', 'data'),
     Input('rsi-length-input', 'value'),
     Input('ema-length-input', 'value'),
     Input('smoothing-switch', 'value')]
)
def update_coin_data(file_path, sync_trigger, rsi_length, ema_length, smoothing_value):
    smoothing_on = 'ON' in smoothing_value
    if file_path and os.path.exists(file_path):
        data = process_data(file_path, rsi_length, ema_length, smoothing_on)
        return data.to_dict('records')
    else:
        print(f"File not found: {file_path}")
        return []

@app.callback(
    [Output('price-chart', 'figure'), Output('output-percent-change', 'children')],
    [Input('price-chart', 'relayoutData'),
     Input('clear-shapes-button', 'n_clicks'),
     Input('coin-data', 'data')],
    [State('price-chart', 'figure'), State('selected-file', 'data')],
    prevent_initial_call=True
)
def update_chart(relayoutData, clear_clicks, coin_data, existing_figure, selected_file):
    ctx = dash.callback_context
    triggered_input = ctx.triggered[0]['prop_id'].split('.')[0]

    data = pd.DataFrame(coin_data)
    data['time'] = pd.to_datetime(data['time'])

    fig, percent_change_text = process_relayout_data(
        relayoutData, clear_clicks, data, existing_figure, selected_file, triggered_input
    )

    return fig, percent_change_text

if __name__ == '__main__':
    app.run_server(debug=False)

server = app.server
