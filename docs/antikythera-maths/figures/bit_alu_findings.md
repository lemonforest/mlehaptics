# Bit-packed HDC ALU — first run

**Status:** Research finding (this branch).
**Date:** 2026-05-04
**Code:**
- [`research/bit_alu.py`](../research/bit_alu.py) — bit-packed binary HDC primitives
- [`research/bit_alu_benchmark.py`](../research/bit_alu_benchmark.py) — perf comparison vs the existing `complex128` reference encoder
- [`research/cycle_alignment_investigation.py`](../research/cycle_alignment_investigation.py) — solar vs sidereal day framing for `permute = sigma_day`
- Public facade: [`antikythera_spectral.bit_alu`](../antikythera-spectral/python/antikythera_spectral/bit_alu.py)

## TL;DR

1. **Memory is a 125× win.** A D=940 hypervector takes 120 B as bit-packed `uint64[15]` vs 15 KB as `complex128[940]`. Same algebraic structure (cyclic-group representation of the Antikythera dials), 1/125 of the memory.
2. **`bind` is a 2-10× speedup**, growing with D. XOR over a uint64 array is much faster than complex-multiply over a complex128 array.
3. **`permute` and `similarity` are slower in this first-run implementation** — `permute` uses Python big-int rotate (good correctness, poor scaling at D=13440); `similarity` uses Python `int.bit_count()` in a loop. Both have known optimisation paths (numpy bit-pack/unpack for permute; `np.bitwise_count` from numpy ≥ 2.0 for similarity) that would push them to native speed; not done in this PR.
4. **The "ALU only" semantics are met.** Every primitive (bind, bundle, permute, hamming, similarity) reduces to integer bit-operations: XOR, popcount, shift. No floating-point, no complex arithmetic, no matrix multiplies. The memory + bind wins are immediate; the permute / similarity wins are an optimisation away.
5. **Cycle alignment of `sigma_day` ⇔ one Julian day = one mean solar day.** Decisive: the existing encoder keys `cycle_period_days` in Julian days; the bit-ALU's `permute(v, 1, D)` advance therefore corresponds to one Julian / mean-solar day. Sidereal-day framing would shift the Callippic residue by 1 over a full 940-tick rotation (drift = 2.57 days). Solar/Julian is correct.

## What we built

### `research/bit_alu.py` — primitives

| Operation | Bit ALU | Reference (complex128) |
|---|---|---|
| `random_hv(D, rng)` | uniform Bernoulli over `uint64[n_words(D)]` | unit-norm complex Gaussian over `complex128[D]` |
| `bind(a, b)` | `a ^ b` (XOR) | `a * b` (complex multiply) |
| `bundle(stack)` | bitwise majority threshold | sum + L2-normalise |
| `permute(v, n, D)` | cyclic bit-rotation by `n` | `np.roll(v, n)` |
| `hamming_distance(a, b)` | popcount of XOR | n/a |
| `similarity(a, b, D)` | `1 − 2H/D` (bipolar-equivalent in [-1, 1]) | `\|⟨a, b⟩\|` |

Plus an encoder analogue:

- `encode_ant_bit(jd, D)` — same algebraic structure as `_encode_dense` in `encode_ant.py` (sum of permuted bases per dial), but `np.roll → permute`, `+ → bundle_majority`, complex Gaussian basis → binary Bernoulli basis.
- `decode_dial_bit(state, D, dial_idx, modulus)` — argmax of similarity over candidate residues.

### `research/cycle_alignment_investigation.py` — solar vs sidereal

Resolution of the user's question: "should one rotation of the key be a complete terrestrial or solar day?"

- Mean solar day: 86 400 SI s. The Julian Date increment. The Antikythera's hand-crank tick.
- Sidereal day: 86 164.09 SI s. Earth's rotation in the inertial frame.
- Ratio: 1.002 738 sidereal/solar, drift 235.9 s/day, drift over 940 days = **2.57 mean-solar days**.

