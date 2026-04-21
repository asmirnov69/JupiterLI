import asyncio, uuid
from nicegui import ui
import plotly.graph_objects as go
import datetime
from redis_utils import RedisLoop

class Histogram:
    def __init__(self, plot, data_idx):
        self.plot = plot
        self.plot.fig.figure.add_histogram(x = [])
        self.data_idx = data_idx

    def append_curve(self, stream_messages):
        #print("Histogram::append_curve:", stream_messages)
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
        #self.plot.fig.figure.add_scatter(x = [1,2,3], y = [1,2,3], mode = self.mode)
        self.plot.fig.figure.add_scatter(x = [], y = [], mode = self.mode)

    def append_curve(self, stream_messages):
        #print(stream_messages[-10:])
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
        #self.plot.fig.figure.add_scatter(x = [1,2,3], y = [1,2,3], mode = self.mode)
        self.plot.fig.figure.add_scatter(x = [], y = [], mode = self.mode)

    def append_curve(self, stream_messages):
        #print(stream_messages[-10:])
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

        
def make_plot__(title):
    fig = go.Figure()
    #fig.add_scatter(x=[1,2,3], y=[1,2,3], mode='lines+markers')
    fig.update_layout(title=title, autosize=True, uirevision='constant')
    return fig

class Plot:
    def __init__(self, pl:"PlotterLoop", title):
        self.pl = pl
        self.pl.plots.add(self)
        self.fig = ui.plotly(make_plot__(title = title)).style('width: 100%; height: 100%;')

    def add_scatter(self, redis_key):
        new_scatter = Scatter(self, data_idx = len(self.fig.figure.data))
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)

        if not redis_key in self.pl.scatters:
            self.pl.scatters[redis_key] = []
        self.pl.scatters[redis_key].append(new_scatter)

    def add_timeseries_scatter(self, redis_key):
        new_scatter = TimeseriesScatter(self, data_idx = len(self.fig.figure.data))
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)

        if not redis_key in self.pl.scatters:
            self.pl.scatters[redis_key] = []
        self.pl.scatters[redis_key].append(new_scatter)
        
    def add_histogram(self, redis_key):
        new_hist = Histogram(self, data_idx = len(self.fig.figure.data))
        self.pl.rl.subscribe(redis_key, self.pl.handle_messages)

        if not redis_key in self.pl.histograms:
            self.pl.histograms[redis_key] = []
        self.pl.histograms[redis_key].append(new_hist)
    
class PlotterLoop:
    def __init__(self, rl:RedisLoop):
        self.rl = rl
        self.plots = set()
        self.scatters = {} # key -> list[Scatter]
        self.histograms = {} # key -> list[Histogram]
    
    def handle_messages(self, key, messages):
        curves = self.scatters[key] if key in self.scatters else []
        curves.extend(self.histograms[key] if key in self.histograms else [])
        for sct in curves:
            sct.append_curve(messages)

    async def loop(self):
        # first update to show all figures
        for plot in self.plots:
            plot.fig.update()
        
        while True:
            await self.rl.batch_is_done.wait()
            self.rl.batch_is_done = asyncio.Event()
            for plot in self.plots:
                plot.fig.update()

    
ui_client_connected = asyncio.Event()
def save_client():
    global ui_client_connected
    ui_client_connected.set()

async def real_start(rl):
    print("real_start")
    await ui_client_connected.wait()
    print("client connected")
    await rl.loop()

main_task = None

def cleanup():
    global main_task
    print("task to cancel:", main_task.get_name())
    main_task.cancel()
    print("cleanup is done")
    
def main():
    print("=====================")
    ui.context.client.on_connect(save_client) # logic to handle waiting for client connect
    rl = RedisLoop()
    pl = PlotterLoop(rl)

    if 0:
        fig1 = Plot(pl, "fig1")
        fig1.add_timeseries_scatter("data1")
        fig1.add_timeseries_scatter("data2")

    fig2 = Plot(pl, "fig2")
    fig2.add_histogram("data1")

    fig3 = Plot(pl, "fig3")
    fig3.add_scatter("data1")
    
    asyncio.get_event_loop().create_task(pl.loop())
    
    # automatic run on page start
    global main_task
    main_task = asyncio.get_event_loop().create_task(real_start(rl))
    main_task_name = f"main-task--{uuid.uuid4().hex[:8]}"
    print("name of brand new main_task:", main_task_name)
    main_task.set_name(main_task_name)
    ui.context.client.on_disconnect(cleanup)

    ui.run()

if __name__ in {"__main__", "__mp_main__"}:
    main()
