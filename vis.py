import numpy as np
from dash import Dash, Input, Output, State, no_update, callback_context, Patch, html
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

from plotly import graph_objs as go
import h5py
from glob import glob

from applayout import gen

experiment_cache = {}

def plot(exp, frng=None, base_freq=0, fill_gaps=True):
    binned = experiment_cache[exp['foldername']]

    azaxis = exp['azaxis']
    elaxis = exp['elaxis']

    data = []
    with h5py.File(exp['specfile'], 'r') as f:
        spectra = f['spectra']['spectrum']
        timestamp = f['spectra']['timestamp']
        freq = f.attrs['frequencies']
        for (az, el), df in binned.groupby(['el', 'az']):
            val = np.asarray(spectra[df['spec_idx'].values])
            tsval = np.asarray(timestamp[df['spec_idx'].values]).min()
            if frng is not None:
                a,b = np.searchsorted(freq, np.asarray(frng)-base_freq)
                val = val[:,a:b]
            data.append((tsval, az, el, val.max()))

    tmp = np.array(data)

    dtstr = np.array([
        datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
        for ts in tmp[:, 0]/1000
    ])

    x = tmp[:, 1].astype(int)
    y = tmp[:, 2].astype(int)
    v = tmp[:, 3]

    arr = np.zeros((y.max()-y.min() + 1, x.max()-x.min() + 1))
    tarr = np.empty(arr.shape, dtype='<U16')
    arr[y-y.min(), x-x.max()] = v
    arr[arr==0] = np.nan
    arr = arr.T

    tarr[y-y.min(), x-x.max()] = dtstr
    tarr = tarr.T

    if fill_gaps:
        mask = np.isnan(arr)

        # For each row, build indices of last non-NaN value seen
        idx = np.where(~mask, np.arange(arr.shape[1]), 0)
        idx = np.maximum.accumulate(idx, axis=1)

        # Fill NaNs from the left
        arr = arr[np.arange(arr.shape[0])[:, None], idx]
        tarr = tarr[np.arange(tarr.shape[0])[:, None], idx]

    fig = go.Figure(data=go.Heatmap(z=arr,
                                    x=azaxis,
                                    y=elaxis,
                                    customdata=tarr,
                                    hovertemplate=
                                    "azimuth: %{x}º<br>" +
                                    "elevation: %{y}º<br>" +
                                    "max. power: %{z}<br>" +
                                    "time: %{customdata}<extra></extra>"
                                    ))

    fig.update_layout(dragmode="select",
                      clickmode='event+select',
                      margin=dict(l=5, r=5, t=20, b=5),
                      xaxis=dict(title_text='Azimuth', fixedrange=True),
                      yaxis=dict(title_text='Elevation', fixedrange=True))
    return fig

def fmt_dt(dt):
    if not isinstance(dt, datetime):
        dt = datetime.fromtimestamp(dt, tz=timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP,
                                 "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"])

folders = [p for p in Path("data").iterdir() if p.is_dir()]
options = [{"label": item.stem, "value": str(item)} for item in folders]

app.layout = gen({}, options)
app.title = 'spec viewer'

@app.callback(
    Output("folder-dropdown", "options", allow_duplicate=True),
    Input("url", "pathname"),
    prevent_initial_call=True
)
def reload_sessions(_):
    folders = [p for p in Path("data").iterdir() if p.is_dir()]
    options = [{"label": item.stem, "value": str(item)} for item in folders]

    return options

@app.callback(
    Output("info-folder", "children"),
    Output("experiment", "data"),
    Input("folder-dropdown", "value"),
    Input('max-rate', 'value'),
    State("experiment", "data"),
)
def select_folder(foldername, max_rate, experiment):
    if foldername is None:
        return no_update, no_update

    max_rate = float(max_rate) or 0

    if not foldername in experiment:
        files = glob(foldername+'/*.h5')
        if len(files) != 2:
            msg = 'there must be exactly two .h5 files in the folder'
            return msg, experiment

        first, second = [Path(f).stat().st_size for f in files]
        acufile = files[0] if first < second else files[1]
        specfile = files[1] if first < second else files[0]

        with (h5py.File(acufile, 'r') as f):
            try:
                if 'azrate' in f and 'elrate' in f:
                    dfpos = pd.DataFrame({'ts': f['timestamp'][:],
                                          'az': f['az'][:],
                                          'el': f['el'][:],
                                          'azrate': f['azrate'][:],
                                          'elrate': f['elrate'][:],
                                          }
                                         ).astype({'ts': np.int64})
                    if max_rate > 0:
                        dfpos = dfpos[dfpos.azrate.abs()<max_rate]
                        dfpos = dfpos[dfpos.elrate.abs()<max_rate]
                else:
                    dfpos = pd.DataFrame({'ts': f['timestamp'][:],
                                          'az': f['az'][:],
                                          'el': f['el'][:],
                                          }
                                         ).astype({'ts': np.int64})

            except KeyError:
                msg = 'not a acu file'
            else:
                dtstart = datetime.fromtimestamp(dfpos.iloc[0]['ts'] / 1000, tz=timezone.utc)
                dtstop = datetime.fromtimestamp(dfpos.iloc[-1]['ts'] / 1000, tz=timezone.utc)
                #experiment.update({'acufile': {'filename': acufile}})
                msg = f'{fmt_dt(dtstart)} to {fmt_dt(dtstop)}'

        if callback_context.triggered_id == 'max-rate' and not 'azrate' in dfpos.columns:
            print('no rate information available')

        with h5py.File(specfile, 'r') as f:
            try:
                ts = f["spectra"]["timestamp"][:]
                freq = np.asarray(f.attrs['frequencies'][:])
            except KeyError:
                msg = 'not a spec file'
            else:
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
        if len(merged) == 0:
            return 'no overlap', experiment

        dtstart = datetime.fromtimestamp(merged.iloc[0]['ts'], tz=timezone.utc)
        dtstop = datetime.fromtimestamp(merged.iloc[-1]['ts'], tz=timezone.utc)

        azbin = 4
        elbin = 1
        binned = merged.copy()
        binned['el'] = (binned['el'] / elbin + 0.5).astype(int)
        binned['az'] = (binned['az'] / azbin + .5).astype(int)

        elaxis = np.arange(binned.el.min(), binned.el.max() + 1) * elbin
        azaxis = np.arange(binned.az.min(), binned.az.max() + 1) * azbin

        experiment_cache[foldername] = binned
        experiment.update({'foldername': foldername,
                           'specfile': specfile,
                           'elaxis': elaxis.tolist(),
                           'azaxis': azaxis.tolist(),
                           'elbin': elbin,
                           'azbin': azbin})

    msg = f'{fmt_dt(dtstart)} to {fmt_dt(dtstop)}'
    return msg, experiment

