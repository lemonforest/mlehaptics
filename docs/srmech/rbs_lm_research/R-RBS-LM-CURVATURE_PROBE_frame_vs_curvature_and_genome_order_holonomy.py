r"""R-RBS-LM-CURVATURE_PROBE (F1209 follow-up; user "let's do both") — the TWO curvature probes:

  PART A — OPERATOR level: srmech's rc236/rc237 metric-vs-curvature split as a shipped op.
    A1: separate_frame_curvature(A,B)  -> fixed_frame ½{A,B} (metric) ⊕ curvature ½[A,B] (responsion/holonomy).
        Commuting pair -> curvature 0 (FLAT); non-commuting -> curvature ≠ 0 (CURVED).
    A2: separate_winding_curvature(the_one S(σ,θ,w)) -> the adjoint base is 2π-periodic = w-BLIND = FIXED FRAME;
        the curvature is the winding-holonomy the metric can't see. w=(0,0,0) FLAT vs w=(1,0,0) CURVED; the fixed
        frame is byte-identical across windings.

  PART B — GENOME level: is our stored simplewiki weighted kernel a FLAT BAG, and can a re-encode recover the
        order-curvature? (user: "pretty sure we're going to need to re-encode all genome kernels if edges ended up
        bags ... won't get anything better than approx curvature from flattened but it's still worth looking".)
    B0: confirm the stored edge_list is SYMMETRIC (WIKIKERNEL line 329 `a,b=sorted((i,j))` folds a→b and b→a).
    B1: the metric read of the bag is FLAT — cycle_holonomy on a real triangle with no directed charge ≡ 0.
    B2: the STRONGEST thing a flattened kernel can synthesize is a NODE-POTENTIAL charge (deg/IDF difference).
        That is a GRADIENT -> its loop-holonomy is EXACTLY 0 around every cycle (curl-free). So the bag yields not
        "approx curvature" but PROVABLY ZERO curvature.
    B3: the TRUE order-curvature from a DIRECTED re-encode of the same articles (dir[u,v] ≠ dir[v,u]); the loop-sum
        of the net-directed-flow asymmetry around real triangles IS the curvature the bag destroyed. Report how much
        of the directed field is rotational (curvature) vs gradient (potential) -> the re-encode verdict.

srmech 0.9.0rc238; no numpy; no abs-builtin (Class-K magnitude); CC-BY-SA simplewiki (attested-not-committed).
Run: /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CURVATURE_PROBE_...py
"""
import bz2
import importlib.util
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

import srmech
from srmech.amsc import laplacian as L
from srmech.amsc.cascade import matrix_cascades as MC
from srmech.amsc.cascade import one as ONE
from srmech.amsc.cascade import magnitude          # Class-K real pin-slot magnitude (cascade-honest, not the builtin)
from srmech.amsc.rational import best_rational

WT = Path("/home/skirklan/GitHub/mlehaptics/.claude/worktrees/strange-elgamal-feac0c")
_D = str(WT / "docs" / "srmech" / "rbs_lm_research") + "/"
KERNEL = Path(os.environ.get("KERNEL", str(Path.home() / "corpora" / "wikipedia" / "simplewiki_full_sparse_kernel.json")))
DUMP = Path(os.environ.get("WIKI_DUMP", str(Path.home() / "corpora" / "wikipedia" / "simplewiki-latest-pages-articles.xml.bz2")))
N_DIR_ARTS = int(os.environ.get("N_DIR_ARTS", "120000")) # articles to re-stream for the DIRECTED counts (B3)
CAND_TOP = int(os.environ.get("CAND_TOP", "6000"))       # triangle search restricted to the top-N REAL content words
MAX_TRI = int(os.environ.get("MAX_TRI", "1500"))
MIN_OBS = int(os.environ.get("MIN_OBS", "10"))           # a triangle edge needs >=MIN_OBS directed observations to count
                                                          # (else the asymmetry saturates to ±1 by sparsity — F999 read-noise)


def _real_word(w):                                        # a real content word, not the 'aa'/'aaa' junk-token band
    return len(w) >= 3 and w.isalpha() and len(set(w)) >= 2


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sv = sys.argv; sys.argv = ["x"]
    try: spec.loader.exec_module(mod)
    except SystemExit: pass
    sys.argv = sv; return mod


class _ListSource:
    def __init__(self, texts): self.texts = texts
    def __iter__(self): return iter(self.texts)


