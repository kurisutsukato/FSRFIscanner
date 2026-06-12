
from dash import dcc, html
import dash_bootstrap_components as dbc

def gen(plot={}, options={}):

    layout = dbc.Tabs([
        dbc.Tab(label='Data', children=[
            dcc.Interval(id="interval", interval=1000*30, n_intervals=0),
            dcc.Location(id="url", refresh=False),
            dcc.Store(id='experiment', data={}),

            dcc.Loading(
                id="acufile-loading",
                type="circle",
                target_components={"info-acufile": "children"},
                children=[
                    html.Span([
                        html.Label('ACU file',  style={"flex": "0 1 auto"}),
                        dcc.Dropdown(
                            id="acufile-dropdown",
                            options=options,
                            value=None,  # next(iter(initial_stored_sessions), None),
                            clearable=False,
                            style={"flex": "0 1 auto", "width": "300px"}
                        ),
                        html.Div(id="info-acufile")
                    ], style={"display": "flex","gap": "10px", "padding": "10px"} ),

                ]
            ),
            html.Span([
                html.Label('Spec file', style={"flex": "0 1 auto"}),
                dcc.Dropdown(
                    id="specfile-dropdown",
                    value=None,  # next(iter(initial_stored_sessions), None),
                    options=options,
                    clearable=False,
                    style = {"flex": "0 1 auto", "width": "300px"}
                ),
                dcc.Loading(html.Div(id="info-specfile")),
            ], style={"display": "flex","gap": "10px", "padding": "10px"} ),
        ]),
        dbc.Tab(label='Vis', children=[
            dcc.Store(id='last_range'),
            dcc.Store(id="files"),

            dcc.Store(id="freq-selection"),
            dcc.Store(id="azel-selection"),

            html.Div(
                [
                    dcc.Graph(id="total", style={"flex": 1}),
                    dcc.Graph(id="crop", style={"flex": 1}),
                ],
                style={
                    "display": "flex",
                    "gap": "10px",
                },
            ),
            dcc.Loading(dcc.Graph(id="map", figure=plot),
                        type="circle",
                        overlay_style={"visibility": "visible", "backgroundColor": "transparent"},
                        ),

            ])
        ])


    return layout