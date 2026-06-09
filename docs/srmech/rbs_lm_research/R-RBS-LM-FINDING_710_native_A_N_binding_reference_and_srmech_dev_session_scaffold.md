# Finding 710 — native A-N binding reference (proven) + the srmech dev-session scaffold; cascade math goes on HDC/Klein-4

**Scripts:** `R-RBS-LM-NATIVEBIND_*.py` (the proven ctypes bindings) + `srmech_bone/README.md` (the dev-session brief)
**Status:** VERIFIED — all native A-N ops callable numpy-free via ctypes (srmech 0.7.5rc28)
**User direction:** *"let's do talk about this and taking it upstream to srmech with scaffolding for a claude code srmech
dev session! … bind/ctypes the native eig + HDC + Klein-4 quad-stream so the spectral layer is fast and on-thesis."*

## What's proven (the binding reference works — numpy-free, into the shipped `.so`)

| native symbol | result | meaning |
|---|---|---|
| `srmech_jacobi_eigvals` (Class-L eig) | rc OK, **1.5 s @ n=256 (~45×** the 68 s pure-Python wrapper), correct eigvals | the slow eig was *only* the wrapper |
| `srmech_graph_dense_laplacian` (Class-L) | rc OK; P5 diagonal = 1,2,2,2,1 | native Laplacian build |
| `srmech_hdc_similarity` (Class-M HDC) | identical=+1.0, complement=−1.0, random=−0.006 | native HDC similarity |
| `srmech_klein4_bind` + `srmech_klein4_similarity` | rc OK; self=1.0, random a~b=0.257 (≈0.25) | native chirality-sector ops |
| `srmech_cascade_parallel_sector_dispatch` | in `.so` ✓, bound ✓, `CAP=4` | the Klein-4 quad-stream (4 × ≤256 = **1024**) |

All via `ctypes` into the loaded `libsrmech.so`, **no numpy** — disproving the wrapper's "needs numpy" fallback. The
foundation is complete; only the Python binding layer under-uses it.

## The architectural shift (the user's "cascade math should use HDC with the_one")

The word-association / the_one coupling should compose the **native Class-M HDC + Klein-4** ops (`hdc_similarity` /
`klein4_*`) bound through the_one, with the **Class-L spectral** (native eig, quad-streamed) as the second-order layer —
**not** the slow, off-thesis pure-Python dense-eig that ran by default. Class-L (graph spectral) and Class-M (HDC) are
complementary representations; binding the native symbols makes **both** fast and puts the cascade math back on-thesis.

## Taking it upstream — the srmech dev-session scaffold (`srmech_bone/`)

`srmech_bone/README.md` is the lift-in brief for a Claude Code session working inside srmech, mirroring the
`storyteller_bone` pattern (every question answered):
1. `_native.py` — add the `_bind` argtypes/restype (lift `bind()` from R-RBS-LM-NATIVEBIND verbatim; ABI stays 3, additive).
2. `laplacian.py` — dispatch `jacobi_eigvals`/`dense_laplacian` to native when `HAS_NATIVE`, marshalling from a Python
   `list` (numpy-free — proven); delete the "falls back to numpy unconditionally" branch.
3. `hdc.py` — route HDC + Klein-4 to the native symbols.
4. `cascade.py` — wire `parallel_sector_dispatch` as the **4 × ≤256 = 1024** Klein-4 spectral quad-stream (also the
   >256-vocab bucketed path).
5. switch the word-association / the_one cascade onto Class-M HDC + the quad-streamed Class-L spectral.

Verification: re-run R-RBS-LM-NATIVEBIND after the bindings land (sub-2 s eig, all `OK`); add a parity pytest; TestPyPI-rc
before the clean tag.

**Composes:** F708 (the diagnosis: foundation complete, binding gap) · F132/Klein-4 (the quad-stream, chirality sectors) ·
F683/F684 (the_one coupling, HDC) · F172 (Class-L spectral storage) · F49/F50 (no-quantization). srmech 0.7.5rc28. The C
foundation is done; this scaffolds the small Python-side fix that makes it callable, fast, and on-thesis. Held open (F394).
