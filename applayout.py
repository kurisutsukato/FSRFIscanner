
from dash import dcc, html
import dash_bootstrap_components as dbc

def gen(plot={}, options={}):
    layout = html.Div([
            #dcc.Interval(id="interval", interval=1000 * 30, n_intervals=0),
            dcc.Location(id="url", refresh=False),
            dcc.Store(id='experiment', data={}),

            #dcc.Store(id='last_range'),
            dcc.Store(id="files"),

            dcc.Store(id="freq-selection"),
            dcc.Store(id="azel-selection"),

            dcc.Loading(
                id="folder-loading",
                type="circle",
                target_components={"info-folder": "children"},
                children=[
                    html.Span([
                        html.Label('Data folder', style={"flex": "0 1 auto"}),
                        dcc.Dropdown(
                            id="folder-dropdown",
                            options=options,
                            value=None,  # next(iter(initial_stored_sessions), None),
                            clearable=False,
                            style={"flex": "0 1 auto", "width": "300px"}
                        ),
                        html.Div(id="info-folder"),
                        html.Div(style={"marginLeft": "auto"}),
                        html.Label('base frequency (Hz)'),
                        dcc.Input(id='base-freq', value=0, type='number', style={"flex": "0 1 auto", "width": "300px"})
                    ], style={"display": "flex", "gap": "10px", "padding": "10px"}),



                ], style={"flex": 1}
            ),

            html.Div(
                [
                    dcc.Graph(id="total", style={"flex": 1, "height": "100%", "minHeight": 0},),
                    dcc.Graph(id="crop", style={"flex": 1, "height": "100%", "minHeight": 0},),
                ],
                style={
                    "display": "flex",
                    "gap": "10px",
                    "flex": "0 1 auto",  # don't force equal share
                    "minHeight": 0,
                },
            ),
            dcc.Loading(id='map-loading', children=[dcc.Graph(id="map", figure=plot)],
                        type="circle",
                        target_components={'map': 'figure'},
                        overlay_style={"visibility": "visible", "backgroundColor": "transparent"},
                        style={"flex": 1}
                        ),

        ],
        style={"height": "100vh",
               "display": "flex",
               "flexDirection": "column",
               }
    )


    return layout