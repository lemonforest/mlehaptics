# F292 — dev hand-down: optimize srmech's own C by grafting techniques from established reference implementations (the "apple-tree" method). Worked example: cpuminer SHA-256 CPU optimizations → srmech Class-A `sha256_bytes` + the block-diagonal native ops. Energy/perf-engineering scope; crypto/mining OUT.

> **SCOPE (load-bearing):** this is **performance-engineering of srmech's own C library**, measured in **energy-per-op** (on-brand for srmech's microcontroller/edge story), NOT cryptocurrency mining. The reference codebase (`cpuminer`) is read **only as a source of generic CPU-optimization *techniques***; no mining logic, no crypto-attack content, no capability material is transferred. The `btc-rosetta` bench already established the honest boundary and it is carried in verbatim below: **binding does not make hashing cheaper; SHA-256 has no algebraic PoW shortcut; this is "a correct instrument, not a money printer."** CAD-ban N/A (this is algebra/C-perf, not fabrication geometry). MPM provenance attests each technique to **public references**, not to GPL code. No srmech package edits from this subtree — this is a hand-down; the dev decides what lands.

**Headline.** A method + a worked, measured example for the srmech dev. **The method ("apple-tree"):** for each srmech C hot path, identify the *established, battle-tested reference implementation* that is the canonical optimization tree for that operation-kind, and **graft the technique** onto srmech's own code — *apples-to-apples* when the op matches (cpuminer SHA-256 → srmech SHA-256), *apples-to-oranges* when only the optimization *pattern* transfers (cpuminer's N-way SIMD mindset → the block-diagonal `loop_bind_hd`). Every graft is re-implemented **JPL-clean** (techniques, not cpuminer's `goto`/asm/macro code) and must stay **bit-exact** to the scalar/Python fallback. **The one already-measured win** (btc-rosetta, RAPL on a Xeon E5530): SHA-256 **midstate = 1.73× / ~42% less energy per hash, byte-identical**. The two highest-value *broadly-applicable* grafts: an **N-way SIMD `sha256_batch`** (bulk attestation) and **SIMD-vectorizing `loop_bind_hd`** (its 256 independent dim-8 blocks are literally the N-way-parallel structure cpuminer exploits).

---

## §0 — The method: the "apple-tree" reference-implementation graft
srmech's open-by-architecture + no-external-dep + JPL-clean commitments mean we **cannot** just link a tuned library (no LAPACK, no FFTW, no asm blobs — that breaks microcontroller-readiness + the Power-of-Ten ratchet). So the optimization model is **graft the technique, keep srmech self-contained**:

1. **Pick the hot path** in srmech's C (profile-led; the candidates below are ranked by how often the op runs across AMSC).
2. **Find its established reference tree** — the mature, battle-tested app/library whose whole reason for existing is to make *that operation-kind* fast (cpuminer for SHA-256/integer-SIMD; the FFT literature for `autocorrelation`; the BLAS family's cache-blocking for dense Class-L).
3. **Classify the graft:** *apples-to-apples* (same op — copy the algorithm, re-impl JPL-clean) vs *apples-to-oranges* (different op, same pattern — transfer the structure).
4. **Re-implement under srmech's constraints** (§4) — intrinsics not asm, no new deps, bit-exact parity, ABI-safe.
5. **Attest to the public reference** (§5), with the reference app as a "we saw it work here" pointer.

This doc walks the method once, concretely, on the cpuminer→SHA-256 tree (§1–§2), then lists the open orchard (§3).

## §1 — Worked graft #1 (apples-to-apples): cpuminer SHA-256 → srmech Class-A `srmech_sha256.c` / `sha256_bytes`
srmech's Class-A SHA-256 is the foundational content-addressing op (`response_sha256`, `descriptor_hash`, `parser_rule_hash`, `kernel_cache_hash`, every attestation). cpuminer (`sha2.c`, GPLv2-or-later — see §5) carries the canonical CPU-tuned SHA-256: `sha256_transform` (scalar), `sha256d_ms` (midstate), `sha256d_ms_4way` (SSE2 4-way), `sha256d_ms_8way` (AVX2 8-way), 32-byte-aligned buffers, per-arch asm + `USE_AVX/AVX2` dispatch.

| technique (in cpuminer) | srmech target symbol | expected payoff | graft type |
|---|---|---|---|
| **N-way SIMD batch** (`sha256d_ms_4way/8way`) | NEW `sha256_batch(msgs[]) -> digests[]` behind `format.sha256_bytes` | **highest broadly-applicable win** — srmech hashes *many independent* records; 4-way (SSE2) / 8-way (AVX2) hashes them in lockstep | apples-to-apples |
| **SHA-NI** (`sha256rnds2`/`sha256msg1/2`) | `srmech_sha256.c` compression rounds | hardware SHA-256 round; large single-stream speedup where the CPU has the extension | apples-to-apples |
| **midstate** (`sha256d_ms`) | conditional fast path on `sha256_bytes` | **MEASURED 1.73× / 42% less energy** (btc-rosetta, RAPL) — but **only** for "hash many messages sharing a fixed prefix"; srmech's SHA-256 is *general* content-addressing, so this is a **specialized** path, flag as opt-in | apples-to-apples (conditional) |
| **32-byte alignment** (`__attribute__((aligned(32)))`) | the SHA state/block buffers | enables aligned SIMD loads; cheap, JPL-clean | apples-to-apples |
| **runtime CPU-feature dispatch** + scalar fallback | new dispatch tier under `_native` | portability; srmech's `HAS_NATIVE`→pure-Python fallback **already models this** — the SIMD tier slots in as one more level | structural |

**Honest payoff note:** midstate is real but specialized; **`sha256_batch` is the win that pays off across all of AMSC** (bulk attestation is the common case). SHA-NI is a big single-stream win where present, gated behind dispatch.

## §2 — Worked graft #2 (apples-to-oranges, the on-theme gem): cpuminer's N-way SIMD *mindset* → `loop_bind_hd`
The single most apt cross-fruit graft. **`loop_bind_hd` is the direct sum ⊕ of 256 *independent* dim-8 octonion products — block-diagonal, zero inter-block coupling** (F289 D1, verified err 0.0). That is *exactly* the data-parallel shape cpuminer's 4-way/8-way SHA-256 exploits: N independent units advanced in lockstep across SIMD lanes. An 8-wide AVX register holds **one octonion block**; the 256 blocks are an embarrassingly-parallel batch.

| target | technique grafted | payoff |
|---|---|---|
| `loop_bind_hd` / `loop_unbind_hd` / `loop_runbind_hd` | vectorize the per-block Cayley–Dickson product across SIMD lanes (the N-way-lockstep pattern) | the k=7 op runs ~SIMD-width faster; the order-aware RBS store + the capacity sweeps get cheaper-per-joule |
| Class-M HDC bulk `klein4_bind`/`bundle`/`similarity` over many tokens | same N-way batch pattern (per-token independent) | bulk encoding (the RBS-LM hot loop) vectorizes |

This is the most on-theme graft: the **block-diagonal structure F289 established IS a SIMD invitation** — the cpuminer mindset applied to the octonion substrate.

## §3 — The open orchard (candidate reference trees for future grafts — evaluate, don't prescribe)
Each is a *candidate*; srmech's constraints may forbid the direct approach (then graft only the pattern, stay self-contained):
- **`cascade.autocorrelation`** (rc9, Wiener–Khinchin `IFFT(|FFT|²)`) ← **the FFT literature** (split-radix, cache-oblivious / Stockham auto-sort). Constraint: srmech is **pi-free + no FFTW dep**; trig routes through `asymptotic_calculus`. So graft the *algorithmic structure* (radix decomposition, in-place layout), **not** a library link. Apt because autocorrelation is the un-flatten catalog's one new primitive — worth being fast.
- **Class-L dense Laplacian / `jacobi_eigvals` / `symmetric_eigendecompose`** ← **the BLAS-family cache-blocking + the Jacobi-sweep literature**. Constraint: srmech does Jacobi **pi-free in C, no LAPACK** by design (microcontroller-readiness). So graft **cache-blocking + SIMD inner products**, keep the self-contained Jacobi. Apt because Class-L runs on every co-occurrence spectrum.
- **TLV / NDJSON streaming (Class-B/C)** ← established SIMD parsers (the simdjson *pattern*). Constraint: Phase-B5 keeps parsing scope-bounded; graft only the branch-free scanning idea if it stays JPL-clean.

**Rule for the orchard:** a graft that would require a **new external dependency** or **asm** is rejected on arrival (it breaks no-external-dep + JPL). The transfer is always *technique → srmech-native re-implementation*.

## §4 — The must-respect constraints (the half the dev most needs)
- **JPL Power-of-Ten** (`test_jpl_audit.py`, violations only go DOWN): SIMD via `<immintrin.h>` **intrinsics, NOT hand-asm**; **no `goto`** (cpuminer uses it — re-structure); **≤60-line functions** (split the 64-round loop into helpers); **≥2 asserts** per non-exempt function; **no multi-line macros** (cpuminer's round macros must become inline functions).
- **Pedantic-build CI matrix** (gcc / clang / MSVC, `-Werror`/`/WX`): MSVC intrinsic spellings differ from GCC/Clang; **AVX2 / SHA-NI are not universal** → a **runtime cpuid feature-dispatch + a scalar fallback is mandatory**, never a hard `-mavx2` build assumption. Pyodide/WASM gets the scalar/pure-Python path.
- **ABI**: a SIMD-internal speedup of an existing function changes **no wire format → no `SRMECH_ABI_VERSION` bump**; adding `sha256_batch` is **a new symbol → also no bump** (adding symbols never bumps ABI). So every graft here is ABI-safe.
- **Bit-exact parity** (the parity-test ratchet): every SIMD/SHA-NI path **must equal the scalar/Python fallback** digit-for-digit — trivial to assert for SHA-256 (deterministic; same NIST KATs) and for `loop_bind_hd` (assert vs the oracle / the scalar block product, the same `== oracle` check F291 used, err 0.0).
- **Routing**: no new direct `hashlib.sha256(...)` calls — the optimization lives **behind `format.sha256_bytes`** so native dispatch picks it up transparently (existing Phase-B5 discipline).
- **Metric**: report **energy-per-op (hashes/joule via RAPL)** as the headline, not just wall-clock — it is srmech's on-brand, accessibility-aligned figure and the one btc-rosetta already instruments (`energy.py`).

## §5 — Provenance + license (MPM-clean)
- **cpuminer is GPLv2-or-later** (per `sha2.c` headers: "version 2 … or (at your option) any later version"). srmech C is **GPL-3.0-or-later**. GPLv2+ is **forward-compatible** with GPL-3.0+ (the "+" permits upgrade to v3) — so even adapting a snippet is license-clean; but we transfer **techniques**, which are not copyrightable.
- **Attest each technique to its PUBLIC reference**, with cpuminer as a "working-impl pointer," not the citation of record: SHA-NI + N-way SIMD SHA-256 → the **Intel Intrinsics Guide** + **Gueron & Krasnov, "Parallelizing message schedules to accelerate SHA-256"**; the algorithm → **FIPS 180-4**. This keeps "a citation without attestation is not real" intact: the math is attested **A-tier (structure)** to FIPS/Intel; cpuminer is a **B-tier "we read a working impl here"** pointer with its license noted.

## §6 — Verification plan (ships with any graft)
1. **Parity**: SHA-256 paths vs NIST KATs + the btc-rosetta genesis-nonce keystone (byte-identical); `loop_bind_hd` SIMD vs the scalar/oracle product (err 0.0, the F291 check).
2. **JPL audit still passes** (`test_jpl_audit.py` count does not go up).
3. **Pedantic CI matrix** green on gcc/clang/MSVC with the dispatch + scalar fallback; AVX2/SHA-NI cells exercised where available, scalar elsewhere.
4. **Energy bench**: hashes/joule (RAPL) before/after, reusing btc-rosetta `energy.py`; report energy-per-op, not just speed.

## Status / discipline
HAND-DOWN (F281/F289-style); the dev makes the final call on what lands + in what order. **No srmech package edits from this subtree.** Recommended landing order: (1) `sha256_batch` N-way SIMD (biggest broad win, apples-to-apples, ABI-safe new symbol); (2) `loop_bind_hd` SIMD (on-theme, parity-trivial); (3) SHA-NI single-stream (dispatch-gated); (4) midstate as an opt-in specialized path; the §3 orchard is evaluate-later. Scope: energy/perf-engineering of srmech's own C; **crypto/mining explicitly OUT** (btc-rosetta boundary cited). Provenance to public refs (FIPS 180-4 / Intel / Gueron-Krasnov); cpuminer GPLv2+ ↔ srmech GPL-3.0+ compatible. Builds on the btc-rosetta bench (`/home/skirklan/general/btc-rosetta`, the measured midstate 1.73× anchor) + F289 D1 (the block-diagonal structure that makes `loop_bind_hd` a SIMD target). `[[feedback_trauma_informed_defensive_scope]]` (perf-engineering only; no mining/capability); `[[feedback_upstream_srmech_fixes_as_research_notes]]`; `[[feedback_abstract_lexicon_is_ada_accommodation]]` (the "apple-tree" graft framing is the user's, load-bearing). Verified srmech v0.7.0rc9, `/tmp/srmech_v070rc9_venv`.
