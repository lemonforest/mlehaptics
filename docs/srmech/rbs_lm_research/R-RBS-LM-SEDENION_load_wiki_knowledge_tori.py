r"""R-RBS-LM-SEDENION-LOAD — load the sedenion-addressable RBS-HDC instrument (F465) with REAL
knowledge (simplewiki) and read the SHAPE OF THE TORI it takes.

User (2026-06-06): "what happens if we load this sedenion shaped kernel with our knowledge? like if we
seed it for the shape of the tori our rbs-hdc instrument would take? for things like our wiki knowledge."

The reading: a knowledge co-occurrence graph's LOW Laplacian eigenmodes are its smooth global coordinates —
and the toroidal signature is near-degenerate eigenvalue PAIRS (each cos/sin pair = one circle = one torus
angle; the ring-graph fact). So:
  1. build the wiki co-occurrence Class-L Laplacian (srmech-native), eigendecompose (F172 storage signature);
  2. TEST the toroidal signature — how many low modes come in near-degenerate (circular) pairs = the tori;
  3. SEED the sedenion instrument (F465): the principal non-DC eigenmodes -> the octonion working block
     e1..e7 (the ≤7 reversible tori), DC -> anchor e0, the tail -> the EC block e8..e15;
  4. read each octonion slot's THEME (top tokens of its eigenmode) — what the instrument's tori encode.
The instrument's shape is NOT imposed: it IS the knowledge's own co-occurrence eigenspectrum, on the
sedenion/Hopf toroidal coordinates.
"""
import importlib.util as U
import numpy as np
from collections import Counter                      # vocab SELECTION + transient edge weights (not storage)
from srmech.amsc.laplacian import dense_laplacian, hermitian_eigendecompose
from srmech.amsc.hdc import bind, bundle, similarity
from srmech.signal_processing import mint_vector
import srmech

CORPUS = "/home/skirklan/corpora/wikipedia/simplewiki_extracted"
MAX_ARTICLES = 12000
VOCAB = 128
WINDOW = 5
D = 8192

_spec = U.spec_from_file_location("wk", "docs/srmech/rbs_lm_research/R-RBS-LM-WIKI_kernel_build.py")
wk = U.module_from_spec(_spec); _spec.loader.exec_module(wk)


def _bundle(vs):
    if len(vs) == 1:
        return vs[0]
    if len(vs) % 2 == 0:
        vs = vs + [mint_vector("__pad__", D=D)]
    return bundle(vs)