Empirical run at `D = 940`, `n_ticks = 940`:

| Framing | Span | Callippic residue (actual / expected) | Metonic residue (actual / expected) |
|---|---|---|---|
| **Solar / Julian** | 940 JD | **127 / 127 ✓** | 31 / 31 ✓ |
| Sidereal | 937.43 JD | 126 / 127 ⨯ | 31 / 31 ✓ |

The Callippic dial drifts by 1 residue position over a full bit-rotation cycle under sidereal framing. Metonic happens to be 31 in both because its modulus is small enough that the 0.273 % drift doesn't cross a residue boundary.

**Conclusion:** the bit-ALU's `permute(v, 1, D)` ⇔ one **Julian / mean-solar day**. The encoder's `cycle_period_days` are documented in Julian days (see `encode_ant.DialSpec.residue` and `astronomical_cycles.Cycle.mechanism_days`); the Julian Date is by definition tied to the mean solar day. The mechanism's hand-crank turns once per mean-solar day. All three pieces (encoder spec, time-scale convention, mechanism semantics) align on solar/Julian.

Sidereal-day framing IS meaningful for sidereal-frame DIALS (zodiac longitude in the inertial sky, planetary sidereal periods), but those are already expressed in Julian days inside `encode_ant.py`; one would convert at decode time if a sidereal interpretation of the residue were wanted.

## Benchmark results

`python -m research.bit_alu_benchmark --reps 5000 --encode-reps 100`

Hardware: contemporary x86-64, single-threaded, NumPy 2.4.4. Results in microseconds per operation.

### Memory footprint

| D | complex128 HV | bit_alu HV | Ratio |
|---|---:|---:|---:|
| 940 (Callippic) | 15 040 B | 120 B | **125×** |
| 13 440 (packing) | 215 040 B | 1 680 B | **128×** |

### Operation timings

| op | D | reps | cx128 µs/op | bit µs/op | speedup |
|---|---:|---:|---:|---:|---:|
| `bind` | 940 | 5 000 | 5.314 | 2.239 | **2.37×** |
| `bundle (M=8)` | 940 | 1 000 | 86.513 | 96.905 | 0.89× |
| `permute (n=1)` | 940 | 1 000 | 36.928 | 53.571 | 0.69× |
| `similarity` | 940 | 5 000 | 5.534 | 16.558 | 0.33× |
| `encode_full` | 940 | 100 | 497.681 | 578.756 | 0.86× |
| `bind` | 13 440 | 5 000 | 40.257 | 4.068 | **9.90×** |
| `bundle (M=8)` | 13 440 | 1 000 | 925.073 | 389.967 | **2.37×** |
| `permute (n=1)` | 13 440 | 1 000 | 62.325 | 1 143.138 | 0.05× |
| `similarity` | 13 440 | 5 000 | 78.314 | 87.771 | 0.89× |
| `encode_full` | 13 440 | 100 | 2 134.221 | 14 985.298 | 0.14× |

### Reading the table

- **`bind` scales with D, decisively.** 2.37× at D=940 → 9.90× at D=13 440. XOR over `uint64[n]` is much cheaper than complex-multiply over `complex128[64n]`. This is the operation HDC algorithms call most often.
- **`bundle` is competitive at small D and 2.37× faster at large D.** The bit-ALU bundle uses `np.unpackbits` + `sum` + threshold — vectorisable and cache-friendly at scale. At D=940 the unpack-pack overhead competes with numpy's native sum + L2-normalise; at D=13 440 the bit-ALU pulls ahead.
- **`permute` is the weak point.** This first-run implementation packs to a Python big-int, rotates within the D-bit window with `<<`/`>>`, and unpacks. Big-int operations are ~O(D) but constant-factor expensive at D=13 440 (1.1 ms vs 0.06 ms for `np.roll`). Numpy bit-pack / unpack with `np.roll` would close most of this gap; vectorised cross-word shifts on uint64 arrays would close the rest. **Tracked as a follow-up; see "What's next" below.**
- **`similarity` at D=940 is the second weak point.** Python's `int.bit_count()` in a sum-loop pays a per-word overhead. `np.bitwise_count` (numpy ≥ 2.0) would vectorise this to native speed. **Same follow-up as `permute`.**
- **The full encoder is currently slower** because `permute` is hot in the encode path (one rotate per dial).

