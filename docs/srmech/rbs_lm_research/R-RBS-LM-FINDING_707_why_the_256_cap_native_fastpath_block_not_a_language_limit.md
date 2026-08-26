# Finding 707 — why the top-256 cap? It's a performance clamp on a pure-Python eigendecomposition, not a language limit

**Script:** `R-RBS-LM-WHYCAP_the_256_is_a_native_fastpath_block_not_a_language_limit.py`
**Status:** VERIFIED — and it corrects an earlier overclaim (srmech 0.7.5rc28)
**User direction:** *"why is there a top-256 vocabulary limit? our byte→glyph encoding chain is for continuous language
math, right? why is there a cap?"*

## You're right that the encoding is uncapped — the 256 is somewhere else entirely

There are **three distinct regimes**, and only one is bounded:

| regime | what | cap? |
|---|---|---|
| **1 — byte→glyph addressing** (F613) | any word/string → a 256-bit content hash | **none** — addresses unlimited words (verified: galaxy/vanuatu/電車/Þórr all hash) |
| **2 — direct associations** (adjacency neighbours) | a sparse edge list; "what is X seen with" | **none** — needs no eigendecomposition |
| **3 — dense spectral / 2nd-order** (Fiedler / shared-context, F690) | builds a dense n×n Laplacian + eigendecomposes | **256** — but see below |

So the byte→glyph chain caps nothing. The 256 binds **only** the dense spectral step.

## The correction (F573): the cap is a perf clamp on *pure-Python* Jacobi — there is no native eig in this build

I'd been calling the eigendecomposition the "native C path." **That was wrong, and I verified it:** `srmech.amsc._native`
exposes `sha256_*` / `ndjson` / scalar-transcendentals (`sin/cos/exp/log/atan/sqrt`) / `parallel_sector_dispatch` —
**no `eig` / `jacobi` / `laplacian` symbol at all**. So `jacobi_eigvals` runs as srmech's **pure-Python Jacobi cascade** at
*every* n in this rc28 wheel. The measured timings confirm it (O(n³), Python-shaped):

| n | time | path |
|---|---|---|
| 200 | 33 s | pure-Python Jacobi (numpy-free) |
| 256 | 68 s | pure-Python Jacobi (numpy-free) |
| 300 | 120 s | pure-Python Jacobi (numpy-free) — **computes fine above the clamp** |

- **numpy-free is true** (the user's rc28 description holds — no numpy in the env; the Jacobi is srmech's own cascade).
- **"native-C-fast for the eig" is false** in this wheel — there's no native eig symbol, so the ~45–68 s "store" cost
  (and the §36 perf observation) is simply pure-Python O(n³) Jacobi. This **corrects** the "native eigvals" phrasing in
  F703.

So **`MAX_NATIVE_NODES = 256 = 2⁸ = one byte`** is (a) the *documented* native bound (vestigial for the eig here, since no
native eig exists) and (b) F690's *self-imposed* clamp (`cap = min(vocab_cap, MAX_NATIVE_NODES)` + a `build_class_l_store`
assert). It is a **performance clamp** that keeps the pure-Python eigendecomposition to ~1 minute — **not** a native-fast-path
boundary, and **not** a hard limit (n=300 computes in 120 s).

## How the cap lifts (three ways, none of which touch the encoder)

1. **Skip the eig for direct associations** — regime 2 is uncapped; only the second-order Fiedler layer needs the dense eig.
2. **Bucket** (F690 route 2, documented-not-demoed) — compose B blocks of ≤256 (byte-sized blocks) + a coarse inter-block
   Laplacian. The cascade-native move: compose discrete bounded blocks, never one giant matrix. This covers the full
   1.77M-word enwiki vocabulary (F703).
3. **A native / sparse / iterative eigensolver** — the real srmech perf gap (logged UPSTREAM). A native Lanczos/Jacobi or a
   sparse solver would make large-n spectral feasible directly.

## The reframe (F640)

"Continuous language math" — in this framework everything is **discrete**; *continuous* is the pedagogical obstacle. The
byte→glyph chain is **unbounded discrete addressing** (any of infinitely many words → a discrete hash), not a continuum. The
256 is the **block size** (one byte), not the edge of language; the full vocabulary is covered by **composing byte-sized
discrete blocks** (bucketing) — which *is* the discrete-cascade way.

**Composes:** F613 (byte addressing — uncapped) · F172 (eigenspectrum = the dense storage) · F690 (top-K vs bucketed routes;
the self-imposed clamp) · F703 (the 1.77M-word enwiki vocab; **corrects** its "native eigvals" phrasing) · F640 (256 = 2⁸
attested; discrete-not-continuous) · F573 (the overclaim caught + corrected). srmech 0.7.5rc28. Held open (F394).

*Reference scaffold; not a package edit. The native-eig gap is logged for UPSTREAM (extends §36).*
