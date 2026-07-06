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

__all__ = ["build", "load_or_build", "stream_descriptions"]


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
