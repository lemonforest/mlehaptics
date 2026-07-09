"""siona.reconstruct — fragment GROUPING + the group→align→majority-correct reconstruction pipeline (F1176/F1177/F1178).

A damaged/fragmentary formulaic line is reconstructed the way antiquity's scribes and modern epigraphers do it: not by
guessing the missing slot, but by GROUPING the fragment with its formula-FAMILY (the parallels that share its frame) and
reading the missing words off the family's CONSENSUS. F1176 measured that the family-grouping is stronger through the
coupling graph's low eigenmodes (spectral neighbours) than through raw content-overlap alone — the same F1172
low-eigenmode↔recurrence identity `couple()` reads, now used to select a line's parallels. F1177 measured that the
consensus is a distance-k repetition code: k=2 DETECTS a divergence, k≥3 CORRECTS it by majority (the op(x)operand(x)EC
triality, F1131) — the "responsion" antiquity already named (strophe↔antistrophe metrical identity, parallelismus
membrorum). This module exposes that as three residue read-outs of ONE Class-L coupling operation, never a re-run:

  * ``group(lines)``            — cluster a set of fragments into their formula-FAMILIES (the signed low-eigenmode
                                  community sign-code, the F1176 grouping strength — the couple.py ``communities``
                                  residue, applied to LINES-as-nodes instead of concepts-as-nodes)
  * ``family(survive, pool)``    — one damaged fragment's family: its surviving words → its k spectrally-nearest
                                  parallels in ``pool`` (F1176's local-coupling-graph finder)
  * ``reconstruct(damaged, pool)`` — the full pipeline: find the family, then majority-correct the missing slots off
                                  the family consensus (F1178; k≥3 corrects, k=2 only detects, F1177)

Every spectral read is ONE ``signed_laplacian`` + ONE ``symmetric_eigendecompose`` (srmech Class-L ONLY — the same
surface `couple()` uses). numpy-free; sparse (edge-lists / dicts, no dense hand-built matrix); no magic weights (Jaccard
overlap is the attested edge); no Python magnitude builtin (nearest-in-embedding uses a squared Class-K distance
``(a−b)·(a−b)``, never that primitive); no Python ``abs`` builtin; no ``Counter`` (a plain-dict tally, deterministically tie-broken).
"""
from srmech.amsc import laplacian as L

__all__ = ["group", "family", "reconstruct"]

# no magic weights: the ONE edge kind is within-fragment content OVERLAP (Jaccard), an attested structural coupling —
# the identical +v co-occurrence edge `couple._build_graph` uses, here between whole LINES instead of concept-words.
_MIN_TOK = 3            # a content token is ≥ 3 chars (drops the function-word chaff — the operator side, not the operand)


def _toks(line):
    """A fragment → its content-word SET (the graph node's signature). Accepts a token set/sequence (used verbatim)
    or a raw string (split on non-letters, lowercased, function-chaff dropped). The WORD-set is what couples two
    fragments, so a shared word is itself an edge — the recurrence the reconstruction rides."""
    if isinstance(line, (set, frozenset)):
        return frozenset(line)
    if isinstance(line, (list, tuple)):
        return frozenset(str(w).lower() for w in line if len(str(w)) >= _MIN_TOK)
    out, cur = [], []
    for ch in str(line).lower():
        if ch.isalpha():
            cur.append(ch)
        elif cur:
            out.append("".join(cur)); cur = []
    if cur:
        out.append("".join(cur))
    return frozenset(w for w in out if len(w) >= _MIN_TOK)


def _jac(a, b):
    """Jaccard overlap — the attested coupling weight (shared-content fraction), never a tuned float."""
    u = len(a | b)
    return len(a & b) / u if u else 0.0


def _low_modes(nodes, m):
    """The shared Class-L residue: build the ONE signed coupling graph over ``nodes`` (Jaccard-overlap edges), run the
    ONE ``symmetric_eigendecompose``, return ``(evecs, low)`` — the ``m`` lowest NONZERO eigenvectors (the community /
    recurrence embedding, F1172). Returns ``(None, None)`` if the graph has no edges (an honest disconnected read)."""
    n = len(nodes)
    edges, weights = [], []
    for a in range(n):
        for b in range(a + 1, n):
            v = _jac(nodes[a], nodes[b])
            if v > 0.0:
                edges.append((a, b)); weights.append(v)
    if not edges:
        return None, None
    evals_vec, evecs = L.symmetric_eigendecompose(L.signed_laplacian(n, edges, weights))
    evals = [float(x) for x in evals_vec]
    low = [k for k in sorted(range(n), key=lambda k: evals[k]) if evals[k] > 1e-6][:m]
    return evecs, (low or None)


