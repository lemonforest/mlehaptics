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

__all__ = ["introspect_srmech", "introspect_carriers", "introspect_patterns", "introspect_carrier_examples",
           "PATTERNS", "Tooling", "SRMECH_MODULES", "TIERS"]

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
    # The qm / QFT / Standard-Model physics layer (F1204): srmech's _REGISTRY (409 ops) has these, but Siona's
    # introspection omitted them — she couldn't answer "how do I compute the weak mixing angle" because her
    # self-knowledge never mined srmech.qm.*. The Standard Model (qm.sm) was INVISIBLE to her. Now included.
    "srmech.qm.single_particle", "srmech.qm.spin", "srmech.qm.potentials", "srmech.qm.relativistic",
    "srmech.qm.propagators", "srmech.qm.pseudo_hermitian", "srmech.qm.gauge", "srmech.qm.sm",
    "srmech.qm.so8", "srmech.qm.triality",
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


def introspect_carriers():
    """``{carrier_name: description}`` for every CARRIER TYPE — the NOUNS of the composition graph (F1110).
    ``introspect_srmech`` SKIPS these: it filters upper-case class names, and the carriers (``Poly`` / ``BiPoly``
    / ``TriPoly`` …) ARE classes — so Siona knew her ops (verbs) but NOT her types (nouns). Synthesised from
    ``carrier_ladder_descriptor`` (F1038) so Siona KNOWS her carriers: name + variable-count + ladder/rung.
    HONEST caveat (F1110): grounding separates the DISTINCT types (Mat / float / octonion) but not the
    variable-COUNT (Poly vs BiPoly vs TriPoly differ only by a rung NUMBER surface-word grounding can't weight —
    the structure-not-surface lesson of F1100); the number-sensitive typing lives in ``goal_typing`` (the cue)."""
    import srmech.amsc.carrier_ladder as _cl
    d = _cl.carrier_ladder_descriptor()
    out = {}
    for nm, c in d["carriers"].items():
        lad = d["ladders"].get(c.get("ladder"), {})
        n = c.get("rung") or 0
        vs = [v for v in (lad.get("adds_variable", {}).get(str(i)) for i in range(1, n + 1)) if v]
        q = "q-analog " if str(c.get("ladder", "")).endswith("_q") else ""
        out[nm] = "%s: a %s%d-variable polynomial (rung %s of the %s ladder%s)" % (
            nm, q, n, c.get("rung"), c.get("ladder"), ("; variables " + " ".join(vs)) if vs else "")
    out.setdefault("cayley_dickson:8", "octonion: an 8-dimensional hypercomplex number (Cayley-Dickson rung 8)")
    out.setdefault("float", "float: a scalar number — a magnitude, norm, or single value")
    out.setdefault("Mat", "Mat: a matrix")
    return out


