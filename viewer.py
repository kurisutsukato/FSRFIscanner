import numpy as np
from dash import Dash, dcc, html, Input, Output, State, no_update, callback_context, set_props
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from pathlib import Path
import pandas as pd

from plotly import graph_objs as go

from datetime import datetime

import h5py
from json import dumps, loads
from glob import glob
import base64, uuid


from applayout import layout

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP,
                                 "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
                                 ])
app.layout = layout
app.title = 'spec viewer'

btns = [
               {
                   'label': 'Autoscale Y',
                   'method': 'relayout',
                   'args': [{'yaxis.autorange': True, 'yaxis2.autorange': True}]
               }]

with h5py.File('20260603-181042_fullsky.h5', 'r') as f:
    dfpos = pd.DataFrame({'ts': f['timestamp'][:], 'az': f['az'][:], 'el': f['el'][:]}).astype({'ts': np.int64})

with h5py.File('20260603-180131_sband.h5', 'r') as f:
    # spectra = f["spectra"]["spectrum"]          # shape (N, channels)
    # ts_spec = pd.to_datetime(f["spectra"]["timestamp"][:], unit="ms")
    ts = f["spectra"]["timestamp"][:]
    freq = np.asarray(f.attrs['frequencies'][:])
    dfspec = pd.DataFrame({"ts": ts, "spec_idx": range(len(ts))}).astype({'ts': np.int64})

merged = pd.merge_asof(
    dfspec,
    dfpos,
    on="ts",
    direction="nearest",
    tolerance=100  # adjust
)

merged.ts = merged.ts // 1000
merged = merged.loc[merged.az.notna()]

binned = merged.copy()
binned['el'] = (binned['el'] / 2 + 0.5).astype(int)
binned['az'] = (binned['az'] / 6 + .5).astype(int)
print(binned.az.min(), binned.az.max())
print(binned.el.min(), binned.el.max())

# ---- Handle zoom + file change (state only) ----
@app.callback(
    Output("last_range", "data"),
    Output("map", "figure"),
    Input("total", "relayoutData"),
    State("last_range", "data"),
    allow_duplicate=True
)
def handle_zoom_and_file(relayoutData, last_range):

    ctx = callback_context
    trigger = ctx.triggered_id

    xrng = yrng = None

    # ---- New file → reset everything ----
    if trigger == "filename":
        return dumps((None, None)), no_update

    # ---- Restore previous range ----
    if last_range:
        xrng, yrng = loads(last_range)

    # ---- Handle zoom ----
    if relayoutData:
        if "xaxis.autorange" in relayoutData:
            xrng = None
        if "yaxis.autorange" in relayoutData:
            yrng = None

        if "xaxis.range[0]" in relayoutData:
            xrng = [
                relayoutData["xaxis.range[0]"],
                relayoutData["xaxis.range[1]"]
            ]

        if "yaxis.range[0]" in relayoutData:
            yrng = [
                relayoutData["yaxis.range[0]"].split('.')[0],
                relayoutData["yaxis.range[1]"].split('.')[0],
            ]

    return dumps([xrng, yrng]), no_update


# ---- Main figure update ----
@app.callback(
    Output("total", "figure"),
    #Output("last_range", "data"),
    State("last_range", "data"),
)
def update_total(last_range):
    #xrng, yrng = loads(last_range) if last_range else (None, None)

    with h5py.File('20260603-180131_sband.h5', 'r') as f:
        spectra = np.asarray(f['spectra']['spectrum'][:]).max(axis=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=freq, y=spectra))
    return fig

# ---- Main figure update ----
@app.callback(
    Output("map", "figure"),
    Input("last_range", "data"),
)
def update_map(last_range):
    xrng, yrng = loads(last_range) if last_range else (None, None)

    data = []
    with h5py.File('20260603-180131_sband.h5', 'r') as f:
        spectra = f['spectra']['spectrum']
        for (az, el), df in binned.groupby(['el', 'az']):
            val = np.asarray(spectra[df['spec_idx'].values])
            if xrng is not None:
                a,b = np.searchsorted(freq, xrng)
                val = val[:,a:b]
            data.append((az, el, val.max()))

    tmp = np.array(data[:-1])

    x = tmp[:, 0].astype(int)
    y = tmp[:, 1].astype(int)
    v = tmp[:, 2]

    arr = np.zeros((y.max() + 1, x.max() + 1))
    arr[y, x] = v
    arr = arr[:,1:]

    fig = go.Figure(data=go.Heatmap(z=arr.T))
    print(arr.shape)
    return fig

if __name__ == "__main__":
    app.run()

