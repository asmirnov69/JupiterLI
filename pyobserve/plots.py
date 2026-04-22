import datetime
from nicegui import ui
import plotly.graph_objects as go


def make_plot__(title):
    fig = go.Figure()
    fig.update_layout(title=title, autosize=True, uirevision='constant')
    return fig


class Histogram:
    def __init__(self, plot, data_idx):
        self.plot = plot
        self.plot.fig.figure.add_histogram(x = [])
        self.data_idx = data_idx

    def append_curve(self, stream_messages):
        old_xs = list(self.plot.fig.figure.data[self.data_idx].x)
        delta_xs = [float(it['value']) for it in stream_messages]
        print(f"delta_xs: {len(delta_xs)}")
        new_xs = old_xs + delta_xs
        print(f"new_xs: {len(new_xs)}")
        self.plot.fig.figure.data[self.data_idx].x = new_xs


class Scatter:
    def __init__(self, plot, data_idx):
        self.plot = plot
        self.data_idx = data_idx
        self.mode = 'lines+markers'
        self.plot.fig.figure.add_scatter(x = [], y = [], mode = self.mode)

    def append_curve(self, stream_messages):
        old_ys = list(self.plot.fig.figure.data[self.data_idx].y)
        delta_ys = [float(it['value']) for it in stream_messages]
        print(f"old_ys: {len(old_ys)}, delta_ys: {len(delta_ys)}")
        new_ys = old_ys + delta_ys
        new_xs = list(range(len(new_ys)))
        print(f"new_xs: {len(new_xs)}, new_ys: {len(new_ys)}")
        self.plot.fig.figure.data[self.data_idx].x = new_xs
        self.plot.fig.figure.data[self.data_idx].y = new_ys


class TimeseriesScatter:
    def __init__(self, plot, data_idx):
        self.plot = plot
        self.data_idx = data_idx
        self.mode = 'lines+markers'
        self.plot.fig.figure.add_scatter(x = [], y = [], mode = self.mode)

    def append_curve(self, stream_messages):
        old_ys = list(self.plot.fig.figure.data[self.data_idx].y)
        delta_ys = [float(it['value']) for it in stream_messages]
        print(f"old_ys: {len(old_ys)}, delta_ys: {len(delta_ys)}")
        new_ys = old_ys + delta_ys
        old_xs = list(self.plot.fig.figure.data[self.data_idx].x)
        delta_xs = [datetime.datetime.fromtimestamp(float(it['timestamp'])) for it in stream_messages]
        new_xs = old_xs + delta_xs
        print(f"new_xs: {len(new_xs)}, new_ys: {len(new_ys)}")
        self.plot.fig.figure.data[self.data_idx].x = new_xs
        self.plot.fig.figure.data[self.data_idx].y = new_ys


class Plot:
    def __init__(self, pl, title):
        self.pl = pl
        self.pl.plots.add(self)
        self.fig = ui.plotly(make_plot__(title=title)).style('width: 100%; height: 100%;')

    def add_scatter(self, redis_key):
        new_scatter = Scatter(self, data_idx=len(self.fig.figure.data))
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)
        self.pl.scatters.setdefault(redis_key, []).append(new_scatter)

    def add_timeseries_scatter(self, redis_key):
        new_scatter = TimeseriesScatter(self, data_idx=len(self.fig.figure.data))
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)
        self.pl.scatters.setdefault(redis_key, []).append(new_scatter)

    def add_histogram(self, redis_key):
        new_hist = Histogram(self, data_idx=len(self.fig.figure.data))
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)
        self.pl.histograms.setdefault(redis_key, []).append(new_hist)
