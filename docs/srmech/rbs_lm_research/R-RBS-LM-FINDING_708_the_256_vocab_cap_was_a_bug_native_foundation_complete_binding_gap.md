# Finding 708 — the top-256 vocab cap was a BUG (pre-encode quantization); the native A-N foundation is complete; the gap is a Python binding layer

**Scripts:** `R-RBS-LM-UNCAPPED_*.py` (the fix, proven) + `R-RBS-LM-WHYCAP_*.py` (F707) + the diagnostic probes
**Status:** VERIFIED — and it is a self-correction the user forced (srmech 0.7.5rc28)
**User (verbatim, the barrage):** *"why are you trimming big wiki before encode? … why are we quantizing it before
encoding?"* · *"i said a long time ago to attest magic numbers. what else have you tried to conceal from us?"* · *"there
are more than 256 words in a child's dictionary"* · *"that looks like a bug we ignored and treated it like canon"* · *"why
couldn't you make a quad stream of that for 1024 … threaded klein4 streams?"* · *"why you accepted it without question?"* ·
*"cascade math isn't using HDC operations with the_one kernel?"* · *"how to get missing native symbols for A-N operations?
this sounds foundational"* · *"is pypi not shipping native dll?"*

The user is right on every point. This finding is the honest accounting + the fix.

## 1. The top-256 was a BUG treated as canon — and it was pre-encode quantization

`build_edges_topk` did `cap = min(vocab_cap, MAX_NATIVE_NODES)` — it clamped the **vocabulary** to 256 before encoding.
That is **pre-encode quantization**: throwing away 1.77M words to keep 256, the exact opposite of the project's
unquantized-structural thesis (F49/F50). I accepted it as canon and even **rationalized** it ("256 = 2⁸ = one byte") — the
precise opposite of the no-magic-number discipline (F640). **Fixed:** the vocab is no longer clamped (`vocab_cap=None`
keeps all words; 256 bounds only the *dense-eig block*, never the vocabulary or the adjacency).

**Proven (R-RBS-LM-UNCAPPED, 20k simplewiki articles, uncapped):** **157,444 words** kept (0 dropped), 6.28M sparse edges,
121 s — and the words the cap threw away are real anchors again: `planet`→earth/solar/system/dwarf/sun ·
`church`→catholic/roman/orthodox · `ocean`→atlantic/pacific/sea/indian · `energy`→potential/heat/mass/light/matter ·
`mathematics`→number/logic/study. **Direct associations need no eigendecomposition** → a sparse adjacency lookup, uncapped,
at any vocab size.

## 2. The native A-N foundation is COMPLETE — the gap is the Python binding layer (not PyPI, not the C)

The user's foundational questions, answered with facts:

- **"is pypi not shipping native dll?"** — PyPI **is** shipping it: `srmech/_native/libsrmech.so`, **119 `srmech_` symbols**.
- **"how to get missing native symbols for A-N?"** — They are **not missing from the binary.** `nm -D` shows
  `srmech_jacobi_eigvals`, `srmech_graph_dense_laplacian`, `srmech_hermitian_eigendecompose`, `srmech_hdc_{bind,bundle,
  similarity,permute}`, `srmech_klein4_{bind,bundle,similarity,triality_cycle}`, `srmech_cascade_parallel_sector_dispatch`,
  `srmech_cyclic_period`, `srmech_is_prime`, … The whole A-N foundation is in the C library. **The gap is that the Python
  ctypes shim (`_native.py`) only *binds* 13 `_c` symbols** (sha256/ndjson/transcendentals/sector-dispatch), and
  `laplacian.jacobi_eigvals` "falls back to numpy unconditionally" — so with **numpy absent** (the numpy-free `srmech`
  install) it runs the **pure-Python Jacobi cascade**, never calling the native symbol that is right there in the loaded
  `.so`.
- **PROVEN:** calling `LIB.srmech_jacobi_eigvals` directly via ctypes (n=256) runs in **1.4 s vs the wrapper's 68 s — ~49×
  faster**, correct eigenvalues. So the foundation works; only the wrapper wasn't using it. This **corrects F707's** "no
  native eig" wording — there *is* one; it just isn't bound/dispatched in the numpy-free path.

## 3. The Klein-4 quad-stream the user kept raising = the answer, and it's already native

`srmech_cascade_parallel_sector_dispatch` is native **and bound** (`cascade_parallel_sector_dispatch_c`). Four Klein-4
sectors × 256 = **1024** for the spectral layer, natively, right now. I never connected the **threaded-Klein-4 streams** the
user raised repeatedly to the 256 cap — that miss is on me. The bucketed/blocked spectral path (F690 route 2) *is* the
quad-stream.

## 4. "cascade math isn't using HDC with the_one?" — correct catch

The word-association path used the **Class-L dense Laplacian eig** (and pure-Python at that), **not** the native HDC /
Klein-4 ops (`srmech_hdc_*` / `srmech_klein4_*`) — which exist in the `.so` but are also unbound in the shim. So "cascade
math uses HDC with the_one" was not holding for this path. The native HDC/Klein-4 ops are the faster, on-thesis route and
should be bound + used.

## What I will carry forward (the discipline I lapsed)

Questioning every cap / magic number / pre-encode lossy step is the project's **core method across every scale** (the user:
*"these are all questions we've been asking the entire time"*). I rationalized limitations as canon (the 256 cap, the
"native eigvals" label). The fix is not a one-off: **attest or question every constant; never quantize the input; check the
binary, not the wrapper's bound names.**

## Upstream asks (the foundational fix) — logged §38

Bind the native A-N symbols in `_native.py` (`srmech_jacobi_eigvals`, `srmech_graph_dense_laplacian`, `srmech_hdc_*`,
`srmech_klein4_*`) and wire `laplacian`/`hdc` to dispatch to them **numpy-free** (the ctypes call works without numpy — the
matrix marshals from a Python `list`/`bytes`, as the direct ctypes proof shows). Then the eig is ~49× faster, the HDC/Klein-4
ops run native, and the Klein-4 quad-stream gives 1024-node spectral blocks. The C foundation is done; only the Python
wrapper under-uses it.

**Composes:** F49/F50 (no quantization) · F640 (no-magic / question the constant) · F690 (the kernel, clamp removed) · F707
(corrected) · F132/Klein-4 (the quad-stream) · F683/F684 (the_one coupling, HDC). srmech 0.7.5rc28. Held open (F394).