def main():
    print(f"=== R-RBS-LM-SEDENION-LOAD — wiki knowledge → the tori the instrument takes  (srmech {srmech.__version__}) ===\n")

    # ---- 1. build the wiki co-occurrence Class-L Laplacian (srmech-native) ----
    print(f"streaming ≤{MAX_ARTICLES} simplewiki articles, vocab={VOCAB}, window={WINDOW} ...")
    sections = [toks for toks, _ in wk.read_wiki_articles(CORPUS, max_articles=MAX_ARTICLES)]
    freq = Counter()
    for t in sections:
        freq.update(t)
    vocab = [t for t, _ in freq.most_common(VOCAB)]
    vidx = {t: i for i, t in enumerate(vocab)}
    N = len(vocab)
    ec = Counter()
    for toks in sections:
        ix = [vidx[t] for t in toks if t in vidx]
        for i in range(len(ix)):
            for j in range(i + 1, min(i + WINDOW, len(ix))):
                a, b = ix[i], ix[j]
                if a != b:
                    ec[(min(a, b), max(a, b))] += 1
    edges = list(ec.keys()); weights = [float(w) for w in ec.values()]
    L = dense_laplacian(N, edges, weights)                 # Class L
    evals, evecs = hermitian_eigendecompose(L)             # the F172 storage signature
    evals = np.asarray(evals, dtype=float); evecs = np.asarray(evecs, dtype=float)
    # orient: column i = i-th eigenvector; ascending eigenvalues
    order = np.argsort(evals); evals = evals[order]; evecs = evecs[:, order]
    if evecs.shape[0] != N:                                # row-major fallback
        evecs = evecs.T[:, order]
    print(f"  {len(sections)} articles, N={N} nodes, {len(edges)} edges; "
          f"eig range [{evals[0]:.2f} .. {evals[-1]:.2f}]")

    # ---- 2. TEST the toroidal signature: near-degenerate low-eigenvalue PAIRS (circles) ----
    print("\n[1] toroidal signature — do the low modes come in near-degenerate PAIRS (= circles = tori)?")
    lo = evals[1:17]                                       # skip the DC mode (eigval≈0)
    span = evals[-1] - evals[1] + 1e-9
    pairs = 0
    for p in range(0, 14, 2):
        within = abs(lo[p + 1] - lo[p])
        between = abs(lo[p + 2] - lo[p + 1]) if p + 2 < len(lo) else span
        circ = within < 0.5 * between                      # tight within-pair, gap to next pair
        pairs += int(circ)
        print(f"    modes ({p+1:2d},{p+2:2d}): λ=({lo[p]:.1f},{lo[p+1]:.1f})  within={within:.1f} "
              f"next-gap={between:.1f}  {'CIRCLE (torus angle)' if circ else 'single'}")
    print(f"    → {pairs} circular (toroidal) coordinate-pairs in the low spectrum")

    # ---- 3. SEED the sedenion instrument: principal eigenmodes -> octonion working block ----
    print("\n[2] seed the sedenion-addressable instrument (F465) with the wiki tori:")
    ADDR = [mint_vector(f"SEDENION:e{k}", D=D) for k in range(16)]
    def mode_theme(i, top=8):                              # top tokens of eigenmode i (by |component|)
        comp = evecs[:, i]
        idx = np.argsort(-np.abs(comp))[:top]
        return [vocab[j] for j in idx]
    def mode_hv(i, top=21):
        comp = evecs[:, i]
        idx = np.argsort(-np.abs(comp))[:top]
        return _bundle([mint_vector(vocab[j], D=D) for j in idx])
    # e0 = anchor (DC/global mode); e1..e7 = the 7 principal tori (reversible working set); e8..e15 = EC tail
    slot_mode = {0: 0}                                     # anchor = DC
    for k in range(1, 16):
        slot_mode[k] = k                                   # eigenmode k at slot e_k
    register = _bundle([bind(ADDR[k], mode_hv(m)) for k, m in slot_mode.items()])
    print("    octonion working block e1..e7 = the 7 principal tori (the ≤𝕆 reversible working set):")
    for k in range(1, 8):
        print(f"      e{k}  λ={evals[slot_mode[k]]:7.1f}  theme: {', '.join(mode_theme(slot_mode[k]))}")
    print(f"    anchor e0 (DC/global): {', '.join(mode_theme(0, 6))}")
    print(f"    EC/carry block e8..e15: modes 8..15 (the spectral tail — detail/error-correction region)")

    # ---- 4. read a slot back by sedenion address: does the instrument return its torus? ----
    print("\n[3] read by sedenion ADDRESS — recover each torus's theme from the loaded register:")
    theme_cb = {f"e{k}": mode_hv(slot_mode[k]) for k in range(16)}
    hits = 0
    for k in range(1, 8):
        noisy = bind(ADDR[k], register)
        best = max(theme_cb, key=lambda n: similarity(noisy, theme_cb[n]))
        ok = best == f"e{k}"; hits += ok
        print(f"      address e{k} → {best}  {'✓' if ok else '(crosstalk)'}")
    print(f"    {hits}/7 principal tori addressable from the loaded sedenion register")

    print("\nVERDICT:")
    print(f"  • Loading wiki knowledge SEEDS the instrument with the knowledge's OWN co-occurrence eigenspectrum")
    print(f"    (F172) — the shape is not imposed. {pairs} of the low modes are near-degenerate PAIRS = toroidal")
    print(f"    (circular) coordinates — the literal 'tori the instrument takes'.")
    print(f"  • The 7 principal non-DC eigenmodes seed the OCTONION working block (e1..e7, the ≤𝕆 reversible")
    print(f"    tori); the DC/global mode is the anchor e0; the spectral tail is the EC/carry block (e8..e15).")
    print(f"  • Each octonion slot is a coherent THEME (its eigenmode's top tokens) and is addressable by its")
    print(f"    sedenion name ({hits}/7). The RBS-HDC instrument's geometry IS the knowledge's spectral shape.")


if __name__ == "__main__":
    main()