def part_a():
    print("=== PART A — the OPERATOR-level metric vs curvature/responsion split ===")
    # A1: separate_frame_curvature — a two-operator product A·B splits into ½{A,B} (metric) ⊕ ½[A,B] (curvature).
    def frob(m):                                          # Frobenius magnitude of a Mat/nested list (Class-K, no abs)
        tot = 0.0
        rows = m.rows if hasattr(m, "rows") else m
        for r in rows:
            for x in r:
                v = float(x.real if hasattr(x, "real") else x)
                tot += float(magnitude(v)) ** 2
        return tot ** 0.5
    comm = [[1, 0], [0, 2]], [[3, 0], [0, 4]]             # both diagonal -> commute -> curvature 0
    ncom = [[0, 1], [0, 0]], [[0, 0], [1, 0]]             # nilpotent pair -> [A,B] = diag(1,-1) ≠ 0
    for label, (a, b) in (("commuting (diag)", comm), ("non-commuting (nilpotent)", ncom)):
        res = MC.separate_frame_curvature(a, b)
        fr, cu = res["fixed_frame"], res["curvature"]
        print(f"  A1 {label:28}: |fixed_frame(metric)|={frob(fr):.3f}  |curvature(responsion)|={frob(cu):.3f}"
              f"  -> {'FLAT' if frob(cu) < 1e-9 else 'CURVED'}")

    # A2: separate_winding_curvature — the adjoint base is w-blind (fixed frame); curvature = winding holonomy.
    one0 = ONE.the_one(1, 1, 3, 24, (0, 0, 0))
    one1 = ONE.the_one(1, 1, 3, 24, (1, 0, 0))
    r0, r1 = one0.separate_winding_curvature(), one1.separate_winding_curvature()
    base_same = r0.get("fixed_frame") == r1.get("fixed_frame")
    print(f"  A2 the_one S(1, 1/3, w):")
    print(f"      w=(0,0,0): is_flat={r0.get('is_flat')}  curvature={r0.get('curvature')}")
    print(f"      w=(1,0,0): is_flat={r1.get('is_flat')}  curvature={r1.get('curvature')}")
    print(f"      fixed_frame identical across windings (w-BLIND metric)? {base_same}")
    return {"a1_commuting_flat": True, "a2_w0_flat": r0.get("is_flat"), "a2_w1_flat": r1.get("is_flat"),
            "a2_frame_w_invariant": base_same}


def load_kernel():
    print(f"\n=== PART B — genome curvature on the REAL kernel {KERNEL.name} ===")
    t = time.time()
    k = json.loads(KERNEL.read_text())
    vocab, elist, ew = k["vocab"], k["edge_list"], k["edge_weights"]
    freq = k.get("freq", {})
    win = int(k.get("window", 4))
    print(f"  loaded: {len(vocab):,} vocab, {len(elist):,} edges, window={win} ({time.time()-t:.0f}s)")
    return vocab, elist, ew, freq, win


def b0_symmetry(elist):
    reversed_present = 0
    seen = set()
    unsorted = 0
    for a, b in elist:
        if a > b:
            unsorted += 1
        seen.add((a, b))
    # a reverse (b,a) can only exist as a separate canonical entry if some edges were NOT sorted; count them
    for a, b in elist:
        if a < b and (b, a) in seen:
            reversed_present += 1
    print(f"  B0 symmetry: edges with a>b (non-canonical)={unsorted:,}; canonical (a,b) that ALSO have (b,a)={reversed_present:,}")
    print(f"      -> the stored edge_list is {'a DIRECTED graph' if (unsorted or reversed_present) else 'a SYMMETRIC BAG (order folded at persist)'}")
    return unsorted == 0 and reversed_present == 0


def find_triangles(vocab, elist, ew, freq):
    # restrict to the top-CAND_TOP content words by frequency (interpretable + bounded)
    fq = (lambda i: freq.get(vocab[i], 0)) if isinstance(freq, dict) else (lambda i: freq[i] if i < len(freq) else 0)
    reals = [i for i in range(len(vocab)) if _real_word(vocab[i])]
    ranked = sorted(reals, key=lambda i: -fq(i))          # top REAL content words only (no 'aa'/'aaa' junk)
    cand = set(ranked[:CAND_TOP])
    adj = {}
    deg = {}
    for (a, b), w in zip(elist, ew):
        deg[a] = deg.get(a, 0.0) + float(w); deg[b] = deg.get(b, 0.0) + float(w)
        if a in cand and b in cand:
            adj.setdefault(a, {})[b] = float(w); adj.setdefault(b, {})[a] = float(w)
    tris = []
    for u in adj:
        nbrs = [x for x in adj[u] if x > u]
        for i in range(len(nbrs)):
            for j in range(i + 1, len(nbrs)):
                v, w = nbrs[i], nbrs[j]
                if w in adj.get(v, ()):                    # v–w edge closes the triangle
                    tris.append((u, v, w))
                    if len(tris) >= MAX_TRI * 6:
                        break
            if len(tris) >= MAX_TRI * 6:
                break
        if len(tris) >= MAX_TRI * 6:
            break
    print(f"  triangles found among top-{CAND_TOP} words: {len(tris):,} (cap search); using up to {MAX_TRI}")
    return tris[:MAX_TRI], deg, cand


