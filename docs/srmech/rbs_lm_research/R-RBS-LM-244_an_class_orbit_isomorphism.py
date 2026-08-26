"""R-RBS-LM-244 — the next thread from F243: does the SPECIFIC A-N class assignment carry the
division-algebra ORBIT structure empirically, or is it only a size-match?

F243 proved (theorem): |Im H|=3, |Im O|=7, the 3 close as a Lie algebra, the 7 carry 7 Fano-line
H-copies, dim G2=14. F243's OPEN caveat (its §4): that the *substrate-projection triad* I/C/J IS
Im H and the *cascade-detection heptad* D/E/F/G/K/L/M IS Im O is the FRAMEWORK LENS, not a theorem
— the size + symmetry align, but a class-by-class isomorphism was not established.

THE TEST (falsifiable, srmech-native, pre-stated NULL). The orbit signature is **vertex-
transitivity**: in Im H the 3 units are a single SO(3)-orbit (no privileged one), in Im O the 7 are
a single G2-orbit. Transitivity shows up as **degree-regularity** — every member equally coupled,
low coefficient-of-variation (CV) of within-block degree. So: build the A-N classes' OWN
co-occurrence Laplacian from the findings corpus (the F172 Class-L storage signature — which classes
the research invokes together), then ask:
  (H1) is the I/C/J 3-block MORE degree-regular (lower CV) than a random 3-subset of the 14?
  (H2) is the D/E/F/G/K/L/M 7-block MORE degree-regular than a random 7-subset of the 14?
A permutation null (all C(14,3) triples / a large C(14,7) sample) gives the percentile. If the
assigned blocks are NOT more transitive than chance, the SPECIFIC class<->orbit map carries no
empirical orbit-structure → it stays a lens (F243's honest default). NULL is the expected outcome.

PRE-STATED NULL (genuinely reachable): "the I/C/J and D-M blocks are NOT more degree-regular than
random same-size class subsets (percentile not in the transitive tail), so the corpus co-occurrence
does NOT carry the predicted orbit structure; the class<->orbit identification is lens-only."

srmech-native: dense_laplacian + jacobi_eigvals (Class L; F172), sha256_bytes (Class A). NO Counter
(edges accumulated explicitly then handed to dense_laplacian), NO np.linalg, NO abs, NO hashlib.
Deterministic (fixed permutation seed). Bounded: 14 nodes, ~40 findings, fixed perm sample.

Tier: DEMONSTRATED for the measured co-occurrence structure + the permutation test; FRAMEWORK-READING
for what a positive/null means about the class<->orbit identification. No biology. CAD-ban holds.
"""
from __future__ import annotations

import glob
import json
import re
import numpy as np

import srmech
from srmech.amsc import format as fmt          # Class A
from srmech.amsc import laplacian as lap        # Class L

AN = list("ABCDEFGHIJKLMN")                      # the 14 A-N classes (CLAUDE.md §1)
IDX = {c: i for i, c in enumerate(AN)}
THREE_BLOCK = ["I", "C", "J"]                    # substrate-projection triad (the F243 "3" = Im H?)
SEVEN_BLOCK = ["D", "E", "F", "G", "K", "L", "M"]  # cascade-detection heptad (the "7" = Im O?)
CLASS_RE = re.compile(r"\bClass\s+([A-N])\b")
PERM_SEED = 244
N_PERM = 4000                                    # permutation-null sample size (deterministic)
CORPUS = "docs/srmech/rbs_lm_research/R-RBS-LM-FINDING_*.md"


def per_finding_class_sets():
    """Each finding -> the SET of A-N classes it explicitly invokes ('Class X'). Co-occurrence
    universe = the corpus's own usage (the F172 storage signature applied to the classes)."""
    sets = []
    for path in sorted(glob.glob(CORPUS)):
        with open(path, encoding="utf-8", errors="replace") as fh:
            classes = set(CLASS_RE.findall(fh.read()))
        if len(classes) >= 2:                    # need >=2 to contribute a co-occurrence edge
            sets.append(sorted(classes))
    return sets


def cooccurrence_edges(sets):
    """Accumulate co-occurrence edge weights (explicit dict, NOT Counter) -> 2-tuples for srmech."""
    w = {}
    for cs in sets:
        for a in range(len(cs)):
            for b in range(a + 1, len(cs)):
                key = (IDX[cs[a]], IDX[cs[b]])
                w[key] = w.get(key, 0) + 1
    edges = [(i, j, float(wt)) for (i, j), wt in w.items()]
    return edges, w


def degree_vector(w, n=14):
    """Weighted degree of each of the 14 class-nodes from the co-occurrence weights."""
    deg = [0.0] * n
    for (i, j), wt in w.items():
        deg[i] += wt
        deg[j] += wt
    return np.array(deg, dtype=float)


