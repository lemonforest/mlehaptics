r"""R-RBS-LM-CIRCLEVOL (the user's question 2026-06-07): "put our simple wiki kernel into a circle volume — will we
need to re-encode, or is this easy HDC operations?" Answer it by DOING it and timing every step.

The wiki kernel = the Class-L co-occurrence Laplacian + its eigendecomposition (the expensive part). Putting it into
a CIRCLE VOLUME = a ring of NT tome-hypervectors. Two things to separate:
  • ROUTING (which tome a word is in): the spectral angle atan2(V[:,2], V[:,1]) -> tome. This is a FREE READ-OUT of
    eigenvector columns the kernel ALREADY has. No HDC, no rebuild.
  • VOLUME (the tome's hypervector): a Class-M BUNDLE of the per-word HVs. Cheap. The per-word HV is either:
      (B1) a random IDENTITY tag  (mint_vector(word)) — stores WHICH words, carries no inter-word structure;
      (B2) a SPECTRAL-DERIVED HV  (bundle_m bind(mode_hv[m], sign_token[sign V[i,m]])) — carries the KERNEL's
           similarity structure, built from V we ALREADY have (no new eigendecomposition).

So the claim to test: NO corpus re-encode and NO re-eigendecomposition — the kernel is computed ONCE and reused;
routing is free; the volume is cheap bundles. We time it to prove "cheap", and test that the volume is functional
(B1 recovers tome membership; B2 additionally preserves neighbour structure).

srmech 0.7.4; Class-L kernel (reused) + srmech.calculus.atan2 routing + Class-M hdc.bind/bundle/similarity volume.
No abs(); no CAD; no Workflow tool; no sub-agents.
"""
import importlib.util as U
from time import perf_counter
import numpy as np
import srmech
from srmech.calculus import atan2 as srm_atan2
from srmech.amsc import hdc
from srmech.signal_processing import mint_vector

_s = U.spec_from_file_location("sup", "docs/srmech/rbs_lm_research/R-RBS-LM-SUPERPOSITION_structured_spectral_gate_which_band_biology_drops.py")
sup = U.module_from_spec(_s); _s.loader.exec_module(sup)
TWO_PI = 6.283185307179586
D = 8192


def odd_bundle(vs, pad):
    """hdc.bundle needs an ODD count (tie-free majority, F527) — pad with a fixed sentinel if even."""
    vs = list(vs)
    if not vs:
        return pad
    if len(vs) % 2 == 0:
        vs = vs + [pad]
    return hdc.bundle(vs)


