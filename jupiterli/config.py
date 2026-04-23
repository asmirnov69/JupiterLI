from rdflib import Graph, RDF, URIRef
from jupiterli.plots import Plot

JLI = "http://example.com/jupiterli#"
SCRATCH = "http://example.com/scratch#"

_CURVE_METHODS = {
    URIRef(JLI + "Scatter"): "add_scatter",
    URIRef(JLI + "TimeseriesScatter"): "add_timeseries_scatter",
    URIRef(JLI + "Histogram"): "add_histogram",
}


def load_config(pl, ttl_path):
    g = Graph()
    g.parse(ttl_path, format="turtle")

    title = URIRef(SCRATCH + "title")
    on_plot = URIRef(SCRATCH + "on_plot")
    redis_key = URIRef(SCRATCH + "redis_key")

    plots = {}
    for s in g.subjects(RDF.type, URIRef(JLI + "Plot")):
        plots[s] = Plot(pl, str(g.value(s, title)))

    for curve_type, method_name in _CURVE_METHODS.items():
        for s in g.subjects(RDF.type, curve_type):
            plot = plots[g.value(s, on_plot)]
            getattr(plot, method_name)(str(g.value(s, redis_key)))

    return plots
