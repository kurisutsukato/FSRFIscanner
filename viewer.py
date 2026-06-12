import numpy as np
from dash import Dash, Input, Output, State, no_update, callback_context, Patch
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime

from plotly import graph_objs as go
import h5py
from json import dumps, loads
from glob import glob

from applayout import gen



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

azbin = 6
elbin = 2
binned = merged.copy()
binned['el'] = (binned['el'] / elbin + 0.5).astype(int)
binned['az'] = (binned['az'] / azbin + .5).astype(int)
binned = binned.loc[binned.az < 60]
elaxis = np.arange(binned.el.min(), binned.el.max()+1)*elbin
azaxis = np.arange(binned.az.min(), binned.az.max()+1)*azbin

def plot(xrng=None):
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
    arr[arr==0] = np.nan

    fig = go.Figure(data=go.Heatmap(z=arr.T,
                                    x=azaxis,
                                    y=elaxis))

    fig.update_layout(dragmode="select",
                      clickmode='event+select',
                      margin=dict(l=5, r=5, t=20, b=5),
                      xaxis=dict(title_text='Azimuth', fixedrange=True),
                      yaxis=dict(title_text='Elevation', fixedrange=True))
    return fig

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP,
                                      "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
                                      ])
files = glob('*.h5')
options = [{"label": item, "value": item} for item in files]

app.layout = gen(plot(), options)
app.title = 'spec viewer'


@app.callback(
    Output("acufile-dropdown", "options", allow_duplicate=True),
    Output("acufile-dropdown", "value", allow_duplicate=True),

    Input("url", "pathname"),
    prevent_initial_call=True
)
def reload_sessions(_):
    print('reload')

    acufiles = glob('*.h5')
    options = [{"label": item, "value": item } for item in acufiles]

    return options, None

@app.callback(
    Output("info-acufile", "children"),
    Output("experiment", "data"),
    Input("acufile-dropdown", "value"),
    State("experiment", "data"),
)
def select_acufile(filename, experiment):
    if filename is None:
        return no_update, no_update

    with h5py.File(filename, 'r') as f:
        try:
            dfpos = pd.DataFrame({'ts': f['timestamp'][:], 'az': f['az'][:], 'el': f['el'][:]}).astype({'ts': np.int64})
        except KeyError:
            msg = 'not a acu file'
        else:
            experiment.update({'acufile': filename})
            dtstart = datetime.fromtimestamp(dfpos.iloc[0]['ts']/1000)
            dtstop = datetime.fromtimestamp(dfpos.iloc[-1]['ts']/1000)
            msg = f'{dtstart} to {dtstop}'
    return msg, experiment

#@app.callback(
#    Output("last_range", "data"),
#    Output("map", "figure"),
#    Input("total", "relayoutData"),
#    State("last_range", "data"),
#    allow_duplicate=True
#)
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


@app.callback(
    Output("crop", "figure"),
    Input('azel-selection', 'data'),
    prevent_initial_call=True
)
def update_crop(azel_selection):
    xr, yr = azel_selection
    xr = np.asarray(xr).astype(int)
    yr = np.asarray(yr).astype(int)

    data = []
    nspec = 0
    with h5py.File('20260603-180131_sband.h5', 'r') as f:
        spectra = f['spectra']['spectrum']
        crop = binned.loc[binned.az.between(*xr/azbin) & binned.el.between(*yr/elbin)]
        for (az, el), df in crop.groupby(['el', 'az']):
            val = np.asarray(spectra[df['spec_idx'].values])
            nspec += val.shape[0]
            data.append(val.max(axis=0))
    y = np.asarray(data).max(axis=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=freq, y=y))
    fig.update_layout(margin=dict(l=5, r=5, t=20, b=5),
                      xaxis=dict(title_text='Frequency (Hz)'))

    fig.add_annotation(
        x=0.02,
        y=0.98,
        xref="paper",
        yref="paper",
        text=f"{xr[0]:d}-{xr[1]:d}º azimuth<br>{yr[0]}-{yr[1]}º elevation<br>max of {nspec} spectra",
        showarrow=False,
        bgcolor="rgba(255,255,255,0.8)"
    )
    return fig

@app.callback(
    Output("total", "figure", allow_duplicate=True),
    Output("freq-selection", "data"),
    Input('total', 'selectedData'),
    prevent_initial_call=True
)
def update_total_selection(selected):
    if not selected or "range" not in selected:
        return no_update, no_update
    patch = Patch()

    x0, x1 = selected["range"]["x"]

    patch["layout"]["shapes"] = [{
        "type": "rect",
        "xref": "x",
        "yref": "paper",
        "x0": x0,
        "x1": x1,
        "y0": 0,
        "y1": 1,
        "fillcolor": "rgba(255,0,0,0.2)",
        "line": {"width": 0},
    }]
    return patch, (x0,x1)


@app.callback(
    Output("total", "figure"),
    #Output("last_range", "data"),
    State("last_range", "data"),
)
def update_total(last_range):
    #xrng, yrng = loads(last_range) if last_range else (None, None)

    with h5py.File('20260603-180131_sband.h5', 'r') as f:
        spec = np.asarray(f['spectra']['spectrum'][:]).max(axis=0)
        p90 = np.percentile(f['spectra']['spectrum'][:], 99.9, axis=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=freq, y=spec, name='max'))
    fig.add_trace(go.Scatter(x=freq, y=p90, name='99%'))

    fig.update_layout(dragmode="select",
                      clickmode='event+select',
                      legend=dict(
                          yanchor="top",
                          y=.95,
                          xanchor="left",
                          x=.05,
                          itemsizing='constant'
                         ),
                      margin=dict(l=5, r=5, t=20, b=5),
                      yaxis=dict(fixedrange=True),
                      xaxis=dict(title_text='Frequency (Hz)', fixedrange=True)
                      )
    return fig

@app.callback(
    Output("map", "figure"),
    Output("azel-selection", "data"),
    Input('map', 'selectedData'),
    Input("freq-selection", "data"),
    prevent_initial_call=True
)
def update_map_selection(selected, freq):
    patch = Patch()

    # remove previous selection
    patch["layout"]["shapes"] = []

    if selected and "range" in selected:
        xr = selected["range"]["x"]
        yr = selected["range"]["y"]

        patch["layout"]["shapes"].append({
            "type": "rect",
            "x0": xr[0],
            "x1": xr[1],
            "y0": yr[0],
            "y1": yr[1],
            "line": {"width": 2},
            "fillcolor": "rgba(255,255,255,0.2)",
        })

        return patch, (xr, yr)
    return no_update, no_update

# ---- Main figure update ----
@app.callback(
    Output("map", "figure"),
    Input("freq-selection", "data"),
    State("azel-selection", "data"),
)
def update_map(xrng, azel_selection):

    fig = plot(xrng)

    if azel_selection:
        xr, yr = azel_selection
        fig.add_shape({
            "type": "rect",
            "x0": xr[0],
            "x1": xr[1],
            "y0": yr[0],
            "y1": yr[1],
            "line": {"width": 2},
            "fillcolor": "rgba(255,255,255,0.2)",
        })
    return fig

if __name__ == "__main__":
    app.run()

