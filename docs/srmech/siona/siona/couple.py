"""siona.couple — the pipeline-COLLAPSE: ONE Class-L coupling operation whose RESIDUE reproduces the separate
transcription steps (F1161: "emergence = the residue of the refined formula" — an "emergent" item is not extra
magic, it is what a LINEAR observer calls the read-out of one operation's residue, once the math is in its
correct shape).

Before this module, `anchor.py` ran a chain of SEPARATE steps over a Sumerian glyph line: `transcribe` (glyph ->
concept), `case` (the operand's op(x)operand coupling role), `verb_infixes` (the verb's operator-side re-encoding
of that same role), `coupling_ec` (case<->infix redundancy check), `express_story` (the recurring-concept SPINE
as a render read-out), and the of-cycle formula-repetition count (F1160). F1161 DEMONSTRATED that two of these —
the render spine (F1148) and the of-cycle EC formulae (F1160) — are the SAME residue: the dominant eigenvector of
ONE `symmetric_eigendecompose` of the glyph-coupling graph (167 concept-words) reproduced BOTH at once (8/8
top-spine words were in the recurring formulae). `couple()` is the constructive follow-through F1161 called for:
build that ONE coupling graph — nodes = concept words, edges = within-phrase co-occurrence PLUS the case/infix
coupling roles (so the graph carries the op(x)operand structure, not bare co-occurrence) — run ONE
`symmetric_eigendecompose`, and read every prior "step" off its residue:

  * ``coherence``    — λ₂ (algebraic connectivity) = the phase-locking of the WHOLE coupling
  * ``spine``         — the dominant eigenvector's largest-magnitude words = the recurring-concept spine
                        (F1148's render read-out, now a residue, not a step)
  * ``communities`` / ``formulae`` — a Class-L signed-partition sign-code (F1138 pattern) over several low
                        nonzero eigenvectors = the strong-community word-groups = the recurring FORMULAE (F1160's
                        of-cycle EC, now a residue, not a manual repeat-count)
  * ``render_order``  — the Fiedler vector's total order over the vocabulary = a residue-derived render sequence
  * ``coupling_edges``— the case/infix role that DERIVED each op(x)operand edge, kept as edge annotations so the
                        coupling structure stays visible in the one object (not hidden inside the matrix)

Every field above comes from the SAME ``(evals, evecs)`` pair — one `dense_laplacian` + one
`symmetric_eigendecompose`, never a second decomposition. srmech-native (`srmech.amsc.laplacian` ONLY), numpy-free,
sparse (edge-lists / dicts, no dense hand-built matrix — `dense_laplacian` builds its matrix internally). No
Python's magnitude builtin: eigenvector ranking uses ``x*x`` as a Class-K sort key, never that primitive.
"""
from siona import anchor

__all__ = ["couple"]

# Edge weight = the ATTESTATION COUNT of the coupling (F1159), NOT a tuned float — a coupling stated N times weighs
# N (no-magic-numbers: the weight is attested to structure, class A). A within-phrase co-occurrence attests the
# pair ONCE; the operand's CASE attests its role ONCE; a CONFIRMED coupling (case AND the verb's infix both state
# it — the F1159 "stated twice") attests TWICE. Honest note: these attested integers reproduce the F1161 spine at
# ~5/8 vs ~7/8 for an earlier hand-TUNED float set — the extra cleanliness of the tuned floats was observer-fitting,
# and that 5/8-vs-7/8 gap is honest evidence this coupling-graph is a good FIRST collapse, not yet the fully-refined
# shape (in the refined shape the clean partition would fall out of the attested weights for free, F1161).
_COOCCUR_WEIGHT = 1             # one within-phrase co-occurrence = attested once (repeats accumulate as more edges)
_CASE_WEIGHT_ONLY = 1          # the case states the operand's role once = attested once
_CASE_WEIGHT_CONFIRMED = 2     # case AND verb-infix both state it (F1159 "stated twice") = attested twice


