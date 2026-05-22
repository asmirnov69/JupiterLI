import asyncio, os, pathlib, sys, uuid
from nicegui import ui, app
from starlette.requests import Request
from .redis_utils import RedisLoop
from .plotter_loop import PlotterLoop
from .config import load_config
from rdflib import Graph, URIRef, Namespace
from clickhouse_driver import Client

TTL_PATH = sys.argv[1] # "examples/producer.ttl"
PKG_DIR = pathlib.Path(__file__).parent

class NiceGUIApplication:
    def __init__(self):
        self.g = None
        self.ch = Client(host="localhost", port=9000, user="default", password="", database="default")
        self.series_ids_d = {} # key => series_id

    def verify_prefixes(self, g:Graph):
        known_prefixes = {
            "rdf": URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
            "jli": URIRef("http://example.com/jupiterli#")
        }
        
        any_errors = False
        for prefix, namespace in g.namespaces():
            if prefix in known_prefixes:
                #print(prefix, namespace)
                #print(type(prefix), type(namespace))
                if known_prefixes.get(prefix) != namespace:
                    print("problem with prefix", prefix)
                    any_errors = True

        if any_errors:
            print("prefix verification failed")
            sys.exit(2)

    def load_series_ids_d(self, run_id):
        if run_id is None:
            rows = self.ch.execute("select run_id from runs_dets where created_ts = (select max(created_ts) from runs_dets)")
            if len(rows) == 1:
                run_id = rows[0][0]
            else:
                raise Exception("can't find latest run_id")
        ui.page_title(f"run_id={run_id}")
        rows = self.ch.execute(f"select series_id, key from series_dets where run_id = '{run_id}'")
        for r in rows:
            series_id, key = r
            self.series_ids_d[series_id] = key
        print("series_ids_d:", self.series_ids_d)
        
    def load_config_graph(self):
        jli_shacl_ttl_path = os.path.join(PKG_DIR, "ttl/jli-shacl.ttl")
        try:
            shapes_g = Graph()
            print("parsing", jli_shacl_ttl_path)
            shapes_g.parse(jli_shacl_ttl_path, format = "turtle")
            self.verify_prefixes(shapes_g)
        except Exception as e:
            print(f">>> exception during parse of {jli_shacl_ttl_path}")
            print(e)
            sys.exit(2)

        try:
            print("parsing", TTL_PATH)
            data_g = Graph()
            data_g.parse(TTL_PATH, format="turtle")
            self.verify_prefixes(data_g)
        except Exception as e:
            print(f">>> exception during parse of {TTL_PATH}")
            print(e)
            sys.exit(2)

        # this way of merged graph construction retain order of triples, maybe broken in future
        self.g = Graph()
        self.g.parse(jli_shacl_ttl_path, format = "turtle")
        self.g.parse(TTL_PATH, format = "turtle")

    async def clear_page(self, rl):
        await rl.flush()
        ui.run_javascript('location.reload()')        
        
    def launch(self, request:Request):
        run_id = request.query_params.get('run_id')
        rl = RedisLoop(self)
        pl = PlotterLoop(rl)

        #ui.button('Clear', on_click=lambda: print('Hello from new button', flush=True)).classes('absolute top-2 left-2 z-50')
        #ui.button('Clear', on_click=lambda: rl.flush()).classes('absolute top-2 left-2 z-50')
        ui.button('Clear', on_click=lambda: self.clear_page(rl)).classes('absolute top-2 left-2 z-50')

        self.load_series_ids_d(run_id)
        load_config(self.g, pl)
        
        loop = asyncio.get_event_loop()
        loop.create_task(pl.loop())
        
        redis_task = loop.create_task(rl.loop())
        redis_task.set_name(f"redis-task--{uuid.uuid4().hex[:8]}")
        ui.context.client.on_disconnect(redis_task.cancel)
        

def _watched_mtimes():
    paths = [TTL_PATH, *(str(p) for p in PKG_DIR.rglob("*.py"))]
    out = {}
    for path in paths:
        try:
            out[path] = os.stat(path).st_mtime
        except FileNotFoundError:
            pass
    return out


async def _watch_files():
    last = _watched_mtimes()
    while True:
        await asyncio.sleep(1.0)
        current = _watched_mtimes()
        for path, mtime in current.items():
            if path in last and mtime != last[path]:
                print(f"{path} changed, restarting...", flush=True)
                os.execv(sys.executable, [sys.executable, *sys.argv])
        last = current


def main():
    nicegui_app = NiceGUIApplication()
    nicegui_app.load_config_graph()
    ui.page('/')(nicegui_app.launch)
    app.on_startup(_watch_files)
    ui.run(reload=False)


if __name__ in {"__main__", "__mp_main__"}:
    main()
