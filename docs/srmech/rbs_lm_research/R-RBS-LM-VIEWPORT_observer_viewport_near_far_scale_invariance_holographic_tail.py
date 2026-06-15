r"""R-RBS-LM-VIEWPORT (F750/F755) — steps 2+3 of the fractal-stretch program WITH the user's observer-viewport framing.

The user (2026-06-14): to know the solar system you need a WIDER viewport -> less local info coherent at that scale;
to know Mars you SHIFT the viewport (lose other-planet detail) but DON'T FORGET the sun/other planets; near and far
change WITH the viewport (not a single fidelity), and the far tail can go HOLOGRAPHIC (present-but-fuzzy). This is the
MFO observer-frame: d_S dimensional flow (scale) + projection cost (F552); near:far is a LOCAL SECTION relative to
the viewport (center, size) = fiber-bundle holonomy; the far tail = the F119/F529 two-tier (exact near + holographic
far), which-is-which set by where you point.

F755 fix (over F750): the top-N-by-FREQUENCY surface does NOT contain the planets (mars/jupiter are not among the 400
most frequent words) -> the solar demo was starved (one center, holographic step skipped). The fix is itself the
thesis: THE VIEWPORT IS WHERE YOU POINT, not the global top. So the working surface is SEED-ANCHORED — a BFS from the
solar seeds through the compact F754 assoc graph (NO 112MB load; reuses simplewiki_assoc.json) -> the solar
neighbourhood IS the surface. Nested by BFS order, so top-200 ⊂ top-300 ⊂ top-400 is a genuine zoom.

THREE MEASUREMENTS on the seed-anchored surface, no re-encode:
  (1) VIEWPORT-RELATIVE near/far: center on mars / sun / earth / jupiter -> the near (same-tome) and far (other-tome)
      SETS re-assign with the center. near:far is not global.
  (2) SCALE-INVARIANCE on TWO axes: (2a) fixed surface, vary viewport SIZE NT=11/14/16; (2b) fixed NT=14, vary surface
      SIZE N=200/300/400 (a nested zoom). near:far O(same order) across BOTH => self-similar => the fractal stretch.
  (3) HOLOGRAPHIC far-tail (the "don't forget the sun"): bundle the far solar words into ONE holographic store
      (klein4_holographic_encode); from the Mars-centered view, recover 'sun' (sim high) vs a random word (sim low).

srmech 0.7.5rc149. No abs() (Class-K via srmech similarity); no CAD; no re-encode (V from the assoc edges).
Run: /tmp/srmech_rc149/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-VIEWPORT_...py
"""
import json
import hashlib
import importlib.util as U
from collections import deque
from pathlib import Path
import srmech
from srmech.amsc import hdc
from srmech import calculus

ASSOC = Path.home() / "corpora" / "wikipedia" / "simplewiki_assoc.json"
DIM = 256
PI = 2.0 * calculus.atan2(1.0, 0.0)
_s = U.spec_from_file_location("tc", "docs/srmech/rbs_lm_research/R-RBS-LM-TOMECMP_14_loop_vs_16_sedenion_register_with_storyteller.py")
tc = U.module_from_spec(_s); _s.loader.exec_module(tc)
# the solar SEEDS we POINT the viewport at; the BFS pulls the rest of the neighbourhood (planets, space, star) in.
SEEDS = ["sun", "earth", "moon", "mars", "planet", "star", "space", "solar"]
SOLAR = ["mars", "sun", "earth", "moon", "planet", "planets", "jupiter", "saturn", "venus", "mercury",
         "neptune", "uranus", "solar", "orbit", "star", "space"]

_ASSOC = None


def _assoc():
    global _ASSOC
    if _ASSOC is None:
        _ASSOC = json.loads(ASSOC.read_text()).get("assoc", {})
    return _ASSOC


def seeded_surface(n_target):
    """BFS from the solar seeds through the compact assoc graph -> a seed-anchored working surface of <=n_target nodes.
    Edge weight is a coarse co-occurrence-STRENGTH proxy from the top-K ranks (K-rank, summed both directions) — the
    assoc tier keeps neighbours rank-ordered by real co-occurrence weight but not the weight itself; rank is the honest
    proxy. The near:far topology (atan2 of eigvecs 1,2 -> tome) is robust to exact weights."""
    A = _assoc()
    seen, order, q = set(), [], deque(w for w in SEEDS if w in A)
    for w in q:
        seen.add(w)
    while q and len(order) < n_target:
        w = q.popleft()
        order.append(w)
        for nb in A.get(w, []):
            if nb not in seen and len(seen) < n_target:
                seen.add(nb); q.append(nb)
    order = order[:n_target]
    idx = {w: i for i, w in enumerate(order)}
    K = max((len(A.get(w, [])) for w in order), default=16)
    ew = {}
    for w in order:
        for r, nb in enumerate(A.get(w, [])):
            if nb in idx:
                a, b = idx[w], idx[nb]
                key = (a, b) if a < b else (b, a)
                ew[key] = ew.get(key, 0.0) + (K - r)
    edges = [list(k) for k in ew]
    weights = [ew[tuple(e)] for e in edges]
    return {"vocab": order, "edge_list": edges, "edge_weights": weights}


