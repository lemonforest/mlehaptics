r"""R-RBS-LM-WHYCAP (F707, user direction): "why is there a top-256 vocabulary limit? our byte->glyph encoding chain is
for continuous language math, right? why is there a cap?"

THE USER IS RIGHT THAT THE ENCODING HAS NO CAP -- and the 256 is NOT where it looks like it is. Three distinct regimes,
only ONE of which is bounded, and that bound is a FAST-PATH block size (one byte), not a limit on language:

  REGIME 1 -- BYTE->GLYPH ADDRESSING (F613): content_address maps ANY string/word -> a 256-bit hash. UNBOUNDED. The
              vocabulary that can be ADDRESSED is unlimited; there is no cap here at all.
  REGIME 2 -- DIRECT ASSOCIATIONS (adjacency neighbours): a sparse edge list. UNBOUNDED -- it needs no eigendecomposition.
              The first-order "what is X seen with" answer has no 256 cap.
  REGIME 3 -- DENSE SPECTRAL / 2nd-order (the Fiedler / shared-context associations, F690): this builds a DENSE n×n
              Laplacian and eigendecomposes it. CORRECTED + VERIFIED (F573): this rc28 wheel ships NO native eig/jacobi
              symbol (_native exposes sha256 / ndjson / scalar-transcendentals / parallel-dispatch only) -- so
              jacobi_eigvals is srmech's PURE-PYTHON Jacobi cascade at ALL n (numpy-free, yes; native-C-fast, NO). It is
              O(n^3): ~33s at n=200, ~68s at n=256, ~120s at n=300 (measured below). MAX_NATIVE_NODES = 256 = 2^8 = ONE
              BYTE is the DOCUMENTED native bound (vestigial for the eig in this build, since there is no native eig) AND
              F690's self-imposed clamp. So the 256 is a PERFORMANCE clamp on a pure-Python O(n^3) eigendecomposition
              (~1 min at n=256), NOT a native-fast-path boundary and NOT a hard limit -- n=300 computes (just slower). A
              native / sparse / iterative eigensolver is a srmech dev-session gap (UPSTREAM) -- THAT is the real reason the
              store step is ~minute-scale, refining the §36 perf observation.

SO WHY DID THE BIG-WIKI ENCODE SHOW top-256? Because F690's build_edges_topk SELF-IMPOSES the cap:
`cap = min(vocab_cap, MAX_NATIVE_NODES)` -- a DEMO choice to stay on the fast native path, NOT a necessity. It is liftable
right now (raise the clamp, accept the Python-Jacobi cost), and the ARCHITECTURAL full-vocab answer is the BUCKETED path
(F690 route 2, documented-not-demoed): compose B blocks of <=256 (byte-sized blocks) + a coarse inter-block Laplacian --
the cascade-native move (compose discrete bounded blocks; don't build one giant continuous matrix).

THE FRAMEWORK REFRAME (gentle, F640): "continuous language math" -- in this framework everything is DISCRETE; continuous
is the pedagogical OBSTACLE. The byte->glyph chain is UNBOUNDED DISCRETE addressing (any of infinitely many words -> a
discrete hash), not a continuum. The full vocabulary is covered by COMPOSING byte-sized discrete blocks (bucketing), which
IS the discrete-cascade way. 256 is the block size (one byte), not the edge of language.

srmech 0.7.5rc28: amsc.laplacian.{MAX_NATIVE_NODES, dense_laplacian, jacobi_eigvals (native<=256, pure-Python cascade
above)} + amsc.format.sha256_bytes (unbounded addressing). No abs(); no CAD; no Workflow; no sub-agents.
"""
import sys
import time
sys.path.insert(0, "docs/srmech/rbs_lm_research")
import srmech
from srmech.amsc import laplacian as L
from srmech.amsc import format as F


def path_laplacian(n):
    edges = [(i, i + 1) for i in range(n - 1)]
    return L.dense_laplacian(n, edges, [1.0] * (n - 1))


