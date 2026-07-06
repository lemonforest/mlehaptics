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


def _default_source_dirs():
    """The live source to mine for usage examples: the installed srmech package (op call-sites + docstring
    examples) and siona's own package (our real call-sites) — the human-written demonstrators (F1086)."""
    import os
    import srmech
    return [os.path.dirname(srmech.__file__), os.path.dirname(os.path.abspath(__file__))]


def mine_usage(op_labels, source_dirs=None, *, max_per_op=4):
    """Learning by IMITATION (F1086): scan ``source_dirs`` for real call-sites of each op → ``{label:
    [example_line, …]}``. These WORKING EXAMPLES are the how-to-USE (procedural) knowledge that the signature
    (declarative, being-TOLD) omits. Cross-substrate imitation: Siona learns from the human-written examples."""
    import os
    import re
    short2full = {}
    for lab in op_labels:
        short2full.setdefault(lab.split(".")[-1], lab)              # first module wins on a name collision
    usage = {lab: [] for lab in op_labels}
    call_re = re.compile(r"\b([a-z_][a-z0-9_]*)\s*\(")
    for d in (source_dirs or _default_source_dirs()):
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                try:
                    txt = open(os.path.join(root, fn), encoding="utf-8", errors="ignore").read()
                except Exception:
                    continue
                for ln in txt.split("\n"):
                    s = ln.strip()
                    if not (12 < len(s) < 180) or s.startswith(("def ", "#", "async def ")):
                        continue
                    for name in set(call_re.findall(s)):
                        full = short2full.get(name)
                        if full and ("def " + name) not in s and s not in usage[full] and len(usage[full]) < max_per_op:
                            usage[full].append(s)
    return usage


class Tooling:
    """Siona's self-knowledge of her tooling — BOTH tiers (F1084/F1086): learning by being TOLD (op
    signature/docstring, ``answer``) AND learning by IMITATION (real usage examples, ``how_to``). Told is the
    index; imitation is the runnable. Both built from the LIVE package/source, so neither lags the format."""

    def __init__(self, grounder, modules=None, *, mine=True, source_dirs=None):
        self._g = grounder
        self.kb = introspect_srmech(modules)                        # TOLD: {label: description} — live, never stale
        self.labels = list(self.kb)
        self._vecs = [grounder.enc_query(self.kb[l]) for l in self.labels]
        self.usage = mine_usage(self.labels, source_dirs) if mine else {}   # IMITATION: {label: [examples]}

    def answer(self, query, k=3):
        """TOLD tier: ground a tooling question to the k nearest ops → ``[(label, description, similarity)]``."""
        qv = self._g.enc_query(query)
        scored = sorted(
            ((_hdc.klein4_similarity(qv, v).as_float(), l) for l, v in zip(self.labels, self._vecs)),
            reverse=True)
        return [(l, self.kb[l], round(s, 3)) for s, l in scored[:k]]

    def how_to(self, query, k=1, n=3):
        """IMITATION tier (F1086): ground the query to the op (TOLD), then SHOW ``n`` real working examples
        (IMITATION) of how it is actually called. Returns ``[(label, description, [usage_examples])]`` — the
        runnable how-to, not just the signature. This is what the #249 genome bug needed: the composition, shown."""
        return [(lab, desc, self.usage.get(lab, [])[:n]) for lab, desc, _ in self.answer(query, k=k)]
