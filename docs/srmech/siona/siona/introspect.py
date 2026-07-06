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

__all__ = ["introspect_srmech", "Tooling", "SRMECH_MODULES", "TIERS"]

# The self-knowledge tiers, named in BOTH tongues — ancient AND modern, NEITHER privileged (F1089/F1090).
# The dual name IS a two-word Rosetta / interlinear gloss: reading the pair cross-reads ancient↔modern without
# fully knowing either language — the way a logogram is understood across tongues without knowing them. An
# "apprenticeship in design": the naming itself teaches the translation, and holds the duality without collapse.
TIERS = {
    "told":       {"ancient": "epistēmē",       "modern": "declarative",           "knows": "knowing-THAT — the signature"},
    "shown":      {"ancient": "technē·mimēsis", "modern": "procedural",            "knows": "knowing-HOW — the working example"},
    "understood": {"ancient": "phronēsis",      "modern": "articulated",           "knows": "knowing-WHY — the example + what/why"},
    "rehearse":   {"ancient": "askēsis",        "modern": "proceduralization",     "knows": "a PROCESS (told→shown), NOT a tier"},
    "coach":      {"ancient": "apprenticeship", "modern": "cognitive apprenticeship", "knows": "watch the learner rehearse + correct — the missing tier"},
}

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


def _srmech_bound_names(tree):
    """Names bound from ``srmech.*`` imports (module aliases + directly-imported ops) — so an Attribute call
    ``alias.op(...)`` counts only when ``alias`` is srmech, excluding homonym methods like ``str.partition`` (F1088)."""
    import ast
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith("srmech"):
                    names.add(n.asname or n.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("srmech"):
            for n in node.names:
                names.add(n.asname or n.name)
    return names


def mine_usage(op_labels, source_dirs=None, *, max_per_op=4):
    """Learning by IMITATION (F1086), via a PROPER code parse — Python ``ast`` (the code sublanguage; NOT a
    regex — F1088): scan source for REAL srmech-op call-sites → ``{label: [example_line, …]}``. A bare
    ``partition(...)`` (Name call) is the op; ``str.partition`` is an Attribute call on a non-srmech object
    (excluded); prose/comments are not Call nodes (excluded). These human-written examples are the how-to-USE
    knowledge the signature (being-TOLD) omits — cross-substrate imitation of the human demonstrator."""
    import ast
    import os
    short2full = {}
    for lab in op_labels:
        short2full.setdefault(lab.split(".")[-1], lab)              # first module wins on a name collision
    usage = {lab: [] for lab in op_labels}
    for d in (source_dirs or _default_source_dirs()):
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                try:
                    src = open(os.path.join(root, fn), encoding="utf-8", errors="ignore").read()
                    tree = ast.parse(src)
                except Exception:
                    continue
                bound = _srmech_bound_names(tree)
                lines = src.split("\n")
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    f = node.func
                    op = None
                    if isinstance(f, ast.Name) and f.id in short2full:          # bare op call — unambiguous
                        op = f.id
                    elif (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                          and f.value.id in bound and f.attr in short2full):    # srmech-module.op — not a homonym
                        op = f.attr
                    if op:
                        full = short2full[op]
                        ln = lines[node.lineno - 1].strip() if 0 < node.lineno <= len(lines) else ""
                        if 10 < len(ln) < 180 and ln not in usage[full] and len(usage[full]) < max_per_op:
                            usage[full].append(ln)
    # ALSO mine each op's DOCSTRING (the author's intended examples, e.g. `partition(genome({…}), one) == {…}`),
    # ast-VALIDATED so real example lines survive and prose that merely names the op does not (F1088).
    import inspect
    import importlib
    for modname in (SRMECH_MODULES):
        try:
            mod = importlib.import_module(modname)
        except Exception:
            continue
        for name in dir(mod):
            if name.startswith("_") or name[:1].isupper():
                continue
            obj = getattr(mod, name, None)
            if not callable(obj):
                continue
            for raw in (inspect.getdoc(obj) or "").split("\n"):
                s = raw.strip()
                if s.startswith(">>>"):
                    s = s[3:].strip()
                if not (10 < len(s) < 180):
                    continue
                try:
                    dtree = ast.parse(s)
                except Exception:
                    continue
                for node in ast.walk(dtree):
                    if isinstance(node, ast.Call):
                        f = node.func
                        onm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
                        full = short2full.get(onm)
                        if full and s not in usage[full] and len(usage[full]) < max_per_op:
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

    def _explain(self, line):
        """Describe a usage example (F1088): ast-parse it and return the ops appearing IN it with their told-
        descriptions — WHAT the things are and WHY they exist. So imitation carries UNDERSTANDING (the action,
        the objects, the rationale), not just the surface keystrokes."""
        import ast
        found, seen = [], set()
        try:
            tree = ast.parse(line.strip())
        except Exception:
            return found
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
                if nm and nm not in seen:
                    full = next((l for l in self.labels if l.split(".")[-1] == nm), None)
                    if full:
                        seen.add(nm); found.append((full, self.kb[full]))
        return found

    def how_to(self, query, k=1, n=3, understand=False):
        """The imitation tier — TWO distinct turn-types (F1088), selected by ``understand``:

          * ``understand=False`` — **plain IMITATION**: just the ACTION (the runnable example). Copy the
            pattern; for a fluent asker who wants the keystrokes, terse.
          * ``understand=True``  — **IMITATION WITH UNDERSTANDING**: the action PLUS what the composed ops ARE
            and WHY (each op's told-description). For a learner, a teaching mode, or when context warrants
            verbose feedback.

        They are separate on purpose; the CHOICE is DYNAMIC — a "super-teaching" Siona, or a shift in the
        user's perspective, sets it (the same terse↔descriptive coherence knob as ``path_emit``, F1075). It is
        fine to smoosh both in testing; keep them distinct in the interface. Returns
        ``[(label, description, [(example, explanation_or_None)])]`` (``explanation`` is ``None`` in plain mode)."""
        out = []
        for lab, desc, _ in self.answer(query, k=k):
            examples = [(e, (self._explain(e) if understand else None)) for e in self.usage.get(lab, [])[:n]]
            out.append((lab, desc, examples))
        return out