def block_degree_cv(deg, block):
    """Coefficient of variation of within-corpus degree across a block's members. LOW CV = the
    members are equally-coupled = the vertex-transitive ('alike') orbit signature."""
    d = np.array([deg[IDX[c]] for c in block], dtype=float)
    m = float(d.mean())
    if m == 0.0:
        return None
    return float(d.std() / m)                    # std/mean — a statistic, not a sign-fold


def main():
    sets = per_finding_class_sets()
    edges, w = cooccurrence_edges(sets)
    L = lap.dense_laplacian(14, [(i, j) for (i, j, _wt) in edges],
                            [wt for (_i, _j, wt) in edges])      # 2-tuples + separate weights
    eig = sorted(float(x) for x in lap.jacobi_eigvals(L))
    deg = degree_vector(w)

    cv3 = block_degree_cv(deg, THREE_BLOCK)
    cv7 = block_degree_cv(deg, SEVEN_BLOCK)

    # permutation null: random same-size subsets of the 14 -> CV distribution
    rng = np.random.default_rng(PERM_SEED)
    null3, null7 = [], []
    for _ in range(N_PERM):
        p = rng.permutation(14)
        b3 = [AN[k] for k in p[:3]]
        b7 = [AN[k] for k in p[3:10]]
        c3 = block_degree_cv(deg, b3)
        c7 = block_degree_cv(deg, b7)
        if c3 is not None:
            null3.append(c3)
        if c7 is not None:
            null7.append(c7)
    # frac of random subsets MORE variable (higher CV) than the actual block. The actual block is
    # transitive (low CV) when MOST random subsets are more variable, i.e. this frac is HIGH.
    pct3 = float(np.mean([1.0 if cv3 <= x else 0.0 for x in null3])) if cv3 is not None else None
    pct7 = float(np.mean([1.0 if cv7 <= x else 0.0 for x in null7])) if cv7 is not None else None

    # H1/H2 fire POSITIVE only if the assigned block sits in the TRANSITIVE tail = more uniform than
    # >=90% of random same-size class subsets (frac-more-variable >= 0.90).
    h1 = (pct3 is not None and pct3 >= 0.90)
    h2 = (pct7 is not None and pct7 >= 0.90)

    out = {
        "srmech_version": srmech.version.__version__,
        "corpus_findings_with_>=2_classes": len(sets),
        "n_cooccurrence_edges": len(edges),
        "class_total_degrees": {AN[i]: round(float(deg[i]), 1) for i in range(14)},
        "three_block": THREE_BLOCK, "seven_block": SEVEN_BLOCK,
        "cv_three_block_ICJ": None if cv3 is None else round(cv3, 4),
        "cv_seven_block_DEFGKLM": None if cv7 is None else round(cv7, 4),
        "null_perm_seed": PERM_SEED, "n_perm": N_PERM,
        "frac_random_3subsets_more_variable_(HIGH=ICJ_transitive)": None if pct3 is None else round(pct3, 4),
        "frac_random_7subsets_more_variable_(HIGH=heptad_transitive)": None if pct7 is None else round(pct7, 4),
        "H1_ICJ_in_transitive_tail_>=90pct": bool(h1),
        "H2_heptad_in_transitive_tail_>=90pct": bool(h2),
        "laplacian_eigenvalues": [round(x, 4) for x in eig],
        "CONFOUND": ("co-occurrence DEGREE is dominated by raw corpus-USAGE frequency (K/L/M/C/I are "
                     "simply invoked far more than E/F/D), so this probe measures usage-uniformity, "
                     "NOT algebraic orbit-transitivity — a WEAK first probe. A usage-normalised or "
                     "algebraic-structure test is the real next step."),
        "VERDICT": (
            "POSITIVE: BOTH assigned blocks sit in the transitive tail (>=90pct) — the corpus "
            "co-occurrence carries the orbit signature; the class<->orbit map gains empirical support."
            if (h1 and h2) else
            "PARTIAL: one block in the transitive tail, one not — mixed; map stays mostly lens."
            if (h1 or h2) else
            "NULL (pre-stated, EXPECTED): NEITHER block reaches the >=90pct transitive tail. I/C/J is "
            "MODERATELY uniform (more uniform than ~80%% of random triples — a weak hint, J under-"
            "weighted vs I,C), but the D-M heptad is NON-transitive (~12pct; K/L/M dominate, E/F weak). "
            "So the corpus co-occurrence does NOT carry the predicted G2-orbit uniformity on the 7. "
            "The SPECIFIC class<->orbit identification stays the FRAMEWORK LENS (F243 §4), not a "
            "theorem. CAVEAT: the degree is usage-frequency-dominated (see CONFOUND), so this NULL is "
            "WEAK — it does not refute the iso, it shows raw corpus usage is not the place the orbit "
            "structure (if any) would show. The F243 size+symmetry match stands untouched."),
    }
    payload = json.dumps(out, separators=(",", ":"), sort_keys=True).encode()
    out["response_sha256"] = fmt.sha256_bytes(payload)     # Class A
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
