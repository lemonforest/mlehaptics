"""F1176: the coupling-community PARALLEL-FINDER — the F1175 refinement (a).

F1175: reconstructing a lacuna needs to FIND the recurrence-parallel. Naive fixed-period (i+-P) failed; global raw
nearest-neighbour (F1175c) reached 0.090 (2x the prior). This builds the spectral upgrade: use the low-eigenmode
COMMUNITY structure (the F1172 identity applied to community-finding) to select the damaged line's formula-FAMILY
through the coupling graph — spectral neighbours, not just raw overlap — then reconstruct from the family consensus.

Clean isolation of the spectral step: RAW-KNN and SPECTRAL-COMMUNITY use the SAME family size T and the SAME consensus
threshold; they differ ONLY in HOW the T family members are chosen (raw content-overlap vs nearest in the low-eigenmode
embedding of a local coupling graph). So any gap is attributable to the spectral structure, not to "consensus helps".

Corpus (Gutenberg-attested): 28282 Egyptian Literature (Budge — hymns/litanies/Book of the Dead). srmech Class-L
(signed_laplacian + symmetric_eigendecompose); numpy-free; no magnitude-builtin.
"""
import re, random
from srmech.amsc import laplacian as L

STOP = set(("the of a an and to in on at for with by from as is are was were be been being it he she they thou thee "
            "thy thine ye you your his her its their this that these those o oh unto upon into out over who whom which "
            "what when where how then than not no i am art hath have has had do doth did shall will would may might me "
            "my we us our them him all one there here now come came forth made make let god").split())
PATH = "/tmp/egylit.txt"


def load():
    t = open(PATH, encoding='utf-8', errors='replace').read()
    s = re.search(r"\*\*\* START OF.*?\*\*\*", t); e = re.search(r"\*\*\* END OF", t)
    body = t[s.end():e.start()] if (s and e) else t
    rows = []
    for ln in re.split(r"[.\n;:!?]", body):
        ws = [w for w in re.findall(r"[a-z]+", ln.lower()) if w not in STOP and len(w) > 2]
        if len(set(ws)) >= 4:
            rows.append(frozenset(ws))
    return rows


def jac(a, b):
    return len(a & b) / max(1, len(a | b))


def candidates(survive, rows, i, K):
    """top-K lines by content-overlap with the surviving half (the local neighbourhood to spectrally resolve)."""
    sc = [(jac(survive, rows[j]), j) for j in range(len(rows)) if j != i]
    sc.sort(reverse=True)
    return [j for _, j in sc[:K]]


def family_raw(survive, rows, cand, T):
    """RAW-KNN family: the T candidates with the highest direct content-overlap with the surviving half."""
    return sorted(cand, key=lambda j: -jac(survive, rows[j]))[:T]


def family_spectral(survive, rows, cand, T, m=5):
    """SPECTRAL-COMMUNITY family: build a local coupling graph over {query, candidates}, low-eigenmode-embed
    (Class-L), and take the T candidates nearest the query in that embedding — spectral neighbours (through the
    graph), which pull in formula-family members that raw overlap alone under-ranks."""
    nodes = [survive] + [rows[j] for j in cand]          # node 0 = the surviving-half query
    n = len(nodes)
    edges, weights = [], []
    for a in range(n):
        for b in range(a + 1, n):
            v = jac(nodes[a], nodes[b])
            if v > 0.0:
                edges.append((a, b)); weights.append(v)
    if not edges:
        return family_raw(survive, rows, cand, T)
    evals, evecs = L.symmetric_eigendecompose(L.signed_laplacian(n, edges, weights))
    evals = [float(x) for x in evals]
    low = [k for k in sorted(range(n), key=lambda k: evals[k]) if evals[k] > 1e-6][:m]
    if not low:
        return family_raw(survive, rows, cand, T)
    q = [float(evecs[0][k]) for k in low]
    def d2(node):
        return sum((float(evecs[node][k]) - q[t]) ** 2 for t, k in enumerate(low))
    near = sorted(range(1, n), key=d2)[:T]
    return [cand[node - 1] for node in near]


def consensus(fam, rows, survive, frac):
    wc = {}
    for j in fam:
        for w in rows[j]:
            wc[w] = wc.get(w, 0) + 1
    thr = max(2, int(frac * len(fam)))
    return set(w for w, c in wc.items() if c >= thr) - survive


if __name__ == "__main__":
    rows = load()
    N = len(rows)
    df = {}
    for r in rows:
        for w in r:
            df[w] = df.get(w, 0) + 1
    freq = sorted(df, key=lambda w: -df[w])
    K, T, FRAC, M = 140, 12, 0.34, 5          # neighbourhood / family size / consensus frac / low-modes (design, not tuned to result)
    random.seed(5)
    samp = random.sample(range(N), 150)
    r_prior = r_nn = r_rawc = r_spec = r_specbest = 0.0
    got = 0
    for i in samp:
        words = list(rows[i]); random.shuffle(words)
        survive = frozenset(words[:len(words) // 2]); masked = set(words[len(words) // 2:])
        if not masked:
            continue
        got += 1
        cand = candidates(survive, rows, i, K)
        fr = family_raw(survive, rows, cand, T)
        fs = family_spectral(survive, rows, cand, T, m=M)
        nn = family_raw(survive, rows, cand, 1)                    # single best raw match over ALL candidates (F1175c)
        pred_nn = (set(rows[nn[0]]) - survive) if nn else set()
        pred_rawc = consensus(fr, rows, survive, FRAC)
        pred_spec = consensus(fs, rows, survive, FRAC)
        # the COMBINATION: spectral community to find the family, then the single BEST-raw member WITHIN it
        best_in_fs = max(fs, key=lambda j: jac(survive, rows[j])) if fs else None
        pred_specbest = (set(rows[best_in_fs]) - survive) if best_in_fs is not None else set()
        pred_prior = set(freq[:len(pred_spec) or 8]) - survive
        rec = lambda p: len(p & masked) / len(masked)
        r_prior += rec(pred_prior); r_nn += rec(pred_nn); r_rawc += rec(pred_rawc); r_spec += rec(pred_spec)
        r_specbest += rec(pred_specbest)
    print("F1176: coupling-community parallel-finder (Egyptian formulaic; %d lines, %d masked trials)\n" % (N, got))
    print("  lacuna-word recall (survive half -> recover the missing half):")
    print("     PRIOR (global frequency)                              : %.3f" % (r_prior / got))
    print("     GLOBAL-NN (single best raw match over all cand, F1175c): %.3f" % (r_nn / got))
    print("     RAW-KNN consensus  (T=%d raw content-neighbours)       : %.3f" % (T, r_rawc / got))
    print("     SPECTRAL-COMMUNITY consensus (T=%d, low-modes=%d)       : %.3f" % (T, M, r_spec / got))
    print("     SPECTRAL-COMMUNITY -> single best-in-family (COMBINED) : %.3f" % (r_specbest / got))
    print("\n  isolation: SPECTRAL vs RAW-KNN consensus (same T, same threshold) = %+.1f pp  (the spectral family-selection gain)" % (
        100 * (r_spec - r_rawc) / got))
    print("  COMBINED (spectral family + single-best) vs GLOBAL-NN             = %+.1f pp" % (100 * (r_specbest - r_nn) / got))