# The PATTERNS / DISCIPLINE tier (F1207 fix #2) — architecture rules that are NOT srmech ops, so
# introspect_srmech (which mines op signatures + docstrings) is STRUCTURALLY BLIND to them. Adding this tier is
# why "how do I encode a corpus as a class-l genome" can now surface the correct PATTERN (uncapped-weighted, no
# storage truncation) instead of just the pieces (dense_laplacian). Each value is a full how-to so grounding AND
# display both work. Prevents recurrence #3 of the top-K-truncation trash-fallback (F708/F748/F1207).
PATTERNS = {
    "build_wiki_corpus_genome": (
        "build a wiki/corpus DIRECTED Class-L genome (the #231 store) — the NATIVE srmech rc253 pipeline, the way "
        "the simplewiki body instrument was made (F1232/F1233): (1) tokenize each doc with srmech.amsc.text.tokenize; "
        "(2) n,edges,metric,charge = srmech.amsc.text.cooccurrence_edges(docs, window=4, vocab=V, directed=True) — "
        "metric=w_fwd+w_bwd, charge=w_fwd-w_bwd (the direction); (3) strand,n_syms = srmech.amsc.genome.graph_to_kernel"
        "(n, edges, metric, charge, leaf_dim=64, label='graph', the_one=COUPLE); genome_save(strand,dir,COUPLE,"
        "labels=['graph']) then genome_append_kernel(dir,'vocab', vocab-as-klein4-syms) = ONE content-addressed genome "
        "(graph + vocab chromosomes), NOT loose JSON; (4) verify with srmech.amsc.laplacian.recover_check_structural "
        "(sparse, any vocab) + recover_check_spectral(max_dim=256). Store the directed Laplacian + fiber, NEVER Klein-4 "
        "HVs (F1221). Load for reads via siona.corpus_store.prepare(dir) -> neighbors('X') = 'what is X seen-with'. "
        "(5) for FAST serving, build the DEMAND-LOAD read layer once: siona.corpus_store.build_reads(dir) writes "
        "reads/ (a mmap'd per-token index) so the server opens INSTANTLY and each query gene-EXPRESSES only its token's "
        "neighbourhood (EPH / F1095/F1112/F1235) instead of inflating all edges into RAM. Read via corpus_store."
        "prepare(dir) -> read(handle,'X'). Reference: R-RBS-LM-SIONA231 (store) + R-RBS-LM-SIMPLEWIKIGENOME (831k vocab/"
        "39M edges -> 313MB, 3x < loose) + R-RBS-LM-BUILDREADS (the reads/ layer). To build ANOTHER wiki (enwiki, other "
        "lang): run the SAME pipeline on that wiki's directed cooccurrence."),
    "encode_corpus_class_l_genome": (
        "encode a corpus as a Class-L genome. PREFER 'build_wiki_corpus_genome' — the native rc253 directed genome "
        "(graph_to_kernel + a vocab chromosome; F1232). The older loose form (build_edges_topk vocab_cap=None -> a "
        "full_sparse_kernel {vocab,freq,edge_list,edge_weights} JSON; R-RBS-LM-WIKIWEIGHTED) is SUPERSEDED but the "
        "DISCIPLINE stands: NEVER top-K or drop weights at STORAGE time (the trash-fallback F708/F748/F1207); top-N is "
        "a LOAD-time knob. The stored object recovers op (L=D-A), operand (edges), responsion (excite L) — recover_check guards it."),
    "store_sparse_complete_never_truncate": (
        "store SPARSE-and-COMPLETE: keep EVERY real weighted edge as an int edge-list (no dense float matrix). "
        "'sparse' means sparse vs gen-1 dense-float-in-GPU-RAM, NOT fewer edges. top-K is a query READ, never a "
        "storage cut. A top-16 unweighted store keeps a lossy relational read-out and DESTROYS the distributional "
        "(eigenvectors) and the responsion (eigenvalues) — it amputates two of the object's three faculties."),
    "one_class_l_object_three_readouts": (
        "ONE sparse weighted Class-L object L=D-A (spectrum lambda,v) gives THREE read-outs: edges -> RELATIONAL "
        "(direct 'what is X seen with' lookup, no eig); eigenvectors -> DISTRIBUTIONAL (the dense embedding, "
        "DERIVED not stored — what gen-1 stores as its whole massive object); eigenvalues -> RESPONSION / EPH "
        "(propagator e^{-zL}, resolvent (zI-L)^-1). F1067/F1132/F1186/F172."),
}


def introspect_patterns():
    """PATTERNS/DISCIPLINE self-knowledge (F1207 fix #2) — ``{pattern.<key>: how-to}``. NOT srmech ops, so
    ``introspect_srmech`` misses them; this is the tier that lets an encode/architecture query self-route to the
    correct PATTERN rather than the bare pieces. Genome-safe ``pattern.`` prefix (like ``carrier.``)."""
    return {"pattern." + k: v for k, v in PATTERNS.items()}


def introspect_carrier_examples():
    """CARRIER CONSTRUCTION-example self-knowledge (rc241 #839 / F1221) — ``{carrier_example.<name>: how-to-build}``
    mined from srmech's attested ``_carrier_examples.CARRIER_EXAMPLES`` (the carrier-side peer of the op
    docstrings). ``introspect_carriers`` gives the carrier NOUN (what a Mat / BiPoly IS, the type); THIS gives the
    CONSTRUCTOR (how to BUILD one) — the knowing-HOW for the types, the peer of ``mine_usage``'s knowing-HOW for
    the ops (F1086/F1110). Attested (sha256) upstream, so it composes with the AMSC/MPM discipline. Import-guarded:
    no-ops on an srmech without the layer (pre-rc241), like ``introspect_carriers`` guards its own import."""
    try:
        from srmech.amsc._carrier_examples import CARRIER_EXAMPLES
    except Exception:
        return {}                                                   # pre-rc241 srmech: the layer isn't there yet
    out = {}
    for nm, ex in CARRIER_EXAMPLES.items():
        if isinstance(ex, dict):
            desc = "construct a %s: %s  ->  yields %s" % (nm, ex.get("construct", ""), ex.get("yields", ""))
        else:
            desc = "construct a %s: %s" % (nm, ex)
        out["carrier_example." + nm.replace(":", "_")] = desc       # genome-safe prefix, ``:``-sanitised
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


