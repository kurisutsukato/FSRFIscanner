
from dash import dcc, html
import dash_bootstrap_components as dbc

layout = html.Div([
    dcc.Interval(id="interval", interval=1000*30, n_intervals=0),
    dcc.Store(id='last_range'),
    #html.Div([
    #    html.Label('Choose a file:'),
    #    dcc.Dropdown(id='filename', options=get_file_options(), style={'width': '400px'}),
    #], style={'display': 'flex', 'gap': '10px', 'padding': '10px'}),

    html.Label("Stored files"),

    dcc.Location(
        id="url",
        refresh=False
    ),

    dcc.Store(
        id="stored-files",
        data={}
    ),

    dcc.Graph(id="total"),
    dcc.Graph(id="map"),
    dcc.Graph(id="crop"),
])