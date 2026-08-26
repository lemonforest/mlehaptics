# `srmech_bone/` — scaffold for the srmech Claude-Code dev session: bind the native A-N ops + the Klein-4 quad-stream

**For a Claude Code session working INSIDE the srmech package.** Everything below is answered + proven; lift it in.
**Findings:** F708 (the diagnosis) · F710 (the ctypes-binding reference, proven) · UPSTREAM_NOTES §37/§38.
**Reference code to lift:** `../R-RBS-LM-NATIVEBIND_reference_ctypes_bindings_for_the_unbound_A_N_symbols.py` (the exact
`_bind` argtypes/restype + a passing test for every symbol).

## The problem (one sentence)

The native `libsrmech.so` **exports the full A-N foundation** (119 symbols incl. `srmech_jacobi_eigvals`,
`srmech_graph_dense_laplacian`, `srmech_hdc_*`, `srmech_klein4_*`, `srmech_cascade_parallel_sector_dispatch`), but the
Python ctypes shim **binds only ~13**, and `laplacian.jacobi_eigvals` "falls back to numpy unconditionally" — so the
numpy-free install runs the **pure-Python Jacobi (68 s)** instead of the native symbol (**1.4 s, ~49×**) sitting in the
loaded `.so`. The cascade math (word-association / the_one) therefore ran a slow, off-thesis Class-L dense-eig instead of
the fast native HDC / Klein-4 ops.

**Proven (F710, all numpy-free, via ctypes into the shipped `.so`):** `jacobi_eigvals` 1.5 s @ n=256 (~45× the wrapper);
`graph_dense_laplacian` correct; `hdc_similarity` identical/complement/random = +1/−1/~0; `klein4_bind`+`klein4_similarity`
self=1, random≈0.25; `parallel_sector_dispatch` symbol bound (`SRMECH_PARALLEL_SECTOR_CAP = 4`).

## Dev-session tasks (in order)

1. **`srmech/amsc/_native.py` — bind the symbols.** Add the argtypes/restype for `srmech_jacobi_eigvals`,
   `srmech_graph_dense_laplacian`, `srmech_graph_normalized_laplacian`, `srmech_hermitian_eigendecompose(_ws)`,
   `srmech_hdc_{bind,bundle,permute,similarity}`, `srmech_klein4_{bind,bundle,similarity,triality_cycle}` — **lift the
   `bind()` function from R-RBS-LM-NATIVEBIND verbatim** (signatures are exact, from `c/include/srmech.h`). Expose `*_c`
   wrappers like the existing `sha256_hex_c`. **ABI stays 3** (additive — no wire-format change).
2. **`srmech/amsc/laplacian.py` — dispatch numpy-free.** Make `jacobi_eigvals` / `dense_laplacian` call the native symbol
   when `HAS_NATIVE`, marshalling the matrix from a Python `list` → `(c_double * n*n)` (numpy NOT required — proven in
   F710). Delete the "falls back to numpy unconditionally" branch. Keep the `n ≤ MAX_NATIVE_NODES` guard for the dense
   block only.
3. **`srmech/amsc/hdc.py` — dispatch HDC/Klein-4 to native.** Route `hdc.similarity`/`bind`/`bundle` and
   `klein4_{bind,bundle,similarity}` to the native symbols when `HAS_NATIVE`.
4. **`srmech/amsc/cascade.py` — the Klein-4 quad-stream as the ≤1024 spectral.** Wire `parallel_sector_dispatch`
   (`SRMECH_PARALLEL_SECTOR_CAP = 4`) so a Class-L spectral job buckets into **4 × ≤256 = 1024** nodes across the four
   Klein-4 sectors — the "threaded Klein-4 streams" the user has raised throughout. (This is *also* the >256-vocab
   bucketed path: B blocks of ≤256, quad-streamed.)
5. **The architectural shift (the on-thesis route).** The word-association / the_one coupling should compose **Class-M HDC
   + Klein-4** (native `hdc_*`/`klein4_*`) bound through the_one, with the **Class-L spectral** (native eig, quad-streamed)
   as the second-order layer — **not** a pure-Python dense-eig. Class-L (graph spectral) and Class-M (HDC) are
   complementary; the native bindings make both fast.

## Verification

Run `python R-RBS-LM-NATIVEBIND_*.py` after the bindings land (it calls the same symbols) — every line should read `OK` /
the expected values, and `jacobi_eigvals` should be sub-2 s at n=256. Add a pytest mirroring it (parity vs the pure-Python
fallback + the JPL-clean ratchet). TestPyPI-rc before the clean tag (project discipline).

## Where this came from (research side, already done)

`R-RBS-LM-WIKIKERNEL.build_edges_topk` no longer clamps the vocabulary to 256 (F708 — that clamp was pre-encode
quantization); the 256 bounds only the dense-eig block. The Story-Teller prose lives/dies on the uncapped kernel (F709).
This bone is the *srmech-side* half: make the native foundation actually callable so the spectral layer is fast + on-thesis.