def _default_cache_path():
    """Default on-disk cache for the knowledge genome (F1111/#256) — persists across runs under the user cache
    dir (``$XDG_CACHE_HOME`` or ``~/.cache``), version-keyed so a srmech upgrade rebuilds it."""
    import os
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "siona", "knowledge_genome")


class Tooling:
    """Siona's self-knowledge of her tooling — BOTH tiers (F1084/F1086): learning by being TOLD (op
    signature/docstring, ``answer``) AND learning by IMITATION (real usage examples, ``how_to``). Told is the
    index; imitation is the runnable. Both built from the LIVE package/source, so neither lags the format."""

    def __init__(self, grounder, modules=None, *, mine=True, source_dirs=None, cache=True, cache_path=None):
        self._g = grounder
        self.kb = introspect_srmech(modules)                        # TOLD descriptions (fast; for display + fallback)
        self.kb.update(introspect_patterns())                       # F1207 fix #2: the patterns/discipline tier joins the grounded self-knowledge
        self.kb.update(introspect_carrier_examples())               # rc241 #839/F1221: carrier CONSTRUCTION examples (how to BUILD a carrier, not just what it IS)
        self.labels = list(self.kb)
        self.carriers = introspect_carriers()                       # NOUNS: carrier TYPES (F1110)
        self._clabels = list(self.carriers)
        kg = {}
        if cache:                                                   # F1111/#256: LOAD the cached knowledge genome
            try:                                                    # (the expensive enc_query happens once, then recall)
                from . import knowledge_genome as _kgmod
                kg = _kgmod.load_or_build(grounder, cache_path or _default_cache_path(), modules=modules)
            except Exception:
                kg = {}                                             # any cache issue → encode live (robust)
        self._vecs = [kg.get(l) or list(grounder.enc_query(self.kb[l])) for l in self.labels]
        self._cvecs = [kg.get("carrier." + c.replace(":", "_")) or list(grounder.enc_query(self.carriers[c]))
                       for c in self._clabels]
        self.usage = mine_usage(self.labels, source_dirs) if mine else {}   # IMITATION: {label: [examples]}

    def answer(self, query, k=3, *, route=True, k_modules=3):
        """TOLD tier: ground a tooling question to the k nearest ops → ``[(label, description, similarity)]``.

        With ``route=True`` (F1113/#256): ROUTE the query to its module(s) and EXPRESS + ground WITHIN that
        subset — don't compare against all 256 (the demand-load, F1112). Falls back to the FULL set if the route
        finds nothing (honest — never miss because a keyword route came up empty)."""
        qv = self._g.enc_query(query)
        idxs = range(len(self.labels))
        if route:
            from .knowledge_genome import _route_modules              # lazy (avoid the introspect↔kg import cycle)
            mods = set(_route_modules(query, k_modules))
            hit = [i for i, l in enumerate(self.labels) if l.split(".")[0] in mods]   # EXPRESS the module subset
            if hit:
                idxs = hit                                           # ...and ground WITHIN it
        scored = sorted(((_hdc.klein4_similarity(qv, self._vecs[i]).as_float(), self.labels[i]) for i in idxs),
                        reverse=True)
        if route and "pattern" in mods:                             # F1207 fix #2: the router judged this an
            # architecture question (the PATTERN tier routed) -> LEAD with the pattern; a bare op must not outrank
            # the discipline (klein4 surface-grounding otherwise ties a pattern below a same-topic op, F1100).
            scored.sort(key=lambda sl: (not sl[1].startswith("pattern."), -sl[0]))
        return [(l, self.kb[l], round(s, 3)) for s, l in scored[:k]]

    def carrier(self, query, k=2):
        """Ground a goal to Siona's KNOWN carrier TYPES (F1110) — she knows her NOUNS now, not just her ops.
        STOPGAP consuming ``carrier_ladder_descriptor``: coarse types (Mat / float / octonion) ground; the
        variable-COUNT (Poly / BiPoly / TriPoly) does NOT (they differ only by a rung number the thin srmech
        descriptions can't discriminate — UPSTREAM ask §91). The number-sensitive typing lives in ``goal_typing``."""
        qv = self._g.enc_query(query)
        scored = sorted(((_hdc.klein4_similarity(qv, v).as_float(), l)
                         for l, v in zip(self._clabels, self._cvecs)), reverse=True)
        return [(l, round(s, 3)) for s, l in scored[:k]]

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
