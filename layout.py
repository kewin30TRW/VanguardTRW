import dash_bootstrap_components as dbc
from dash import html, dcc

def create_layout():
    return dbc.Container([
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
                dbc.Label("State 1 Color (def. Green)"),
                dbc.Select(
                    id='state-1-color',
                    options=[
                        {'label': 'Green', 'value': '#009664'},
                        {'label': 'Yellow Green', 'value': '#ADFF2F'},
                        {'label': 'Orange', 'value': '#FF8C00'},
                        {'label': 'Red', 'value': '#B22222'}
                    ],
                    value='#009664'
                )
            ], xs=12, sm=6, md=3),
            dbc.Col([
                dbc.Label("State 2 Color (def. Yellow green)"),
                dbc.Select(
                    id='state-2-color',
                    options=[
                        {'label': 'Green', 'value': '#009664'},
                        {'label': 'Yellow Green', 'value': '#ADFF2F'},
                        {'label': 'Orange', 'value': '#FF8C00'},
                        {'label': 'Red', 'value': '#B22222'}
                    ],
                    value='#ADFF2F'
                )
            ], xs=12, sm=6, md=3),
            dbc.Col([
                dbc.Label("State 3 Color (def. Orange)"),
                dbc.Select(
                    id='state-3-color',
                    options=[
                        {'label': 'Green', 'value': '#009664'},
                        {'label': 'Yellow Green', 'value': '#ADFF2F'},
                        {'label': 'Orange', 'value': '#FF8C00'},
                        {'label': 'Red', 'value': '#B22222'}
                    ],
                    value='#FF8C00'
                )
            ], xs=12, sm=6, md=3),
            dbc.Col([
                dbc.Label("State 4 Color (def. Red)"),
                dbc.Select(
                    id='state-4-color',
                    options=[
                        {'label': 'Green', 'value': '#009664'},
                        {'label': 'Yellow Green', 'value': '#ADFF2F'},
                        {'label': 'Orange', 'value': '#FF8C00'},
                        {'label': 'Red', 'value': '#B22222'}
                    ],
                    value='#B22222'
                )
            ], xs=12, sm=6, md=3)
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