def _tokwords(concept):
    """A concept gloss -> its constituent words (F1153's `g4_motif` tokenization: strip the verb's "to ",
    split, lowercase) — the WORD is the graph node, not the whole concept phrase, so a shared word (e.g. two
    concepts both containing "place") is itself a coupling."""
    return [w for w in concept.replace("to ", "").lower().split() if w]


def _glyph_phrase_cycles(raw_line, concepts_row):
    """Like `anchor._phrase_cycles`, but keeps each concept's SOURCE glyph paired with it (raw glyph, concept)
    per phrase-cycle — the pairing `case`/`verb_infixes` need, which the concept-only split discards. A verb
    ("to X") closes a cycle (Sumerian is verb-final); a trailing operand-only tail is its own (verbless) cycle."""
    cycles, cur = [], []
    for g, c in zip(raw_line, concepts_row):
        if not c:
            continue
        cur.append((g, c))
        if c.startswith("to "):
            cycles.append(cur)
            cur = []
    if cur:
        cycles.append(cur)
    return cycles


def _build_graph(raw_glyph_lines):
    """The ONE coupling graph: nodes = concept-words (index-assigned on first sight), edges = within-phrase
    co-occurrence (repeat-weighted by recurrence) PLUS case/infix op(x)operand coupling (light-weighted, so it
    ENRICHES rather than overwhelms the co-occurrence signal). Returns ``(vocab, edges, weights, coupling_edges)``
    — ``coupling_edges`` is the edge-ANNOTATION list (operand_word, verb_word, role, status), the op(x)operand
    coupling kept visible alongside the numeric graph that carries it."""
    vocab, idx = [], {}

    def node(w):
        i = idx.get(w)
        if i is None:
            i = idx[w] = len(vocab)
            vocab.append(w)
        return i

    edges, weights, coupling_edges = [], [], []

    for raw_line in raw_glyph_lines:
        concepts_row = anchor.transcribe([raw_line])[0]                # per-glyph concept-or-None, aligned
        for cycle in _glyph_phrase_cycles(raw_line, concepts_row):
            words_by_glyph = [(g, c, _tokwords(c)) for g, c in cycle]
            flat = [w for _, _, ws in words_by_glyph for w in ws]
            uniq = list(dict.fromkeys(flat))
            ids = [node(w) for w in uniq]
            for i in range(len(ids)):                                  # (A) within-phrase co-occurrence
                for j in range(i + 1, len(ids)):
                    a, b = ids[i], ids[j]
                    edges.append((a, b) if a < b else (b, a))
                    weights.append(_COOCCUR_WEIGHT)

            verb = next(((g, ws) for g, c, ws in words_by_glyph if c.startswith("to ")), None)
            if verb is None:
                continue
            verb_glyph, verb_words = verb
            infix_roles = anchor.verb_infixes(verb_glyph)               # the OPERATOR-side re-encoded roles
            for g, c, ws in words_by_glyph:                             # (B) case/infix op(x)operand coupling
                if c.startswith("to "):
                    continue
                role = anchor.case(g)                                   # the OPERAND-side coupling role
                if not role:
                    continue
                confirmed = role in infix_roles                         # case<->infix redundancy (coupling_ec)
                w_edge = _CASE_WEIGHT_CONFIRMED if confirmed else _CASE_WEIGHT_ONLY
                status = "confirmed" if confirmed else "case_only"
                for ow in ws:
                    for vw in verb_words:
                        if ow == vw:
                            continue
                        a, b = node(ow), node(vw)
                        edges.append((a, b) if a < b else (b, a))
                        weights.append(w_edge)
                        coupling_edges.append((ow, vw, role, status))

    return vocab, edges, weights, coupling_edges