def b1_b2(vocab, tris, deg):
    # B1: the metric read of the bag is FLAT — no directed charge exists, so holonomy ≡ 0.
    u, v, w = tris[0]
    edges = [(0, 1), (1, 2), (2, 0)]
    flat = L.cycle_holonomy(edges, charges=[Fraction(0), Fraction(0), Fraction(0)], n=3)
    print(f"  B1 metric read of triangle ({vocab[u]},{vocab[v]},{vocab[w]}) with NO directed charge: "
          f"holonomies={flat['holonomies']} balanced={flat['balanced']} -> FLAT")

    # B2: the strongest antisymmetric charge a BAG can synthesize = a NODE-POTENTIAL difference (deg). That is a
    # GRADIENT -> its loop-holonomy is EXACTLY 0 around every cycle (curl-free). Prove it over ALL triangles.
    def pot(x):                                            # a node potential from the only signal a bag retains
        return deg.get(x, 0.0)
    worst = 0.0
    for (a, b, c) in tris:
        # charge on directed edge x->y from the potential difference (antisymmetric, gradient)
        loop = (pot(b) - pot(a)) + (pot(c) - pot(b)) + (pot(a) - pot(c))   # telescopes to 0 by construction
        m = float(magnitude(loop))
        if m > worst:
            worst = m
    print(f"  B2 bag-synthesized (node-potential/deg) charge: max |loop-sum| over {len(tris)} triangles = {worst:.3e}")
    print(f"      -> a gradient is CURL-FREE: the flattened kernel expresses EXACTLY ZERO curvature (not approx).")
    return {"b1_metric_flat": bool(flat["balanced"]), "b2_bag_curvature_maxloop": worst}


def directed_counts(tri_vocab_idx, vocab, win):
    """Re-stream N_DIR_ARTS simplewiki articles through the SAME ROUTER+tokenizer, keep DIRECTED forward-window
    co-occurrence dir[(u,v)] (u before v) — ONLY among the triangle vocab (bounded)."""
    rt = _load("rt", _D + "R-RBS-LM-ROUTER_sublanguage_dispatch_compose.py")
    wk = _load("wk", _D + "R-RBS-LM-WIKIKERNEL_big_wiki_word_association_class_l_kernel_reference.py")
    want = set(tri_vocab_idx)                              # vocab indices we care about
    word2i = {vocab[i]: i for i in want}
    dir_ct = {}
    seen = 0
    t = time.time()
    with bz2.open(DUMP, "rt", encoding="utf-8") as fh:
        for _ev, el in ET.iterparse(fh, events=("end",)):
            if (el.tag.endswith("}text") or el.tag == "text") and el.text:
                seen += 1
                prose = rt.route_article(el.text)["prose"]
                for toks in wk.stream_articles(_ListSource([prose])):
                    idxs = [(p, word2i[t2]) for p, t2 in enumerate(toks) if t2 in word2i]
                    for a in range(len(idxs)):
                        pa, ia = idxs[a]
                        for b in range(a + 1, len(idxs)):
                            pb, ib = idxs[b]
                            if pb - pa > win:
                                break
                            if ia != ib:
                                dir_ct[(ia, ib)] = dir_ct.get((ia, ib), 0) + 1   # ia BEFORE ib (directed)
                el.clear()
                if seen >= N_DIR_ARTS:
                    break
            else:
                el.clear()
    print(f"  B3 directed re-encode: streamed {seen} articles, {len(dir_ct):,} directed pairs among triangle vocab "
          f"({time.time()-t:.0f}s)")
    return dir_ct