@app.callback(
    Output("crop", "figure"),
    Input('azel-selection', 'data'),
    Input('experiment', 'data'),
    Input('base-freq', 'value'),
    prevent_initial_call=True
)
def update_crop(azel_selection, experiment, base_freq):
    try:
        xr, yr = azel_selection
    except TypeError:
        return no_update
    xr = np.asarray(xr).astype(int)
    yr = np.asarray(yr).astype(int)

    base_freq = float(base_freq) or 0

    binned = experiment_cache[experiment['foldername']]

    data = []
    nspec = 0
    with h5py.File(experiment['specfile'], 'r') as f:
        freq = f.attrs['frequencies']+base_freq
        spectra = f['spectra']['spectrum']
        crop = binned.loc[binned.az.between(*xr/experiment['azbin']) & binned.el.between(*yr/experiment['elbin'])]
        for (az, el), df in crop.groupby(['el', 'az']):
            val = np.asarray(spectra[df['spec_idx'].values])
            nspec += val.shape[0]
            data.append(val.max(axis=0))
    try:
        ymax = np.asarray(data).max(axis=0)
    except ValueError:
        return no_update

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=freq, y=ymax, name='max'))
    fig.update_layout(margin=dict(l=5, r=5, t=20, b=5),
                      xaxis=dict(title_text='Frequency (Hz)'))
    fig.update_xaxes(
        tickformat="~s",
        exponentformat="SI"
    )
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
    Input('experiment', 'data'),

    prevent_initial_call=True
)
def update_total_selection(selected, experiment):
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
    Input("experiment", "data"),
    Input("base-freq", "value"),
    State("freq-selection", "data"),
)
def update_total(experiment, base_freq, last_range):
    #xrng, yrng = loads(last_range) if last_range else (None, None)
    if 'specfile' not in experiment or experiment['specfile'] is None:
        return no_update

    binned = experiment_cache[experiment['foldername']]

    base_freq = float(base_freq) or 0

    data = []
    with h5py.File(experiment['specfile'], 'r') as f:
        spectra = f['spectra']['spectrum']
        freq = f.attrs['frequencies']+base_freq
        for (az, el), df in binned.groupby(['el', 'az']):
            data.append(spectra[df['spec_idx'].values])
        data = np.vstack(data)
        p90 = np.percentile(data, 99.9, axis=0)
        spec = data.max(axis=0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=freq, y=spec, name='max'))
    fig.add_trace(go.Scatter(x=freq, y=p90, name='99%'))

    if False or last_range:
        x0, x1 = last_range
        fig.add_shape(
            type="rect",
            xref="x",
            yref="paper",
            x0=x0,
            x1=x1,
            y0=0,
            y1=1,
            fillcolor="rgba(255,0,0,0.2)",
            line_width=0,
        )

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
                      xaxis=dict(title_text='Frequency (Hz)', fixedrange=True, tickformat="~s", exponentformat="SI")
                      )

    if last_range:
        x0, x1 = last_range
        fig.update_layout(
            selections=[
                dict(
                    x0=x0,
                    x1=x1,
                    y0=0,
                    y1=1,
                    xref="x",
                    yref="paper",
                )
            ]
        )
        fig.add_shape(
            type="rect",
            xref="x",
            yref="paper",
            x0=x0,
            x1=x1,
            y0=0,
            y1=1,
            fillcolor="rgba(255,0,0,0.2)",
            line_width=0,
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
    Input("experiment", "data"),
    Input("freq-selection", "data"),
    Input("fill-gaps", "value"),
    State("azel-selection", "data"),
    State("base-freq", "value"),
)
def update_map(experiment, frng, fill_gaps, azel_selection, base_freq):
    if not 'foldername' in experiment:
        return no_update

    base_freq = float(base_freq) or 0
    fig = plot(experiment, frng, base_freq, 'fill' in fill_gaps)

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

