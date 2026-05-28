# rdf-config

## Overview
`process-config.py` reads a SHACL-annotated Turtle file (`config.ttl`) and builds
runtime Python classes from the shapes, plus generates matching Python source for
inspection.

## Key files
- `config.ttl` — RDF data + SHACL shapes; validated with `pyshacl -i rdfs config.ttl -f human`
- `process-config.py` — main pipeline: extract shapes → build classes → populate identity map

## Pipeline
1. `extract_shapes(g)` — reads `sh:NodeShape` subjects, collects `sh:property` tuples:
   `(path, datatype, class_uri, min_count, max_count)`
2. `build_runtime(g, class_prefix)` — creates a `Context`, registers one class per shape
3. `Context.resolve(uri, g, shapes)` — materialises instances into the identity map

## Cardinality rules
- `sh:maxCount 1` → scalar member (`str`, `int`, `nicegui__Foo`, …)
- no `sh:maxCount` or `> 1` → `list[...]` member, fetched with `g.objects()`

## Conventions
- `rdf:type` properties are stripped from shapes — they exist only for SHACL validation
- CURIEs passed to `resolve_curie` must start with `:` (default prefix) or `http`; anything else raises `ValueError`
- Generated class names use a configurable prefix (default `nicegui__`); pass `class_prefix=` to `build_runtime` / `make_class`
- `Context.__getattr__` resolves dot-access via the default prefix (e.g. `ctx.fig1`)
- `__getattr__` on instances lazily resolves `URIRef` values (and lists of them) through the identity map