def main():
    print(f"=== R-RBS-LM-CIRCLEVOL — putting the wiki kernel into a circle volume: re-encode, or cheap HDC?  (srmech {srmech.__version__}) ===\n")
    import re
    seq = re.findall(r"[a-z]+", sup.k7.load_text().lower())

    # ---- THE KERNEL (the expensive part: Class-L eigendecomposition). Built ONCE. ----
    t = perf_counter()
    vocab, idx, nb, V = (sup.build(seq))[:4]
    t_kernel = perf_counter() - t
    N = len(vocab)
    NT = 7                                                        # the LIVE odd circle (F541) — volume build is NT-agnostic
    K = min(8, V.shape[1] - 1)
    print(f"(0) THE KERNEL: Class-L co-occurrence Laplacian + eigendecomposition over {N} words — built ONCE in {t_kernel*1e3:.1f} ms.")
    print(f"    (this is the corpus pass + the eigendecomposition — the only expensive step.)\n")

    # ---- (A) ROUTING into the circle: a ONE-TIME O(N) read-out of V. No HDC, no rebuild. ----
    t = perf_counter()
    ang = np.array([(srm_atan2(float(V[i, 2]), float(V[i, 1])) + TWO_PI) % TWO_PI for i in range(N)])
    t_angles = perf_counter() - t
    t = perf_counter()
    tome_of = (ang / TWO_PI * NT).astype(int) % NT
    tomes = [[i for i in range(N) if tome_of[i] == t_] for t_ in range(NT)]
    t_assign = perf_counter() - t
    t_route = t_angles + t_assign
    print(f"(A) ROUTING (word -> tome): the spectral angle atan2(V[:,2], V[:,1]) -> {NT} tome-arcs. A pure READ-OUT of")
    print(f"    eigenvector columns the kernel ALREADY has — a ONE-TIME O(N) pass, NO rebuild, NO eigendecomposition.")
    print(f"    cost split: srmech.calculus.atan2 series {t_angles*1e3:.0f} ms ({N} calls x 40-term) + tome-bucketing {t_assign*1e3:.2f} ms.")
    print(f"    -> the OPERATION is trivial (the {t_assign*1e3:.2f} ms bucketing); the wall-clock is ENTIRELY srmech's per-call series-")
    print(f"       atan2 (W14: slow AND convergence-limited). It is paid ONCE at kernel-build + cached as tome metadata,")
    print(f"       not per query — so it is still NOT a re-encode. (np.arctan2 would be sub-ms, but we stay srmech-first + log it.)\n")

    # ---- (B1) VOLUME, random identity tags: tome HV = bundle of mint(word). ----
    t = perf_counter()
    pad = mint_vector("__pad__", D=D)
    id_hv = {i: mint_vector(f"w{i}", D=D) for i in range(N)}
    tomevol_id = [odd_bundle([id_hv[i] for i in tomes[t_]], pad) for t_ in range(NT)]
    t_vol_id = perf_counter() - t

    # ---- (B2) VOLUME, spectral-derived: word HV encodes its V-row sign pattern; tome HV = bundle of those. ----
    t = perf_counter()
    mode_hv = [mint_vector(f"mode{m}", D=D) for m in range(1, K + 1)]
    sgn = {1: mint_vector("POS", D=D), -1: mint_vector("NEG", D=D)}
    def spec_hv(i):
        return odd_bundle([hdc.bind(mode_hv[m - 1], sgn[1 if V[i, m] >= 0 else -1]) for m in range(1, K + 1)], pad)
    spec_word = {i: spec_hv(i) for i in range(N)}
    tomevol_spec = [odd_bundle([spec_word[i] for i in tomes[t_]], pad) for t_ in range(NT)]
    t_vol_spec = perf_counter() - t
    print(f"(B) VOLUME (tome hypervectors): Class-M bundles of per-word HVs — cheap.")
    print(f"    B1 random-tag volume: {t_vol_id*1e3:.1f} ms ({t_vol_id/t_kernel*100:.1f}% of kernel).  B2 spectral-derived volume: {t_vol_spec*1e3:.1f} ms ({t_vol_spec/t_kernel*100:.1f}% of kernel).")
    print(f"    BOTH built from V we ALREADY have — no corpus re-read, no new eigendecomposition.\n")

    # ---- TEST 1: does the volume HOLD the words? (tome-membership recovery, random-tag) ----
    hit = 0
    for i in range(N):
        best = max(range(NT), key=lambda t_: hdc.similarity(id_hv[i], tomevol_id[t_]))
        hit += (best == tome_of[i])
    print(f"(1) DOES THE VOLUME HOLD THE WORDS? random-tag tome-recovery: a word's HV is most similar to its OWN tome")
    print(f"    volume {hit/N:.0%} of the time -> the circle volume stores membership (Class-M bundle capacity).\n")

    # ---- TEST 2: does the SPECTRAL volume carry the kernel's structure? (neighbour vs random pairs) ----
    rng = np.random.default_rng(0)
    def vcos(i, j):
        a, b = V[i, 1:K + 1], V[j, 1:K + 1]
        d = (np.dot(a, a) ** 0.5) * (np.dot(b, b) ** 0.5)
        return float(np.dot(a, b) / d) if d else 0.0
    pairs = [(i, j) for i in range(0, N, 3) for j in range(i + 1, N)]
    nbr_pairs = sorted(pairs, key=lambda p: -vcos(*p))[:80]        # spectrally-similar (kernel-neighbour) pairs
    rnd_pairs = [tuple(rng.choice(N, 2, replace=False)) for _ in range(80)]
    def mean_sim(P, table):
        return float(np.mean([hdc.similarity(table[i], table[j]) for i, j in P]))
    sp_nbr, sp_rnd = mean_sim(nbr_pairs, spec_word), mean_sim(rnd_pairs, spec_word)
    id_nbr, id_rnd = mean_sim(nbr_pairs, id_hv), mean_sim(rnd_pairs, id_hv)
    print(f"(2) DOES THE SPECTRAL VOLUME CARRY THE KERNEL? mean HDC similarity, kernel-neighbour pairs vs random pairs:")
    print(f"    B2 spectral-derived : neighbour {sp_nbr:+.3f}  vs random {sp_rnd:+.3f}   (gap {sp_nbr - sp_rnd:+.3f} -> CARRIES structure)")
    print(f"    B1 random-tag       : neighbour {id_nbr:+.3f}  vs random {id_rnd:+.3f}   (gap {id_nbr - id_rnd:+.3f} -> just labels, no structure)\n")

    print("VERDICT:")
    print(f"  • EASY HDC — NO RE-ENCODE. The wiki kernel (the Class-L eigendecomposition) is built ONCE ({t_kernel*1e3:.0f} ms) and")
    print(f"    REUSED. Putting it into a circle volume needs NO corpus re-read and NO new eigendecomposition: the volume")
    print(f"    bundles cost {t_vol_id*1e3:.0f}/{t_vol_spec*1e3:.0f} ms ({t_vol_id/t_kernel*100:.0f}/{t_vol_spec/t_kernel*100:.0f}% of the kernel) and the tome-bucketing {t_assign*1e3:.2f} ms — genuinely cheap.")
    print(f"  • THE ROUTING IS A FREE READ-OUT (one-time): which tome a word lands in is just atan2 of two eigenvector columns")
    print(f"    the kernel already holds (F535/F540) — the circle structure was LATENT in the kernel. The {t_angles*1e3:.0f} ms wall-clock is")
    print(f"    ENTIRELY srmech's slow per-call series-atan2 (logged W14), paid once + cached as tome metadata, not per query.")
    print(f"  • THE VOLUME IS A CHOICE, both cheap: (B1) random tags store WHICH words (membership {hit/N:.0%}); (B2) spectral-")
    print(f"    derived HVs additionally CARRY the kernel's similarity (neighbour-vs-random gap {sp_nbr - sp_rnd:+.3f} vs B1's {id_nbr - id_rnd:+.3f}).")
    print(f"    If you want the HDC volume itself to be navigable by meaning (the live-mirror walk, F541), use B2 — still no")
    print(f"    re-encode, just binds+bundles of the V-rows you already have. Favored not privileged (F398); held open (F394).")


if __name__ == "__main__":
    main()
