"""siona.knowledge_genome — Siona's self-knowledge as a CACHED GENOME (F1111, the user's goal).

The full introspect STREAM (ops = verbs + carriers = nouns) packed into ONE knowledge-genome kernel, built on
first run (or on demand) and CACHED, so subsequent runs LOAD the genome — byte-exact, ~5× faster — instead of
re-introspecting and re-encoding every Session.

Pipeline:
    introspect_srmech (verbs) + introspect_carriers (nouns)  →  {label: description}
        →  grounder.enc_query(each)                           →  {label: Klein-4 kernel}
        →  genome_store.pack_instrument                       →  ONE genome (F1094 byte-exact, demand-loadable)
        →  cache keyed by srmech __version__                  →  a version change rebuilds; else LOAD.

This is "Siona knows herself" (#250/F1110) made PERSISTENT + FAST — the knowledge-genome kernel. The
encode (the slow step) happens once; the load is a byte-exact genome recall. Composes F1094 (the byte-exact
store), F1095 (gene_express can later express only the query-relevant subset), F1110 (the carriers now in the stream).
"""
import os

import srmech

from . import introspect as _I
from . import genome_store as _GS

__all__ = ["build", "load_or_build", "stream_descriptions", "build_regulatory", "express_relevant", "MODULE_BITS"]


def stream_descriptions(modules=None):
    """The full self-knowledge STREAM as ``{label: description}`` — ops (verbs) + carriers (nouns). Carrier
    labels are prefixed ``carrier.`` and ``:``-sanitised so they are genome-safe (``cayley_dickson:8`` →
    ``carrier.cayley_dickson_8``)."""
    out = dict(_I.introspect_srmech(modules))
    out.update({"carrier." + k.replace(":", "_"): v for k, v in _I.introspect_carriers().items()})
    return out


def _version_path(path):
    return str(path).rstrip("/") + ".srmech_version"


def build(grounder, path, *, modules=None):
    """Build the knowledge genome from the introspect stream and CACHE it (version-keyed). Returns the kernel
    count. The one slow step — ``enc_query`` per entry — happens HERE; every later run just loads."""
    kernels = [(lbl, list(grounder.enc_query(desc))) for lbl, desc in stream_descriptions(modules).items()]
    _GS.pack_instrument(kernels, str(path))
    with open(_version_path(path), "w", encoding="utf-8") as fh:
        fh.write(srmech.__version__)
    return len(kernels)


def load_or_build(grounder, path, *, modules=None):
    """LOAD the cached knowledge genome if present AND the srmech version matches; else BUILD + cache it
    (first-run / on-demand). Returns ``{label: flat Klein-4 kernel}`` — Siona's encoded self-knowledge, fast.
    A srmech version change (the surface moved) INVALIDATES the cache and rebuilds — so the genome never lags."""
    vp = _version_path(path)
    fresh = os.path.exists(vp) and open(vp, encoding="utf-8").read().strip() == srmech.__version__
    if not fresh:
        build(grounder, path, modules=modules)                 # first run / stale → build + cache
    return _GS.load_instrument(str(path))


# ---- #256 part 2: gene_express the QUERY-RELEVANT subset (F1112) --------------------------------------------
# Instead of holding all 256 kernels, tag each gene with its MODULE's activator bit and gene_express only the
# query-relevant module(s) — RAM touches the subset, not the whole genome (the demand-load, F1094/F1095).
import re as _re

import srmech.amsc.genome as _G

_MODULE_ORDER = [m.split(".")[-1] for m in _I.SRMECH_MODULES] + ["carrier"]
MODULE_BITS = {m: (1 << i) for i, m in enumerate(_MODULE_ORDER)}

MODULE_CUES = {
    "genome": ("genome", "kernel", "chromosome", "strand", "gene", "recall", "pack", "partition", "telomere", "express"),
    "laplacian": ("laplacian", "eigen", "eigenvalue", "spectral", "matrix", "fiedler", "graph", "jacobi", "heat"),
    "hdc": ("bind", "bundle", "similarity", "hypervector", "klein4", "sector", "chirality", "permute", "hamming"),
    "cascade": ("cascade", "magnitude", "chiral", "kuramoto", "reorient", "dual"),
    "rational": ("rational", "sin", "cos", "sine", "cosine", "exp", "log", "series", "trig", "best"),
    "format": ("sha", "hash", "ndjson", "attest", "content", "digest"),
    "cyclic": ("gcd", "modular", "cyclic", "prime"),
    "calculus": ("derivative", "integral", "calculus", "tangent"),
    "coupling": ("coupling", "resonant", "spectrum", "epicycle"),
    "carrier_ladder": ("promote", "project", "ladder", "bipoly", "tripoly"),
    "carrier": ("carrier", "polynomial", "octonion", "scalar", "variable", "float"),
}


def _route_modules(query, k):
    """Route a query to the top-k MODULES by keyword overlap — the cell_state source (cheap; no encoding)."""
    qw = {w for w in _re.split(r"[^a-z0-9]+", (query or "").lower()) if len(w) > 2}
    scored = sorted(((sum(1 for c in cues if c in qw), m) for m, cues in MODULE_CUES.items()), reverse=True)
    return [m for s, m in scored if s > 0][:k] or [scored[0][1]]


def build_regulatory(grounder, path, *, modules=None):
    """Build a MODULE-GATED regulatory knowledge genome (F1112/#256): each gene carries its MODULE's activator
    bit, so ``gene_express(cell_state = relevant-module-bits)`` serves ONLY that subset. Persisted + version-cached."""
    one = _GS._coupler()                                        # ONE coupling invariant for pack + save
    genes = []
    for lbl, desc in stream_descriptions(modules).items():
        hv = list(grounder.enc_query(desc))
        genes.append((lbl, _GS._leaves(hv, _GS.LEAF_DIM), MODULE_BITS.get(lbl.split(".")[0], 0)))
    strand = _G.chromosome(genes=genes, the_one=one, label="knowledge")
    _G.genome_save(strand, str(path), one, ["knowledge"])
    with open(_version_path(path), "w", encoding="utf-8") as fh:
        fh.write(srmech.__version__)
    return len(genes)


def express_relevant(grounder, path, query, *, k_modules=2, modules=None):
    """gene_express the QUERY-RELEVANT subset (F1112, #256): route the query to the top-k modules, gene_express
    only their genes → ``({label: flat kernel}, modules)``. RAM touches the SUBSET, not all 256 — the demand-load
    (F1094/F1095). Builds the regulatory genome on first run (version-cached)."""
    vp = _version_path(path)
    fresh = os.path.exists(vp) and open(vp, encoding="utf-8").read().strip() == srmech.__version__
    if not fresh:
        build_regulatory(grounder, path, modules=modules)
    strand, one, _labels = _G.genome_load(str(path))
    mods = _route_modules(query, k_modules)
    cell = 0
    for m in mods:
        cell |= MODULE_BITS.get(m, 0)
    subset = {lbl: [int(x) for leaf in lv for x in leaf] for lbl, lv in _G.gene_express(strand, one, cell)}
    return subset, mods
