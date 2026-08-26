"""siona.analytic — the ANALYTIC-language describe/explain arc (F1166): sparse relational knowledge → structured
prose, for languages whose structure lives in WORD ORDER + FUNCTION WORDS rather than morphology.

This is the OTHER half of the end goal, and it is a MORPHOLOGICAL-TYPOLOGY split, not an English-vs-Sumerian one:

  * ANALYTIC / ISOLATING languages (English, Mandarin, Vietnamese, …) — little morphology; grammatical role comes
    from WORD ORDER + FUNCTION/particle words. The source is already meaning-bearing tokens, so there is NO
    glyph→concept step — the sparse knowledge IS a co-incidence (relate) graph. THIS module.
  * SYNTHETIC / AGGLUTINATIVE languages (Sumerian, Turkish, Japanese, Swahili, …) — grammatical role is MARKED IN
    THE WORD (case enclitics, verbal-chain infixes, determinatives). That is the Gilgameš arc (`anchor` — `case`,
    `verb_infixes`, `determinative`, `render_cased`).

BOTH types share ONE machinery and differ in exactly one place:
  * SELECTION (which concepts, how grouped) = `couple()`'s residue (F1163/F1164) — carries to an analytic language
    UNCHANGED, because a co-incidence graph IS a coupling graph: build a signed Class-L graph over a topic's
    neighbourhood (relatedness edges +1, ANTONYM pairs −1 as the chirality sign, F1136), and the ONE signed
    eigendecomposition's residue gives the SPINE (key concepts) and the COMMUNITIES (aspect groups).
  * RENDER (structured sentences) DIFFERS by type — the analytic render is ORDER + FUNCTION WORDS (this module's
    gap to grow); the synthetic render is morphology-driven (`render_cased`).

English (the simplewiki `relate` graph) is the FIRST analytic instance; any other analytic language plugs in its
own co-incidence graph the same way. Dense corpora: simplewiki + the MFO notebook (describe / explain /
article-length coherency targets). Sparse, numpy-free, srmech-native (signed Class-L). Aboutness-gated (F768).
"""
from siona import relate, chirality

__all__ = ["residue", "describe", "describe_from", "have_corpus"]

# aboutness stop-set (F768): function + generic-co-incidence words that flood an analytic-language graph but carry
# no topic (in an analytic language these ARE the grammar — order-glue — so they must be filtered from the residue).
_STOP = frozenset((
    "the of a an and to in on at for with by from as is are was were be been being has have had his her its their "
    "this that these those less more means big small large found made make making used use also known part "
    "type types kind number numbers very most many some other such into out over between about after before called "
    "name names first second two one three not no only which who what when where how then than can may will would "
    "it's they them he she we you i").split())


def have_corpus():
    return bool(relate.load())


def residue(topic, *, k=20, edge=0.04, spine_k=5, aspect_max=6):
    """The couple()-style RESIDUE on the analytic-language co-incidence graph for ``topic`` (F1166): build a signed
    Class-L coupling graph over the topic's aboutness-gated neighbourhood (relatedness ≥ ``edge`` as +1 edges;
    ANTONYM pairs as −1 chirality signs, F1136), run ONE ``symmetric_eigendecompose``, and read the SPINE
    (dominant-eigenvector key concepts) and the ASPECTS (low-eigenvector community groups) off it — the SAME
    residue read as `couple()`, sourced from co-incidence instead of morphology. Returns ``{"topic", "spine",
    "aspects"}`` or ``None``. (English `relate` is the default corpus; another analytic language supplies its own.)"""
    from srmech.math import laplacian as L
    nb = [w for w in relate.neighbors(topic) if w not in _STOP and len(w) > 2 and w != topic][:k]
    field = [topic] + nb
    n = len(field)
    if n < 3:
        return None
    edges, weights = [], []
    for a in range(n):                                                       # the analytic coupling graph
        for b in range(a + 1, n):
            if relate.related(field[a], field[b]) > edge:
                edges.append((a, b))
                weights.append(-1.0 if chirality.opposite(field[a], field[b]) else 1.0)   # antonym = chirality sign (F1136)
    if not edges:
        return None
    lap = L.signed_laplacian(n, edges, weights)
    evals, evecs = L.symmetric_eigendecompose(lap)
    evals = [float(x) for x in evals]
    order = sorted(range(n), key=lambda i: evals[i])
    dom = order[-1]                                                          # dominant coupling mode = the spine (residue)
    dom_col = [float(evecs[r][dom]) for r in range(n)]
    spine = [field[i] for i in sorted(range(n), key=lambda i: -(dom_col[i] * dom_col[i]))
             if field[i] != topic][:spine_k]
    nz = [i for i in order if evals[i] > 1e-6][:3]                           # low modes = the aspect communities (residue)
    code = [0] * n
    for bit, kk in enumerate(nz):
        for i in range(n):
            if float(evecs[i][kk]) > 0:
                code[i] |= (1 << bit)
    groups = {}
    for i, w in enumerate(field):
        if w != topic:
            groups.setdefault(code[i], []).append(w)
    aspects = sorted((sorted(g) for g in groups.values() if 2 <= len(g) <= aspect_max), key=lambda g: -len(g))
    return {"topic": topic, "spine": spine, "aspects": aspects}


def _oxford(words):
    """Analytic RENDER glue (F1168): an Oxford-comma English list — the function-word structure ('and', commas)
    that IS the grammar in an analytic language (vs a case suffix). Incremental, not full NLG."""
    ws = list(words)
    if not ws:
        return ""
    if len(ws) == 1:
        return ws[0]
    if len(ws) == 2:
        return "%s and %s" % (ws[0], ws[1])
    return "%s, and %s" % (", ".join(ws[:-1]), ws[-1])


def describe_from(topic, spine, aspects, *, ride=None, source=None):
    """The SHARED analytic SENTENCE render (F1166/F1168), decoupled from the relate-graph SELECTION so ANY selection
    source renders the SAME prose — the relate residue, OR the #231 directed-corpus tome-tree (F1239). The SPINE
    becomes the topic sentence; each ASPECT community a clause (Oxford-comma lists + varied predicates); an optional
    `ride` (a directed etak PATH) becomes a "leads on to" sentence; an optional `source` cite (an ATTESTED genome,
    MPM) is appended. Returns the joined sentences, or ``None`` if there is nothing to say."""
    spine = [w for w in (spine or []) if w and w != topic]
    if not spine and not aspects:
        return None
    out = []
    if spine:
        out.append("%s is closely related to %s." % (topic.capitalize(), _oxford(spine[:5])))
    predicates = ("centres on", "also involves", "connects to")
    for i, a in enumerate([g for g in (aspects or []) if g][:3]):
        out.append("It %s %s." % (predicates[i % len(predicates)], _oxford(list(a)[:4])))
    tail = [w for w in (ride or []) if w and w != topic]
    if tail:
        out.append("Following its strongest links, %s leads on to %s." % (topic, _oxford(tail[:5])))
    if not out:
        return None
    text = " ".join(out)
    return "%s (%s)" % (text, source) if source else text


def describe(topic, **kw):
    """A structured description of ``topic`` from its relational residue (F1166; render improved F1168): the SPINE
    becomes the topic sentence, each ASPECT community a clause, joined with analytic function-word grammar
    (Oxford-comma lists + varied predicates). The SELECTION is `couple()`'s residue on analytic-language data; the
    RENDER is the shared :func:`describe_from`. ``None`` if the topic has no usable neighbourhood."""
    r = residue(topic, **kw)
    if not r:
        return None
    return describe_from(topic, r["spine"], r["aspects"])
