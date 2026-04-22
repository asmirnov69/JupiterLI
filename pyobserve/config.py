from rdflib import Graph, RDF, URIRef
from pyobserve.plots import Plot

NICEGUI = "http://example.com/nicegui#"
SCRATCH = "http://example.com/scratch#"

_CURVE_METHODS = {
    URIRef(NICEGUI + "Scatter"): "add_scatter",
    URIRef(NICEGUI + "TimeseriesScatter"): "add_timeseries_scatter",
    URIRef(NICEGUI + "Histogram"): "add_histogram",
}


def load_config(pl, ttl_path):
    g = Graph()
    g.parse(ttl_path, format="turtle")

    title = URIRef(SCRATCH + "title")
    on_plot = URIRef(SCRATCH + "on_plot")
    redis_key = URIRef(SCRATCH + "redis_key")

    plots = {}
    for s in g.subjects(RDF.type, URIRef(NICEGUI + "Plot")):
        plots[s] = Plot(pl, str(g.value(s, title)))

    for curve_type, method_name in _CURVE_METHODS.items():
        for s in g.subjects(RDF.type, curve_type):
            plot = plots[g.value(s, on_plot)]
            getattr(plot, method_name)(str(g.value(s, redis_key)))

    return plots