def group(lines, *, community_bits=3, min_family=2):
    """Cluster ``lines`` (fragments — token sets or raw strings) into their formula-FAMILIES via the signed Class-L
    low-eigenmode COMMUNITY sign-code (F1176's proven strength: grouping). This is the ``couple()`` ``communities``
    residue with LINES as the graph nodes — one ``symmetric_eigendecompose`` of the line-line coupling graph, a
    sign-code over the ``community_bits`` lowest nonzero eigenvectors, fragments sharing a code = one family.

    ``community_bits`` — how many low eigenvectors form the code (more bits ⇒ finer families). ``min_family`` — a
    family must have ≥ this many members to be reported (singletons are the un-grouped residue → the expert, F282).

    Returns ``{"labels": [code per line], "families": [[line-index, …], …], "singletons": [line-index, …]}`` —
    families sorted largest-first; ``labels`` aligns with ``lines``."""
    sigs = [_toks(x) for x in lines]
    n = len(sigs)
    if n < 3:
        return {"labels": [0] * n, "families": [list(range(n))] if n else [], "singletons": []}

    evecs, low = _low_modes(sigs, community_bits)
    if low is None:                                         # disconnected: every fragment is its own singleton
        return {"labels": list(range(n)), "families": [], "singletons": list(range(n))}

    codes = [0] * n                                        # the signed community sign-code (F1138 pattern, couple.py)
    for bit, k in enumerate(low):
        for i in range(n):
            if float(evecs[i][k]) > 0:
                codes[i] |= (1 << bit)
    buckets = {}
    for i, c in enumerate(codes):
        buckets.setdefault(c, []).append(i)
    families = sorted((g for g in buckets.values() if len(g) >= min_family), key=lambda g: (-len(g), g))
    singletons = sorted(i for g in buckets.values() if len(g) < min_family for i in g)
    return {"labels": codes, "families": families, "singletons": singletons}


def family(survive, pool, *, k=8, neighbourhood=140, m=5):
    """One damaged fragment's formula-FAMILY (F1176's local-coupling finder): from the SURVIVING words ``survive``,
    return the indices in ``pool`` of the ``k`` parallels nearest the fragment in the low-eigenmode embedding of a
    LOCAL coupling graph over {fragment} ∪ {its ``neighbourhood`` raw-overlap candidates}.

    Spectral neighbours (through the graph) pull in formula-family members that raw content-overlap alone under-ranks
    (the F1176 gain). ``neighbourhood`` bounds the local graph; ``m`` = low eigenvectors embedded. Falls back to raw
    overlap if the local graph is empty (honest, not silent)."""
    q = _toks(survive)
    sigs = [_toks(x) for x in pool]
    ranked = sorted(range(len(pool)), key=lambda j: -_jac(q, sigs[j]))[:neighbourhood]
    if not ranked:
        return []
    nodes = [q] + [sigs[j] for j in ranked]               # node 0 = the surviving-half query
    evecs, low = _low_modes(nodes, m)
    if low is None:
        return ranked[:k]
    qe = [float(evecs[0][c]) for c in low]

    def d2(node):                                          # squared Class-K distance in the embedding; no magnitude builtin
        return sum((float(evecs[node][c]) - qe[t]) ** 2 for t, c in enumerate(low))

    near = sorted(range(1, len(nodes)), key=d2)[:k]
    return [ranked[node - 1] for node in near]


def _tally(seqs):
    """Plain-dict word count over a family (never ``Counter`` — deterministic, hash-noise-free per the F1179 fix)."""
    wc = {}
    for s in seqs:
        for w in s:
            wc[w] = wc.get(w, 0) + 1
    return wc


def reconstruct(damaged, pool, *, k=12, frac=0.34):
    """The full group→align→majority-correct pipeline (F1178): find ``damaged``'s formula-family in ``pool`` (spectral,
    F1176), then recover its missing slots from the family CONSENSUS — a word carried by ≥ a threshold fraction of the
    family (the distance-k repetition code, F1177: k≥3 CORRECTS by majority, k=2 only DETECTS).

    ``damaged`` = the surviving words (token set or raw string); ``pool`` = the candidate parallels. ``k`` = family
    size; ``frac`` = consensus fraction (a slot is filled only when ≥ ``max(2, frac·k)`` family members agree — the
    ≥2 floor is the k=2-detect / k≥3-correct boundary made explicit). Returns
    ``{"family": [pool-index, …], "recovered": [word, …], "support": {word: count}}`` — ``recovered`` = the consensus
    words NOT already present in ``damaged`` (the reconstructed slots), ordered by descending family support."""
    survive = _toks(damaged)
    fam = family(survive, pool, k=k)
    if not fam:
        return {"family": [], "recovered": [], "support": {}}
    fam_sigs = [_toks(pool[j]) for j in fam]
    wc = _tally(fam_sigs)
    thr = 2 if int(frac * len(fam)) < 2 else int(frac * len(fam))    # ≥2 floor = the k=2-detect / k≥3-correct boundary
    support = {w: c for w, c in wc.items() if c >= thr and w not in survive}
    recovered = sorted(support, key=lambda w: (-support[w], w))      # descending support, tie-broken deterministically
    return {"family": fam, "recovered": recovered, "support": support}