def couple(raw_glyph_lines, *, community_bits=4, top_k=8, max_formula_size=12):
    """THE pipeline-collapse (F1161): ONE Class-L coupling-graph eigendecomposition over ``raw_glyph_lines``
    (markup-intact raw glyphs, per line), whose residue IS every field below — never a separate re-run.

    ``community_bits`` — how many low nonzero eigenvectors form the community sign-code (more bits = finer
    partition). ``top_k`` — spine length. ``max_formula_size`` — the recurring-formula groups are capped here
    (bigger groups are the general vocabulary bulk, not a tight formula).

    Returns a dict:
      ``n``              — vocabulary size (graph node count)
      ``coherence``       — λ₂, the algebraic connectivity (phase-locking of the WHOLE coupling; 0.0 if the
                             text's concept-graph is disconnected — an honest read, not a failure)
      ``components``      — count of ~zero eigenvalues = disconnected islands (F1133's graft-scan vocabulary)
      ``spine``            — the dominant (largest-eigenvalue) eigenvector's top-``top_k`` words by magnitude
      ``communities``      — {sign-code: [words]}, the full low-eigenvector partition
      ``formulae``         — the tight (2..``max_formula_size``-member) community groups, excluding the single
                             largest (general-vocabulary) group — the recurring Gilgameš FORMULAE (F1160)
      ``render_order``     — all vocabulary words ordered by the Fiedler vector (smallest-nonzero-eigenvalue
                             eigenvector) — a residue-derived render sequence
      ``coupling_edges``   — [(operand_word, verb_word, role, "confirmed"|"case_only")], the op(x)operand
                             coupling that DERIVED part of the graph, kept visible as edge annotations
      ``evals``            — the raw eigenvalues (ascending), for anyone who wants a further residue read-out
    """
    from srmech.amsc import laplacian as L

    vocab, edges, weights, coupling_edges = _build_graph(raw_glyph_lines)
    n = len(vocab)
    if n < 2:
        return {"n": n, "coherence": 0.0, "components": n, "spine": list(vocab), "communities": {},
                "formulae": [], "render_order": list(vocab), "coupling_edges": coupling_edges, "evals": []}

    lap = L.dense_laplacian(n, edges, weights)          # THE one coupling matrix
    evals_vec, evecs = L.symmetric_eigendecompose(lap)  # THE one eigendecomposition — everything below reads it
    evals = [float(x) for x in evals_vec]
    order = sorted(range(n), key=lambda i: evals[i])    # ascending eigenvalue order (one sort, reused throughout)

    # -- coherence: λ2, the second-smallest eigenvalue (algebraic connectivity) --
    coherence = evals[order[1]] if n > 1 else 0.0
    components = sum(1 for e in evals if e <= 1e-9)     # near-zero multiplicity = disconnected islands

    # -- spine: the dominant (largest-eigenvalue) eigenvector's biggest-magnitude words --
    dom = order[-1]
    dom_col = [float(evecs[r][dom]) for r in range(n)]
    spine_idx = sorted(range(n), key=lambda i: -(dom_col[i] * dom_col[i]))[:top_k]   # Class-K x*x, no magnitude builtin
    spine = [vocab[i] for i in spine_idx]

    # -- communities / formulae: a multi-bit sign-code over the lowest nonzero eigenvectors --
    nonzero = [i for i in order if evals[i] > 1e-6]
    bit_idx = nonzero[:community_bits]
    codes = [0] * n
    for bit, k in enumerate(bit_idx):
        for i in range(n):
            if float(evecs[i][k]) > 0:
                codes[i] |= (1 << bit)
    communities = {}
    for i, w in enumerate(vocab):
        communities.setdefault(codes[i], []).append(w)
    for grp in communities.values():
        grp.sort()
    majority = max(communities, key=lambda c: len(communities[c])) if communities else None
    formulae = sorted((ws for code, ws in communities.items()
                        if code != majority and 2 <= len(ws) <= max_formula_size),
                       key=lambda ws: (-len(ws), ws))

    # -- render_order: the Fiedler vector (smallest-nonzero eigenvalue eigenvector) total order --
    fiedler_k = nonzero[0] if nonzero else order[0]
    fied_col = [float(evecs[r][fiedler_k]) for r in range(n)]
    render_order = [vocab[i] for i in sorted(range(n), key=lambda i: fied_col[i])]

    return {
        "n": n, "coherence": coherence, "components": components,
        "spine": spine, "communities": communities, "formulae": formulae,
        "render_order": render_order, "coupling_edges": coupling_edges, "evals": evals,
    }