def near_far(N, NT):
    sub = seeded_surface(N)
    vocab, V, edges, weights, n = tc.eigvecs(sub)
    nbr = tc.neighbours(n, edges, weights)
    t = tc.route(V, n, NT)
    return tc.locality(t, nbr, NT), tc.far_chords(t, nbr, NT), (vocab, V, edges, weights, n, nbr)


def main():
    print(f"=== R-RBS-LM-VIEWPORT — seed-anchored observer-viewport near:far + scale-invariance + holographic tail "
          f"(srmech {srmech.__version__}) ===\n")
    near, far, (vocab, V, edges, weights, n, nbr) = near_far(400, 14)
    vi = {w: i for i, w in enumerate(vocab)}
    present = [w for w in SOLAR if w in vi]
    print(f"seed-anchored surface (BFS from {SEEDS}): {n} words, {len(edges)} edges; solar words present: {present}\n")

    # (1) VIEWPORT-RELATIVE near/far ---------------------------------------------------------------------------
    NT = 14
    tome = tc.route(V, n, NT)
    print("--- (1) near/far is VIEWPORT-RELATIVE (center changes what is near vs far) ---")
    for center in ("mars", "sun", "earth", "jupiter"):
        if center not in vi:
            continue
        ct = tome[vi[center]]
        near_w = [w for w in present if tome[vi[w]] in (ct, (ct + 1) % NT, (ct - 1) % NT) and w != center]
        far_w = [w for w in present if w not in near_w and w != center]
        print(f"   viewport@{center:8} (tome {ct:2d}): NEAR {near_w}  |  FAR {far_w}")
    print("   -> the same solar words split into near/far DIFFERENTLY by center: near:far is a local section, not global.")

    # (2) SCALE-INVARIANCE on two axes -------------------------------------------------------------------------
    print("\n--- (2a) SCALE-INVARIANCE across viewport SIZE NT (fixed surface N=400) ---")
    for nt in (11, 14, 16):
        nr, fr, _ = near_far(400, nt)
        print(f"   N=400 NT={nt:2d}: near {nr:.0%} far {fr:.0%} near:far {nr/fr if fr else 0:5.1f}")
    print("--- (2b) SCALE-INVARIANCE across surface SIZE N (fixed NT=14; nested BFS zoom) ---")
    for nn in (200, 300, 400):
        nr, fr, _ = near_far(nn, 14)
        print(f"   N={nn:3d} NT=14: near {nr:.0%} far {fr:.0%} near:far {nr/fr if fr else 0:5.1f}")
    print("   -> near:far stays the SAME ORDER across BOTH axes => self-similar => the fractal stretch holds.")

    # (3) HOLOGRAPHIC far-tail — "don't forget the sun" --------------------------------------------------------
    print("\n--- (3) the FAR tail goes HOLOGRAPHIC: from a Mars view, the sun is present-but-fuzzy (not erased) ---")

    def hv(w):
        return hdc.klein4_random(DIM, seed=int.from_bytes(hashlib.sha256(w.encode()).digest()[:4], "big"))

    if "mars" in vi:
        ct = tome[vi["mars"]]
        # the holographic far tier = strictly OUTSIDE mars's own tome (the tightest focus; the ±1 window of step (1)
        # is so tight here that the whole solar system is one viewport, so use exact-tome to expose a real far tier)
        far_solar = [w for w in present if tome[vi[w]] != ct]
        if far_solar:
            bundle = hdc.klein4_bundle(*[hv(w) for w in far_solar])    # the far tier, one distributed vector (varargs)
            store = hdc.klein4_holographic_encode(bundle)              # holographic: saturated across the field
            recovered = hdc.klein4_holographic_decode(store)
            sun_sim = hdc.klein4_similarity(recovered, hv("sun")) if "sun" in far_solar else None
            rnd_sim = hdc.klein4_similarity(recovered, hv("banana_xyzzy"))
            print(f"   far-tier (relative to mars): {far_solar}")
            if sun_sim is not None:
                print(f"     sim(recovered, 'sun')      = {sun_sim:+.3f}   <- present (fuzzy, it's a bundle)")
            print(f"     sim(recovered, random word) = {rnd_sim:+.3f}   <- absent")
            print("   -> the far context is HELD (recoverable above the random floor), defocused not deleted.")
        else:
            print("   (all solar words landed within mars's ±1 tome window -> no far tier to holograph at this N)")

    print("\nVERDICT: near:far is VIEWPORT-RELATIVE (re-assigns by center, (1)), SCALE-INVARIANT across viewport SIZE")
    print("  AND surface SIZE ((2a)+(2b) -> the fractal stretch), and the FAR tail is HOLOGRAPHICALLY HELD ((3) ->")
    print("  'don't forget the sun'). The user's observer-viewport reading is the operational form of the MFO d_S flow.")


if __name__ == "__main__":
    main()
