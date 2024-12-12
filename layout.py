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
                dcc.Graph(
                    id='price-chart',
                    config={
                        'modeBarButtonsToAdd': ['drawrect'],
                        'displayModeBar': True,
                        'editable': True,
                        'edits': {'shapePosition': True}
                    },
                    style={'height': '80vh'}
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
