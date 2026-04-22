import datetime
import json
from nicegui import ui
import plotly.graph_objects as go


def make_plot__(title):
    fig = go.Figure()
    fig.update_layout(title=title, autosize=True, uirevision='constant')
    return fig


def _extend_traces(element, update_dict, trace_indices):
    # Reach into the mounted Plotly Vue instance and call extendTraces on it.
    # This streams only the new points to the client, unlike fig.update() which
    # calls Plotly.react() and disrupts an in-progress pan/zoom gesture.
    js = (
        f"const vue = getElement({element.id});"
        f"if (vue && vue.Plotly && vue.$el) {{"
        f"  vue.Plotly.extendTraces(vue.$el, {json.dumps(update_dict)}, {json.dumps(trace_indices)});"
        f"}}"
    )
    element.client.run_javascript(js)


class Histogram:
    def __init__(self, plot, data_idx):
        self.plot = plot
        self.data_idx = data_idx
        self.xs = []
        self._pending_x = []
        self.plot.fig.figure.add_histogram(x=[])

    def append_curve(self, stream_messages):
        new_xs = [float(it['value']) for it in stream_messages]
        self.xs.extend(new_xs)
        self._pending_x.extend(new_xs)

    def flush(self):
        if not self._pending_x:
            return
        xs, self._pending_x = self._pending_x, []
        _extend_traces(self.plot.fig, {'x': [xs]}, [self.data_idx])


class Scatter:
    def __init__(self, plot, data_idx):
        self.plot = plot
        self.data_idx = data_idx
        self.xs = []
        self.ys = []
        self._pending_x = []
        self._pending_y = []
        self.plot.fig.figure.add_scatter(x=[], y=[], mode='lines+markers')

    def append_curve(self, stream_messages):
        new_ys = [float(it['value']) for it in stream_messages]
        start = len(self.ys)
        new_xs = list(range(start, start + len(new_ys)))
        self.xs.extend(new_xs)
        self.ys.extend(new_ys)
        self._pending_x.extend(new_xs)
        self._pending_y.extend(new_ys)

    def flush(self):
        if not self._pending_x:
            return
        xs, self._pending_x = self._pending_x, []
        ys, self._pending_y = self._pending_y, []
        _extend_traces(self.plot.fig, {'x': [xs], 'y': [ys]}, [self.data_idx])


class TimeseriesScatter:
    def __init__(self, plot, data_idx):
        self.plot = plot
        self.data_idx = data_idx
        self.xs = []
        self.ys = []
        self._pending_x = []
        self._pending_y = []
        self.plot.fig.figure.add_scatter(x=[], y=[], mode='lines+markers')

    def append_curve(self, stream_messages):
        new_xs = [datetime.datetime.fromtimestamp(float(it['timestamp'])) for it in stream_messages]
        new_ys = [float(it['value']) for it in stream_messages]
        self.xs.extend(new_xs)
        self.ys.extend(new_ys)
        self._pending_x.extend(new_xs)
        self._pending_y.extend(new_ys)

    def flush(self):
        if not self._pending_x:
            return
        xs_iso = [x.isoformat() for x in self._pending_x]
        ys = self._pending_y
        self._pending_x, self._pending_y = [], []
        _extend_traces(self.plot.fig, {'x': [xs_iso], 'y': [ys]}, [self.data_idx])


class Plot:
    def __init__(self, pl, title):
        self.pl = pl
        self.pl.plots.add(self)
        self.curves = []
        self.fig = ui.plotly(make_plot__(title=title)).style('width: 100%; height: 100%;')

    def add_scatter(self, redis_key):
        new_scatter = Scatter(self, data_idx=len(self.fig.figure.data))
        self.curves.append(new_scatter)
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)
        self.pl.scatters.setdefault(redis_key, []).append(new_scatter)

    def add_timeseries_scatter(self, redis_key):
        new_scatter = TimeseriesScatter(self, data_idx=len(self.fig.figure.data))
        self.curves.append(new_scatter)
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)
        self.pl.scatters.setdefault(redis_key, []).append(new_scatter)

    def add_histogram(self, redis_key):
        new_hist = Histogram(self, data_idx=len(self.fig.figure.data))
        self.curves.append(new_hist)
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)
        self.pl.histograms.setdefault(redis_key, []).append(new_hist)

    def flush(self):
        for curve in self.curves:
            curve.flush()