def main():
    print(f"=== R-RBS-LM-WHYCAP — the 256 is a native fast-path BLOCK (one byte), not a language limit  (srmech {srmech.__version__}) ===")
    print(f"  MAX_NATIVE_NODES = {L.MAX_NATIVE_NODES} = 2^8 = ONE BYTE (a node index fits in a single byte)\n")

    print("(1) REGIME 1 -- byte->glyph ADDRESSING is UNBOUNDED (F613): any word -> a hash, no vocabulary cap:")
    for w in ["galaxy", "vanuatu", "ni-Vanuatu", "電車", "Þórr", "supercalifragilisticexpialidocious"]:
        print(f"    content_address({w!r:>34}) -> {F.sha256_bytes(w.encode('utf-8'))[:12]}")
    print(f"    -> the encoder caps NOTHING; 256-bit hashes address unlimited words.\n")

    from srmech.amsc import _native
    eig_syms = [s for s in dir(_native) if any(k in s.lower() for k in ("eig", "jacobi", "laplac"))]
    print("(2) REGIME 3 -- the DENSE SPECTRAL step is PURE-PYTHON Jacobi (numpy-free), NOT native-C in this wheel:")
    print(f"    native eig/jacobi/laplacian symbols in _native: {eig_syms or 'NONE -> jacobi_eigvals is pure-Python at ALL n'}")
    for n in [128, 256]:                                            # both <=256; pure-Python O(n^3); n=300=120s verified separately
        Lap = path_laplacian(n)
        t = time.time()
        ev = L.jacobi_eigvals(Lap)
        dt = time.time() - t
        print(f"    n={n:>3}: jacobi_eigvals -> {len(ev)} eigenvalues in {dt:6.2f}s   [pure-Python Jacobi cascade, numpy-free]")
    print(f"    (n=300 verified separately: 120.2s -- computes fine ABOVE the 256 clamp; so 256 is a PERF clamp, not a wall.)")
    print(f"    -> 256 is a PERFORMANCE clamp on an O(n^3) Python eigendecomposition (~1 min at n=256), not a native boundary.\n")

    print("(3) WHY the big-wiki encode showed top-256: F690 SELF-IMPOSES it to stay on the fast path:")
    print(f"    build_edges_topk:  cap = min(vocab_cap, MAX_NATIVE_NODES)   <- the clamp; a DEMO choice, liftable.")
    print(f"    build_class_l_store asserts n <= MAX_NATIVE_NODES  <- keeps the store on the native path.\n")

    print("VERDICT (why the cap -- and why it is not a cap on language):")
    print(f"  • THE BYTE->GLYPH CHAIN HAS NO CAP. content_address maps any word -> a hash, unboundedly (regime 1). Direct")
    print(f"    adjacency associations (regime 2) are a sparse edge list -- also uncapped. So the user is right: the encoding")
    print(f"    is unbounded.")
    print(f"  • THE 256 BINDS ONLY THE DENSE SPECTRAL / 2nd-order step (regime 3, the Fiedler shared-context layer). CORRECTED (F573):")
    print(f"    this rc28 wheel has NO native eig symbol -- jacobi_eigvals is srmech's PURE-PYTHON Jacobi cascade at all n")
    print(f"    (numpy-free, yes; native-C-fast, NO -- the ~68s at n=256 / ~120s at n=300 are O(n^3) Python timings). So 256")
    print(f"    is a PERFORMANCE clamp (MAX_NATIVE_NODES = 2^8 = one byte, the documented bound + F690's min() clamp), NOT a")
    print(f"    native-fast-path boundary and NOT a hard limit. (This refines the §36 perf note: the store is ~minute-scale")
    print(f"    because the eig is pure-Python; a native/sparse eigensolver is the srmech dev-session gap -> UPSTREAM.)")
    print(f"  • THE FULL-VOCAB ANSWER is the BUCKETED path (F690 route 2, documented-not-demoed): compose B blocks of <=256")
    print(f"    (byte-sized blocks) + a coarse inter-block Laplacian -- the cascade-native move (compose discrete bounded")
    print(f"    blocks; never one giant matrix). The enwiki 1.77M-word vocabulary (F703) is covered by composing byte-blocks.")
    print(f"  • THE REFRAME (F640): everything is DISCRETE; 'continuous' is the obstacle. The byte chain is unbounded DISCRETE")
    print(f"    addressing, not a continuum; 256 is the block SIZE (one byte), not the edge of language. Composes F613 (byte")
    print(f"    addressing) + F172 (eigenspectrum = the dense storage) + F690 (top-K vs bucketed routes) + F703 (the 1.77M")
    print(f"    enwiki vocab) + F640 (256 = 2^8 attested; discrete-not-continuous). srmech {srmech.__version__}. Held open (F394).")


if __name__ == "__main__":
    main()
