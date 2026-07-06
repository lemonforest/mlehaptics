"""siona.introspect — make Siona know her OWN tooling (F1084). Introspect the LIVE srmech package (every
op: name + signature + first-line docstring + module) into knowledge kernels Siona grounds with her own
encoder, so a natural-language tooling question — "how do I recall a kernel from a genome" — answers from
Siona's own knowledge instead of a hand-run ``dir()``/``inspect.signature()`` snapshot.

This is the ultimate dogfood (F1083/F1084): ASK SIONA about her tooling, don't re-introspect. Because the
knowledge kernels are built from the LIVE package each time, they never lag the format — the rc123→v11 genome
drift that silently corrupted the store (F1084) would have been a query away. It is also the substrate for the
front-filter (Siona as the knowledge front-end for her own capabilities).

srmech-native: `s.g.enc_query` encodes each op-description to a Klein-4 HV; Class-M `klein4_similarity` grounds
a query to the nearest op. numpy-free.
"""
import importlib
import inspect
from srmech.amsc import hdc as _hdc

__all__ = ["introspect_srmech", "Tooling", "SRMECH_MODULES"]

SRMECH_MODULES = [
    "srmech.amsc.genome", "srmech.amsc.laplacian", "srmech.amsc.hdc", "srmech.amsc.cascade",
    "srmech.amsc.rational", "srmech.amsc.format", "srmech.amsc.cyclic", "srmech.calculus",
    "srmech.amsc.coupling", "srmech.amsc.carrier_ladder",
]


def introspect_srmech(modules=None):
    """``{qualified_op_name: "name(signature) :: first-line docstring"}`` for every callable op in the LIVE
    package — the self-knowledge source, current by construction (re-read each call)."""
    out = {}
    for modname in (modules or SRMECH_MODULES):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        short = modname.split(".")[-1]
        for name in dir(mod):
            if name.startswith("_") or name[:1].isupper():          # ops are lower_snake; skip classes/typing
                continue
            obj = getattr(mod, name)
            if not callable(obj):
                continue
            try:
                sig = str(inspect.signature(obj))
            except (ValueError, TypeError):
                sig = "(...)"
            doc = (inspect.getdoc(obj) or "").split("\n")[0].strip()
            out["%s.%s" % (short, name)] = "%s%s :: %s" % (name, sig, doc)
    return out


class Tooling:
    """Siona's self-knowledge of her tooling. Encodes every live srmech op-description with the Session's own
    encoder; ``answer(query)`` grounds a natural-language tooling question to the nearest ops (F1084)."""

    def __init__(self, grounder, modules=None):
        self._g = grounder
        self.kb = introspect_srmech(modules)                        # {label: description} — live, never stale
        self.labels = list(self.kb)
        self._vecs = [grounder.enc_query(self.kb[l]) for l in self.labels]

    def answer(self, query, k=3):
        """Ground a tooling question to the k nearest ops. Returns ``[(label, description, similarity)]`` —
        Siona answering about her OWN tooling from her OWN encoded knowledge."""
        qv = self._g.enc_query(query)
        scored = sorted(
            ((_hdc.klein4_similarity(qv, v).as_float(), l) for l, v in zip(self.labels, self._vecs)),
            reverse=True)
        return [(l, self.kb[l], round(s, 3)) for s, l in scored[:k]]
