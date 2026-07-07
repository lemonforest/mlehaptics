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

# The REFINED shape (F1163): NO tuned weights and NO operand→verb "hub" edge. The earlier `couple.py` wired every
# operand to the verb-NODE (a case→verb edge), which made the verb a super-hub that over-connected the graph and
# FORCED a hand-tuned down-weight to stay legible. But the verb is the OPERATOR — a RELATION, not an operand-node;
# treating it as a node was the wrong SHAPE, and the tuning was the un-collapsed manual step (F1161/F1162). The
# refined shape has two STRUCTURAL (attested, class-A) edge kinds only, no floats to dial:
#   * within-phrase CO-OCCURRENCE (+1) among all concept-words — verbs STAY nodes so their recurring concepts reach
#     the spine; recurrence accumulates as repeated edges (the F1160 weight);
#   * the operand's CASE ROLE as a SIGNED CHIRALITY edge (F1138) between the operands the verb couples: complementary
#     roles (from vs to = source vs goal) REPEL (−1), same-role ATTRACT (+1). The role is a SIGN (structure), never a
#     weight — so the partition falls out of the SIGNED Laplacian for FREE, at spine 7/8 with zero tuning (F1161).
# MEASURED: this shape gives spine 7/8 (vs the tuned floats' 7/8, but with NO magic numbers, and vs the case-hub
# attested-int 5/8). The community "blob" is honest structure — the recurring-formula hub-concepts (be/place/go) are
# the F256 ANCHOR backbone, simultaneously the spine AND the connectors; it is not tuning-away-able, and the earlier
# down-weight that shrank it was observer-fitting.
_COOCCUR = 1                    # within-phrase co-occurrence, +1 (recurrence accumulates as repeated edges, F1160)


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
    """The ONE coupling graph — the F1163 REFINED shape (NO tuned weights, NO verb-hub edge). Nodes = concept-words
    (verbs stay nodes so their recurring concepts reach the spine). Two structural edge kinds: (A) within-phrase
    CO-OCCURRENCE (+1, recurrence accumulates as repeated edges); (B) the operand CASE ROLE as a SIGNED CHIRALITY
    edge (F1138) between the operands a verb couples — complementary roles (from vs to) REPEL (−1), same-role
    ATTRACT (+1). The verb is the OPERATOR/relation, so it is NOT wired as a hub; the role is a SIGN, not a weight.
    Returns ``(vocab, edges, weights, coupling_edges)`` — signed weights; ``coupling_edges`` keeps the op(x)operand
    (operand, verb, role, status) annotation visible (F1159)."""
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
            uniq = list(dict.fromkeys(w for _, _, ws in words_by_glyph for w in ws))
            ids = [node(w) for w in uniq]
            for i in range(len(ids)):                                  # (A) within-phrase CO-OCCURRENCE (+1)
                for j in range(i + 1, len(ids)):
                    a, b = ids[i], ids[j]
                    edges.append((a, b) if a < b else (b, a))
                    weights.append(_COOCCUR)

            verb = next(((g, ws) for g, c, ws in words_by_glyph if c.startswith("to ")), None)
            infix_roles = anchor.verb_infixes(verb[0]) if verb else set()
            roled = [(ws, anchor.case(g)) for g, c, ws in words_by_glyph      # the OPERANDS carrying a case role
                     if not c.startswith("to ") and anchor.case(g)]
            for i in range(len(roled)):                                # (B) case ROLE as a SIGNED chirality edge (F1138)
                ws_i, r_i = roled[i]
                for j in range(i + 1, len(roled)):
                    ws_j, r_j = roled[j]
                    sign = -1 if r_i != r_j else 1                      # complementary roles repel, same-role attract
                    for w1 in ws_i:
                        for w2 in ws_j:
                            if w1 == w2:
                                continue
                            a, b = node(w1), node(w2)
                            edges.append((a, b) if a < b else (b, a))
                            weights.append(sign)
            if verb:                                                   # keep the op(x)operand coupling ANNOTATION (F1159)
                vw = verb[1][0] if verb[1] else "?"
                for ws_i, r_i in roled:
                    status = "confirmed" if r_i in {anchor._ROLE.get(x, x) for x in infix_roles} or \
                        anchor._ROLE.get(r_i, r_i) in infix_roles else "case_only"
                    coupling_edges.append((ws_i[0] if ws_i else "?", vw, r_i, status))

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

    lap = L.signed_laplacian(n, edges, weights)         # THE one coupling matrix (SIGNED: the case-role is a ± sign, F1163)
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