### What an actual ALU implementation would look like

The Python-level numbers above are bounded by interpreter overhead. At the *hardware* level — which is the natural framing for "ALU only":

- **`bind`** = `XOR` instruction on a packed register (1 cycle for the whole hypervector if D ≤ register width; constant cycles per cache line for larger D).
- **`hamming_distance`** = `XOR` + `POPCNT` instructions (POPCNT is 3-5 cycle latency on modern x86; ~0.3 µs for D=940 vectors using AVX2 + popcount). NEON has equivalent.
- **`permute`** = combined shift + OR across cache lines. Hardware-friendly; an FPGA could do a 940-bit cyclic shift in O(log D) gates.
- **`bundle (majority)`** = column-wise popcount + threshold. AVX-512 has `_mm512_popcnt_epi64`; SVE2 has `cnt`. Bit-serial-style, but parallel across the D axis.

A hand-tuned C / NEON / AVX-512 implementation of the bit ALU would close the remaining gaps to native speed and likely turn the 0.05–0.89× rows into 5–50× wins. That's a v0.4.x scope; for v0.3.0 the "first run" is to establish that the algebraic substrate is sound (this PR) and measure the pure-Python baseline.

## What's next (deferred to v0.4.x)

1. **Numpy-fast `permute`** — replace Python big-int rotate with `np.unpackbits` + `np.roll` + `np.packbits`, or with vectorised cross-word `<<` / `>>` on `uint64[]`. Estimated 10-50× speedup at D=13 440.
2. **`np.bitwise_count` for `similarity`** — drop the Python-level `int.bit_count()` loop. Estimated 5-20× speedup at all D.
3. **Encoder fast-path** — once `permute` is fast, the full bit-ALU encoder should beat the complex128 encoder by the bind ratio (2-10×) at all D.
4. **Bit-ALU H-battery rows** — does the bit-ALU encoder pass the same H-battery checks as the complex128 encoder (round-trip, σ_day unit-operator, etc.)?  Almost certainly yes (same algebraic structure), but worth pinning.
5. **Hardware-style rotation operators** — the Antikythera's gear ratios are themselves a kind of rotation. There's a research thread on whether the `bit_alu.permute(v, k)` for non-trivial `k` corresponds to gear-ratio-style multi-day advance, and whether that's a faithful representation of the mechanism's gear DAG. Out of scope for this PR.

## Cross-references

- Notebook §6 (E-H2 / E-H3 / E-H4) — the H-battery rows the bit-ALU should also pass once exercised.
- Notebook §3 (cyclic-group algebra B-H1 / B-H2) — the algebraic substrate the bit-ALU implements verbatim, just in BSC (Binary Spatter Code) instead of FHRR.
- ADR 0012 — the "algebra/eigenbasis modelling, not CAD/fabrication" scope discipline. The bit-ALU is the cleanest possible implementation OF that discipline: every operation is bitwise / phase-space algebra.

## Sources

- **Kanerva (2009).** "Hyperdimensional Computing: An Introduction to Computing in Distributed Representation with High-Dimensional Random Vectors." *Cognitive Computation* 1:139.
- **Plate (2003).** *Holographic Reduced Representation: Distributed Representation for Cognitive Structures.* CSLI Publications.
- **Schlegel, Neubert & Protzel (2022).** "A Comparison of Vector Symbolic Architectures." *Artif. Intell. Rev.* 55:4523. (Survey; this module implements the BSC variant.)
- **IAU 2009 / SOFA constants** — sidereal day length, mean solar day length.
