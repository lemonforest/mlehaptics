# Tier 2 design: hyperdimensional state in C

> **Status:** scoping complete; phase 2a foundation in progress
> **Targets:** v0.6.1 (phase 2a), v0.7.0 (phase 2b + 2c)
> **Smoke entries:** `get_local_view`, `get_eclipse_probability` flip from `tier2_skip` to `parity`

## What's left to port

Two encoder-touching bridge methods remain Python-only after v0.6.0 — both flagged as `tier2_skip` in `tests/test_parity_smoke.py`:

| method | what it does |
|---|---|
| `get_local_view(jd, body, lat, lon)` | encode HD state, bind observer, return `complex128[D]` |
| `get_eclipse_probability(jd)` | encode HD state, project onto syzygy operator, return scalar |

Both operate on the **full hyperdimensional state vector** — `complex128` of dimension D=65536 — not the 38-body Q-format integer phases the C side currently exposes. The C runtime needs to learn how to carry the HD state.

## Channel basis construction (the gating decision)

The HD state is built from **per-body channel bases** — random unit-norm complex hypervectors generated at instrument-init time. Currently:

```python
def _initialize_bases(self):
    bases = {}
    for i, body in enumerate(self.body_names):
        rng = np.random.default_rng(2026 + i)              # PCG64 seeded
        phases = rng.uniform(0, 2 * np.pi, self.D)         # numpy uniform conversion
        v = np.exp(1j * phases).astype(np.complex128)
        bases[body] = v / np.sqrt(self.D)
    return bases
```

For C parity, this must produce **byte-identical** output on both sides. Two paths:

### Path A — reproduce numpy PCG64 + uniform in C (rejected)

Numpy's `default_rng` is PCG64-DXSM internally; `.uniform(low, high, size)` does specific double conversion (`(u >> 11) * (1.0 / (1<<53))` scaled). Reproducing PCG64-DXSM exactly in C is ~200 LOC and brittle — any numpy bump that touches the algorithm breaks parity.

### Path B — switch to splitmix64 on both sides (chosen)

Splitmix64 is the canonical "small fast deterministic PRNG":
```
state += 0x9E3779B97F4A7C15
z = state
z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9
z = (z ^ (z >> 27)) * 0x94D049BB133111EB
return z ^ (z >> 31)
```
Six lines. Identical bit-exact output across Python + C trivially. Convert each uint64 to a `[0, 2π)` double via `(u >> 11) * (2π / (1<<53))` — same conversion both sides.

**Behavior change:** the basis byte values change vs v0.6.0. The state vectors `state_interleaved_f32` returned by `get_local_view` will be byte-different from v0.6.0. The Python tests don't pin those bytes (only `ok=True` on the operation), so this is observable but non-breaking.

## Three-phase delivery

### Phase 2a — foundation (v0.6.1, this work)

* C: `c/include/es_prng.h` + `c/src/es_prng.c` — splitmix64 (~30 LOC).
* C: `c/src/es_channel_bases.c` — `es_channel_basis(uint64_t seed, complex64_t *out, size_t D)` lazily fills a D-dim basis from a seed.
* C: `complex64_t` typedef in the public header.
* Python: `_research/portable_prng.py` — mirror algorithm.
* Python: `_initialize_bases` switches to the portable PRNG. Existing tests still pass (no byte pins).
* Test: byte-identical agreement between Py + C for the same seed across N=38 bodies, D ∈ {1024, 65536}.
* ABI v3 → v4 (additive: new exported symbols, no encoder changes).
* No bridge behavior change. Patch-version bump 0.6.0 → 0.6.1.

### Phase 2b — HD encode + observer-bind + eclipse (v0.7.0)

* C: `es_encode_state_hd(double delta_t_days, complex64_t *out)` — call `es_encode_state` for the 38 phases; for each body, lazily get the channel basis, np.roll it by the integer residue, sum into out; normalize.
* C: `es_bind_observer(complex64_t *state_in, size_t body_idx, double lat_deg, double lon_deg, complex64_t *state_out)` — pure HDC algebra, no SPICE/skyfield.
* C: `es_get_eclipse_probability(complex64_t *state, double *out_prob)` — build syzygy operator (sun + moon + node basis with seed=777), project state onto it.
* Bridge: dispatch `get_local_view` and `get_eclipse_probability` on `backend={"auto","bip","c"}`.
* Parity smoke: flip both `tier2_skip` entries to `parity` with float-ULP comparators on the complex64 outputs.
* ABI v4 → v5.
* Minor-version bump 0.6.x → 0.7.0.

### Phase 2c — research instrument decision (v0.7.x)

The current `EphemerisHDCInstrument.encode_state` uses `scipy.linalg.expm` + matrix-expm propagation, which is **divergent** from the BIP path. This is the FPU "reference" path but it's slow (N³ per chunk) and not particularly useful as a reference once the BIP + C paths agree.

Options:
* **Option 1:** retire the matrix-expm path, route `bridge.get_local_view` to a unified BIP-encode-then-lift implementation. Simpler, but loses the FPU-vs-integer parity check (which has been the regression test for cyclic-group propagation correctness).
* **Option 2:** keep the matrix-expm path as the FPU reference behind `backend="fpu-ref"`, route `auto`/`bip`/`c` through the BIP-and-lift path. Three-way parity story (`bip` vs `c` vs `fpu-ref` within float64 ULP).

Decision deferred until phase 2b lands and we can measure the actual path-divergence. **For phase 2b, the "BIP + lift" implementation is the parity target.**

## Smoke discipline

Phase 2b must pin parity in `tests/test_parity_smoke.py` for both flipped entries. Comparators:
* `get_local_view`: complex64[D] state vectors must agree within float-ULP on every entry.
* `get_eclipse_probability`: scalar within ~1e-12 of the ULP bound.

Once phase 2b ships, the parity smoke shows **0 tier2_skip entries**. Every public bridge method touching the encoder has a paired C path. The "if we always smoke all python things, we know to always smoke the same C things" discipline is fully realised.

## What this document is not

A full C-side specification. The cookbook for *exactly* how `es_encode_state_hd` allocates its working buffers, *exactly* what error code goes where, *exactly* how the lazy basis cache invalidates — those are PR-level decisions, not architectural ones. This doc captures the architectural decisions: PRNG choice, three-phase delivery, smoke discipline.