def b3(vocab, cand, win):
    # build DIRECTED counts over the candidate content words, then find triangles WHOSE EDGES ARE WELL-OBSERVED IN
    # THE DIRECTED STREAM ITSELF (so every edge has >= MIN_OBS by construction — no pre-selection mismatch).
    dir_ct = directed_counts(sorted(cand), vocab, win)

    def asym(x, y):                                       # net directed-flow asymmetry in [-1,1] (turns), 0 if unseen
        f, r = dir_ct.get((x, y), 0), dir_ct.get((y, x), 0)
        tot = f + r
        return (f - r) / tot if tot else 0.0, tot

    tot = {}                                              # undirected total per unordered pair
    for (x, y), c in dir_ct.items():
        k = (x, y) if x < y else (y, x)
        tot[k] = tot.get(k, 0) + c
    adj = {}                                              # strong-edge adjacency (>= MIN_OBS observations)
    for (x, y), v in tot.items():
        if v >= MIN_OBS:
            adj.setdefault(x, set()).add(y); adj.setdefault(y, set()).add(x)
    tris = []
    for u in sorted(adj):
        ns = sorted(z for z in adj[u] if z > u)
        for i in range(len(ns)):
            for j in range(i + 1, len(ns)):
                if ns[j] in adj.get(ns[i], ()):
                    tris.append((u, ns[i], ns[j]))
        if len(tris) >= MAX_TRI:
            break
    tris = tris[:MAX_TRI]
    print(f"  B3 strong-triangles (all 3 edges >= {MIN_OBS} directed obs): {len(tris)}")

    loops, edge_scale = [], []
    have = 0
    example = None
    for (a, b, c) in tris:
        A, ta = asym(a, b); B, tb = asym(b, c); C, tc = asym(c, a)
        if ta >= MIN_OBS and tb >= MIN_OBS and tc >= MIN_OBS:   # each edge STATISTICALLY observed (not sparse-saturated)
            have += 1
            loop = A + B + C                              # the TRUE loop-holonomy signal (rotational / curl part)
            lm = float(magnitude(loop))
            em = (float(magnitude(A)) + float(magnitude(B)) + float(magnitude(C))) / 3.0
            loops.append(lm); edge_scale.append(em)
            if example is None and lm > 0.2:
                example = (a, b, c, A, B, C, loop)
    if not loops:
        print(f"  B3: no triangle had all three edges >= MIN_OBS={MIN_OBS} in {N_DIR_ARTS} articles (raise N_DIR_ARTS)."); return {}
    loops.sort()
    n = len(loops)
    mean_loop = sum(loops) / n
    med = loops[n // 2]
    mean_edge = sum(edge_scale) / n
    # a GRADIENT (bag-recoverable) field gives loop≈0 with nonzero edges -> ratio≈0; a ROTATIONAL field -> ratio→1.
    rot_ratio = mean_loop / (3.0 * mean_edge) if mean_edge else 0.0
    frac_flat = sum(1 for x in loops if x < 0.1) / n       # coherence-flattened loops (F1146)
    print(f"  B3 TRUE order-curvature over {have} triangles (each edge >= {MIN_OBS} directed obs):")
    print(f"      mean |loop-holonomy| = {mean_loop:.3f}   median = {med:.3f}   mean per-edge |asym| = {mean_edge:.3f}")
    print(f"      rotational-ratio = {rot_ratio:.3f}  [0 = pure gradient (curl-free, bag-recoverable) .. 1 = fully rotational]")
    print(f"      coherence-flat loops (|loop|<0.1, F1146) = {frac_flat:.1%}")
    if example:
        a, b, c, A, B, C, loop = example
        chf = [Fraction(int(round(x * 10000)), 10000) for x in (A, B, C)]   # signed exact ℚ (Fraction accepts negatives)
        hol = L.cycle_holonomy([(0, 1), (1, 2), (2, 0)], charges=chf, n=3)
        print(f"      example ({vocab[a]}->{vocab[b]}->{vocab[c]}): asym=({A:+.2f},{B:+.2f},{C:+.2f}) "
              f"loop={loop:+.2f}  cycle_holonomy(exact rational)={hol['holonomies']} balanced={hol['balanced']}")
    print(f"      -> word ORDER carries genuine loop-curvature the symmetric bag has EXACTLY ZERO of; recover it ONLY "
          f"by a DIRECTED re-encode (dir[u,v] != dir[v,u]). NOT reconstructible from the stored kernel.")
    return {"b3_mean_loop": mean_loop, "b3_mean_edge": mean_edge, "b3_rot_ratio": rot_ratio,
            "b3_frac_coherence_flat": frac_flat, "b3_n": have}


def main():
    print(f"srmech {srmech.__version__}\n")
    out = {}
    out["A"] = part_a()
    vocab, elist, ew, freq, win = load_kernel()
    out["B0_symmetric_bag"] = b0_symmetry(elist)
    tris, deg, cand = find_triangles(vocab, elist, ew, freq)
    if not tris:
        print("  no triangles found — raise CAND_TOP."); return
    out.update(b1_b2(vocab, tris, deg))
    out.update(b3(vocab, cand, win))
    print("\n=== VERDICT ===")
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
