# srmech CI Python-suite runtime — measured investigation

**Date:** 2026-07-19
**Scope:** investigation + written proposal only. **No fix implemented, no rc, no
refactor, no test deleted.** The only files this work writes are this note and
one appended row in `srmech_mpm_notes.ndjson`.

---

## 0. Headline (read this if you read nothing else)

The suite is **not** uniformly slow. The "≈150 ms/test" framing in the brief is
an artefact of dividing a skewed total by a flat test count.

| | measured |
|---|---|
| profiling run, one process (the `--durations=50` run) | **2292.8 s** (9451 passed / 40 skipped / 60 failed*) |
| clean-tree serial baseline (correct `.so`, later run) | **2618.1 s** (9532 passed / 40 skipped / 15 failed) |
| **top 50 tests** | **1467.2 s = 64.0 % of the profiling run** |
| remaining 9,501 tests | 825.6 s → **87 ms/test** |
| naive flat mean (misleading) | 240 ms/test |

\* Two local baselines exist because the tree moved under this session. The
**2292.8 s** run is where the top-50 table comes from; it used a snapshot whose
`.so` was stale, which is why it shows 60 failures. The **2618.1 s** run is the
clean, consistent tree (15 failures) and is the baseline the xdist comparison in
§6 uses — both sides of that comparison are from the clean tree, so the 2.92×
is apples-to-apples. See §1.

**0.5 % of the tests consume 64 % of the wall clock.** One single file —
`test_qm_so8_triality_c_rc146.py` — is **453 s, ~20 % of the entire suite**, from
six tests.

Consequences for the three questions asked:

1. **Where the time goes:** a short head of very expensive tests, not broad
   per-test overhead, and not duplicated setup.
2. **Single biggest lever:** `pytest-xdist`, worth a **measured 2.92× at `-n 4`**
   (2618 s → 897 s, same tree, back-to-back) — projecting the CI wall-clock
   driver from **25.2 min to ~8.6 min**.
   But it **does not run today**: it aborts during collection, and the cause is
   exactly **one line** — a `parametrize` calling `os.urandom(2000)` at
   collection time (`test_bus_cipher_transport_c_rc179.py:97`), so every worker
   collects a different test ID. One-line fix, zero coverage change (§6 / P0).
   Nothing else in 9,591 tests blocks parallelism.
   **This was found by running xdist, not by reading the tree — my own static
   audit had wrongly cleared it.** Running it also exposed one genuine latent
   defect (a test that passes only by import side effect — §6 / P1a).
3. **Cell spread (1.81×):** decomposes *exactly* into **1.074 × 1.686** —
   ~7 % interpreter version, ~69 % runner hardware. Not a code problem.

Two findings are reported **separately** because they are correctness matters,
not scheduling matters: §8 (the flagged `test_genome_census_rc267` core dump —
**not reproduced**, with a concrete alternative explanation) and §9 (a real
C-side memory/reentrancy finding).

---

## 1. Method, and what to distrust in these numbers

Measured under WSL2 (Ubuntu, Python 3.10.12, gcc), on the **native ext4**
filesystem — *not* `/mnt/d`, because the Windows 9p mount inflates file I/O
enough to invalidate the ranking. The native library was built from the repo's
own CMake (`HAS_NATIVE=True`), matching CI's `pip install -e ".[dev]"`.

**Honest caveats — these matter:**

- **Absolute wall time does not transfer to CI.** Local serial total was 2292 s
  vs CI's 1406–1510 s on ubuntu. The **ranking** transfers; the totals do not.
  Where this note quotes a proposed win as a *fraction*, that fraction is the
  transferable quantity.
- **The top-50 run used a torn snapshot.** The working tree moved underneath this
  session mid-run (another agent's worktree activity; `HEAD` advanced and the
  `tools.total` pin went 453 → 456). My snapshot ended up **2 test files behind**
  (`test_genome_integrate_plasmids_rc279.py`, `test_plasmid_section_counts_rc280.py`)
  with a `.so` built from the *earlier* C source. That produced the 60 spurious
  `native_equals_pure` / version-pin failures. Duration **ranking** is still
  sound, but individual `native-vs-pure` entries may be inflated where the test
  fell back to the pure path. §8's re-test was redone on a **clean, consistent**
  tree with a correctly-built `.so`, and is trustworthy.
- **Concurrency.** Part of the session had a second agent running its own pytest
  on the same box. The authoritative serial run was started only after verifying
  the box was quiet (load ≈ 1.0) and was re-measured mid-flight at a clean
  9 %/120 s rate.
- Run used `--timeout=120`; **two entries are timeout-capped at 120 s** and are
  therefore *lower bounds*. CI has no timeout, so their true CI cost is higher.

---

## 2. The measured top-50 durations

Full list, `pytest tests/ -q --durations=50`. `call` phase throughout — note that
**no `setup` or `teardown` entry appears anywhere in the top 50**, which is
itself a load-bearing result (see §4).

```
120.02s  test_qalg_eigvals_c_rc162.py::test_eigvals_complex_random_byte_identical   [TIMEOUT-CAPPED]
120.00s  test_thetasum_soundness_battery_rc234.py::test_rank2_kernel_sweep_never_yields_a_false_zero [TIMEOUT-CAPPED]
100.57s  test_qm_so8_triality_c_rc146.py::test_byte_exact_native_equals_forced_pure[lean_isa_seventh_primitive]
 99.56s  test_qm_so8_triality_c_rc146.py::test_byte_exact_native_equals_forced_pure[triality_automorphism]
 99.29s  test_qm_so8_triality_c_rc146.py::test_byte_exact_native_equals_forced_pure[triality_swap]
 89.50s  test_qm_so8_triality_c_rc146.py::test_so7_float_composition_parity
 86.87s  test_immolation.py::test_every_advertised_return_type_is_honest
 83.32s  test_octonion_cluster_numpy_free_reachable_rc122.py::test_triality_imports_and_runs_numpy_free
 54.33s  test_qm_so8_triality_c_rc146.py::test_triality_tau_is_order_three_permutation
 49.69s  test_c_standalone_honor_rc156.py::test_exact_dft_over_old_cap_native_accepts_and_matches_pure
 34.69s  test_thetasum_is_zero_sound_rc210.py::test_rank2_kernel_generator_never_yields_a_false_zero
 32.64s  test_thetasum_soundness_battery_rc234.py::test_random_fuzz_soundness_direction
 31.59s  test_an_embedding.py::test_all_imaginary_units
 31.47s  test_mcp.py::test_every_advertised_tool_invocable
 29.36s  test_qalg_eigvals_c_rc162.py::test_eigvals_real_random_byte_identical
 25.82s  test_genome_native_dispatch_rc153.py::test_save_byte_identical_over_old_caps
 25.26s  test_riemann_theta_rc74.py::test_goepel_inner_region_is_box_stable
 24.27s  test_thetasum_z6_collapse_rc235.py::test_z6_soundness_perturbed_siblings_stay_false
 23.85s  test_qrow_prose_constructors_rc113.py::test_capstone_euler_q_exponential_honest_open_via_registry
 20.83s  test_mat_eigvals_qr_shift_rc26.py::test_mixed_spectrum_matches_exact_oracle[5x5]
 20.61s  test_riemann_theta_rc81.py::test_python_c_parity_orthogonal_frame_first_difference
 15.48s  test_riemann_theta_rc74.py::test_goepel_lhs_equals_rhs_on_safe_region
 14.00s  test_vanhoeij_rc222.py::test_byte_identity_corpus[sd5_deg32-poly6]
 13.32s  test_thetasum_c_parity.py::test_randomized_parity_fuzz
 12.19s  test_qmat_rref_crt_rc46.py::test_franel_484x154_dimensions
 11.42s  test_thetasum_z6_collapse_rc235.py::test_z6_native_equals_pure
 11.29s  test_thetasum_soundness_battery_rc234.py::test_zero_side_identities_stay_proven
 10.09s  test_qm_so8_triality_c_rc146.py::test_an_embedding_float_composition_parity
  9.55s  test_qalg_pi_c_rc157.py::test_pi_cascade_native_equals_pure_byte_identical[1000]
  9.17s  test_resonant_spectrum_sparse_rc230.py::test_runs_and_matches_past_256
  9.09s  test_infer_router_f929.py::test_infer_routes_q_definite_sum
  9.07s  test_mat_eigvals_qr_shift_rc26.py::test_cyclic_companion_matches_exact_oracle[x^6-1]
  8.79s  test_qalg_capstone_c_rc166.py::test_eig_exact_native_equals_forced_pure[True-companion_x3]
  8.63s  test_qalg_eigvals_c_rc162.py::test_eigvals_complex_native_equals_pure[mat5]
  8.62s  test_pi_digits_catalog.py::test_pi_cascade_digits_chain_falsification_all_rows
  8.41s  test_qalg_pi_c_rc157.py::test_value_oracles
  8.28s  test_infer_exact_rows_rc223.py::test_native_equals_pure[q_definite]
  8.00s  test_thetasum_interpolation_rc98.py::test_interpolation_sound_vs_eval_oracle
  7.80s  test_thetasum_soundness_battery_rc234.py::test_battery_native_equals_pure
  7.74s  test_riemann_theta_rc107_sparse_gates.py::test_bit_identity_addition_distinctness[4-2]
  7.49s  test_infer_exact_rows_rc223.py::test_open_cases_stay_open[q_indefinite_open]
  7.49s  test_chain_run_c_rc174.py::test_shipped_chain_native_equals_pure[pi_digits:...:11]
  7.43s  test_catalog_chain_infer_c_rc175.py::test_run_catalog_chain_native_equals_fully_pure[...]
  7.38s  test_infer_exact_rows_rc223.py::test_reducible_row_and_verified[q_definite-sigma_q]
  7.35s  test_so8_triality.py::test_cartan_relation_residual_zero
  7.32s  test_qalg_capstone_c_rc166.py::test_eig_exact_native_equals_forced_pure[False-companion_x3]
  7.23s  test_thetasum_z6_collapse_rc235.py::test_z6_declines_the_real_3_3_residue_leaf
  7.13s  test_qalg_capstone_c_rc166.py::test_jordan_form_native_equals_forced_pure[True-companion_x3]
  7.06s  test_qalg_capstone_c_rc166.py::test_jordan_form_native_equals_forced_pure[False-companion_x3]
  6.84s  test_thetasum_iszero_corpus_parity_rc210.py::test_corpus_native_equals_pure_on_every_object
```

### Top-50 aggregated by file

| seconds | tests in top-50 | file | share of suite |
|--------:|----:|---|---:|
| **453.3** | 6 | `test_qm_so8_triality_c_rc146.py` | **19.8 %** |
| 171.7 | 4 | `test_thetasum_soundness_battery_rc234.py` | 7.5 % |
| 158.0 | 3 | `test_qalg_eigvals_c_rc162.py` | 6.9 % |
| 86.9 | 1 | `test_immolation.py` | 3.8 % |
| 83.3 | 1 | `test_octonion_cluster_numpy_free_reachable_rc122.py` | 3.6 % |
| 49.7 | 1 | `test_c_standalone_honor_rc156.py` | 2.2 % |
| 42.9 | 3 | `test_thetasum_z6_collapse_rc235.py` | 1.9 % |
| 40.7 | 2 | `test_riemann_theta_rc74.py` | 1.8 % |
| 34.7 | 1 | `test_thetasum_is_zero_sound_rc210.py` | 1.5 % |
| 31.6 | 1 | `test_an_embedding.py` | 1.4 % |
| 31.5 | 1 | `test_mcp.py` | 1.4 % |
| 30.3 | 4 | `test_qalg_capstone_c_rc166.py` | 1.3 % |
| 29.9 | 2 | `test_mat_eigvals_qr_shift_rc26.py` | 1.3 % |
| 25.8 | 1 | `test_genome_native_dispatch_rc153.py` | 1.1 % |

The **thetasum family** (`rc234` + `rc235` + `rc210` + `c_parity` + `rc98` +
`iszero_corpus`) totals **~277 s ≈ 12 %** across six files — the second-largest
cluster after so8/triality.

---

## 3. What the expensive tests actually are

Almost every entry in the head is one of three shapes:

1. **`native_equals_forced_pure` differential tests.** They deliberately run the
   *complete pure-Python* implementation and compare byte-for-byte against C.
   The pure path is the cost, and that cost is **the point of the test** — this
   is ADR-0003/0009 parity discipline made executable. `test_qm_so8_triality_c_rc146`
   is the extreme case: forcing the pure path through a 28×28 triality
   automorphism is genuinely expensive arithmetic.
2. **Soundness/fuzz batteries.** `thetasum_soundness_battery`, `is_zero_sound`,
   `z6_collapse` — randomized sweeps asserting "never a false zero". Cost scales
   with the sweep parameter.
3. **Whole-surface walks.** `test_immolation::test_every_advertised_return_type_is_honest`
   (86.9 s) and `test_mcp::test_every_advertised_tool_invocable` (31.5 s) each
   invoke **every one of the 456 registered tools** once.

None of these is accidental waste. They are the coverage. That is why every
proposal in §10 is about **scheduling and caching**, not about removing them.

---

## 4. Setup vs assertions vs pathology — the distinction the brief asked for

**Measured: the cost is in `call`, not `setup`.** No `setup`/`teardown` line
appears in the top 50 at all. The suite's fixture layer is cheap.

Corroborating measurements:

| operation | measured cost | notes |
|---|---:|---|
| `import srmech` + `tool_schema` (per process) | **1.18 s** | once per process; ×N for xdist workers and ×36 for subprocess tests |
| `warmup_all()` first call | ~0 ms | registration already happened at module import |
| `warmup_all()` × 10 (idempotent) | **0.7 ms total** | genuinely idempotent |
| `describe()` | **0.4 ms** | |
| `get_tool_schema()` | **0.1 ms** | pure constructor, uncached — but cheap |
| `tool_schema_view()` | 11.4 ms | native round-trip + JSON parse |

### The rc281 duplication hypothesis is REFUTED

rc281 reported the `describe()["tools"]["total"]` pin duplicated across ~56
files. Verified against the tree: it is **50 files** carrying **48 assertions**
(the "~56" count includes stale `__pycache__` entries).

**But the cost is 50 × 0.4 ms ≈ 20 ms — 0.001 % of the suite.** Registration
happens once per process at `srmech.amsc.tool_schema` import (module-level
`_register_*_tools()` calls, cached by `sys.modules`); `warmup_all()` is a
no-op after the first call. There is **no per-module rebuild**.

So this is **redundant assertions, not redundant setup** — and redundant
assertions here are free. **Collapsing the 50 pins would save nothing
measurable and is not proposed.** See §11.

---

## 5. Superlinear / pathological patterns found

- **Two timeout-capped tests** (`test_eigvals_complex_random_byte_identical`,
  `test_rank2_kernel_sweep_never_yields_a_false_zero`) exceeded 120 s. These are
  the strongest remaining candidates for an rc280-style algorithmic fix, because
  they are *bounded only by the timeout*, so their true cost is unknown and
  possibly much larger on a slower cell.
- **~30,000 randomized fuzz iterations** across 27 files (`for _ in range(N)`
  with N ≥ 100; summed literal N = 30,035). Each iteration typically runs both a
  C and a pure path plus a comparison.
- **The rosetta ledger walk is fully uncached.** `tests/conftest.py` defines
  `rosetta_live_objects()` (a `pkgutil.walk_packages` import-walk over 12 root
  packages) and `rosetta_reached_ledger_ops()` (a transitive call-graph walk that
  calls `inspect.getsource()` + `ast.parse()` **per function visited**, with
  `seen_code` scoped *per call*, so functions reachable from many roots are
  re-parsed every time). `rosetta_live_objects()` is called from **7 sites**
  across 4 test files, and `rosetta_reached_ledger_ops()` is invoked in two loops
  over the ledger's 677 rows (227 `composition_of_c` + 201 `non_compute`).
  There is **no `lru_cache` anywhere in `conftest.py`**, and the entire suite has
  exactly **one** module-scoped fixture — everything else is function-scoped.
  Indicative per-file timings put `test_annex_ratchet_rc177/rc183` at ~14 s each
  largely on this walk.
- **36 subprocess spawns** across 19 files (14 in `test_cli_bus.py` alone, 6 in
  `test_mcp.py`, plus 9 one-per-file `*_numpy_free_reachable_*` tests). Each pays
  full interpreter start + the 1.18 s srmech import.
  `test_octonion_cluster_numpy_free_reachable_rc122` at **83.3 s** is the visible
  cost of this shape.

---

## 6. Parallelism (`pytest-xdist`) — viability, blockers, measured win

`pytest-xdist` is **not currently a dependency** and appears nowhere in the repo.
There is **no `[tool.pytest.ini_options]` section** at all.

### Blocker audit (performed against the tree, not assumed)

| candidate blocker | finding | verdict |
|---|---|---|
| writes to fixed paths | every `write_text`/`open(...,'w')` in `tests/` resolves through a `tmp_path`-derived fixture | **not a blocker** |
| `os.chdir` | **1 file** — `test_pypi_readme_changelog.py` (cwd is process-global) | minor; isolated by `--dist loadfile` |
| `os.environ` mutation | 3 files (`test_byo_cascade_toml`, `test_infer_exact_rows_rc223`, `test_introspect`) | minor; per-worker processes make this safe |
| fixed network ports | **none found**; `test_mcp.py` uses ephemeral `port=0` | **not a blocker** |
| module-level registry mutation | 6 files call `warmup_all()` at import — idempotent, per-process | **not a blocker** |
| ordering dependencies | no `pytest.mark.order` / `pytest.mark.dependency` / `incremental` markers anywhere; earlier grep hits were docstring prose | **not a blocker** |
| the native `.so` | loaded read-only per process via ctypes | **not a blocker** |
| ratchet tests (JPL / rosetta / stop-list) | read repo source read-only (`_C_SRC_DIR.glob`, `rosetta_classification.ndjson`) | **not a blocker** |
| C file-scope statics (§9) | process-global, **not** thread-safe — but xdist uses *processes*, not threads | **not a blocker for xdist** (is a blocker for `-p xdist --dist worksteal` inside one process, which is not proposed) |

### The one REAL blocker — found by running it, not by reading it

The static audit above said "viable". **Running it refuted that**, and this is
the most useful single result in this note:

```
ERROR gw2 - Different tests were collected between gw1 and gw2.
tests/test_bus_cipher_transport_c_rc179.py::test_c_bus_wire_is_decode_splice_recoverable[...]
```

`pytest -n 4` and `-n 8` both **abort during collection**. The cause is exactly
one line — `tests/test_bus_cipher_transport_c_rc179.py:97`:

```python
@pytest.mark.parametrize("pt", [b"", b"x", b"hello encrypted bus", os.urandom(2000)])
def test_c_bus_wire_is_decode_splice_recoverable(monkeypatch, pt):
```

`os.urandom(2000)` is evaluated **at collection time, inside the decorator**.
Every xdist worker is a separate process, so each generates a *different* 2000-byte
payload, producing a different test **ID**. xdist requires all workers to collect
an identical test list, so it refuses to start.

This is the whole blocker. It is **one test, one line**, and nothing else in
9,591 tests trips it. (The two other `os.urandom(32)` calls in the same file, at
lines 104 and 122, are *inside the test body* and are perfectly fine.)

**Fix — zero coverage change, randomness preserved.** Move the randomness from
collection time into the test body:

```python
@pytest.mark.parametrize("pt", [b"", b"x", b"hello encrypted bus", None])
def test_c_bus_wire_is_decode_splice_recoverable(monkeypatch, pt):
    if pt is None:
        pt = os.urandom(2000)
    ...
```

The collected ID becomes the deterministic `[None]`, while the payload is still
random — in fact *more* varied than today, because it re-randomises on every run
rather than once per collection. The same assertion runs on the same shape of
input. This is strictly better fuzzing **and** it unblocks parallelism.

**Conclusion: xdist is viable behind a one-line fix.** Apart from that single
line the suite is unusually well-behaved — `tmp_path` discipline is
near-universal, there are no ordering markers, and no fixed ports. Recommended
mode is **`--dist loadfile`** (whole file to one worker), which additionally
neutralises the `chdir`/`environ` cases and keeps each file's tests in their
authored order.

### Measured win

Collection alone (serial, clean tree): **9,591 tests collected in 29.7 s**
(wall 34.9 s). Each xdist worker pays this independently, but concurrently — so
it is a fixed ~30 s floor on any parallel run, not a per-worker multiplier of the
wall clock.

Measured on the **same clean tree**, same deselect, back-to-back, quiet box
(`n=4` chosen because it mirrors a 4-vCPU GitHub ubuntu runner):

| run | wall | pytest-reported | result |
|---|---:|---:|---|
| serial | **2618.1 s** | 2449.7 s | 15 failed, 9532 passed, 40 skipped |
| **`-n 4 --dist loadfile`** | **897.4 s** | 830.3 s | 16 failed, 9531 passed, 40 skipped |

**Speedup at 4 workers: 2.92× (73 % parallel efficiency).** Ideal would be 655 s;
the 243 s gap is per-worker collection (~30 s, concurrent) plus load imbalance.

Projected onto the CI cells (applying the measured 2.92×):

| cell | today | projected | |
|---|---:|---:|---|
| ubuntu py3.10 | 25.2 min | **8.6 min** | ← wall-clock driver |
| ubuntu py3.12 | 23.4 min | 8.0 min | |
| windows py3.12 | 18.1 min | 6.2 min | |
| macos-14 py3.12 | 13.9 min | 4.8 min | (3-core runner → `-n auto` gives 3, so expect somewhat less) |

**The CI wall clock goes 25.2 min → ~8.6 min: a ~16.5-minute saving per run.**

#### Parallelism exposed one real latent defect — and it is worth fixing on its own

The n=4 run had **one extra failure** the serial run did not:

```
FAILED tests/test_signal_processing_rfft.py::test_both_paths_registered
```

All 15 serial failures reproduce identically under xdist; this is the only
divergence. The cause is a genuine (currently invisible) coupling:

```python
def test_both_paths_registered():
    assert path_registry.has_path("rfft", PATH_A)
    assert path_registry.has_path("rfft", PATH_B)
```

`test_signal_processing_rfft.py` **never calls `warmup_all()`** (verified: zero
occurrences in the file). In a single serial process the registry happens to be
populated because some *other* test module imported the registering path first.
In an isolated worker it is not. **The test passes today by accident.**

This is exactly the "orphan-registration bug class" that `warmup_all()`'s own
docstring says it exists to close (the v0.5.0rc9 bus miss). Adding
`warmup_all()` to that file makes the assertion **stronger** — it would then
genuinely verify registration instead of depending on another file's import
side effect. It is a one-line fix and it is listed as **P1a** below.

### The load-balancing caveat that matters

With one file at 453 s (`test_qm_so8_triality_c_rc146.py`), **`--dist loadfile`
cannot go faster than that file.** It is a hard floor on the parallel wall clock.
This is why proposal **P2** (split that file's parameterisation so its six tests
can spread across workers) is ranked directly after xdist — the two compose, and
without P2 the xdist win saturates.

---

## 7. The 1.81× cell spread — decomposed exactly

Using the CI figures as given:

| cell | seconds |
|---|---:|
| ubuntu-latest py3.10 | 1510 |
| ubuntu-latest py3.12 | 1406 |
| windows-latest py3.12 | 1088 |
| macos-14 py3.12 | 834 |

Two **controlled** comparisons isolate the two variables:

- **Interpreter, hardware held fixed** (ubuntu 3.10 vs ubuntu 3.12):
  1510/1406 = **1.074× (+7.4 %)**
- **Hardware, interpreter held fixed** (ubuntu 3.12 vs macos-14 3.12):
  1406/834 = **1.686× (+68.6 %)**

**1.074 × 1.686 = 1.811**, and the observed full spread is 1510/834 = **1.811**.
The decomposition is exact — there is no residual to explain.

**Answer: ~90 % of the spread is runner hardware, ~10 % is the interpreter
version.** It is not a py3.10-only code path, and it is not `tomli`.

A secondary but informative reading: two interpreter generations (3.10 → 3.12)
normally buy ~20–25 % on pure-Python bytecode. Getting only **7.4 %** says a
large share of this suite's time is **not** in the Python interpreter — it is in
native C calls, subprocess startup, and I/O. That is consistent with §3 (the head
is dominated by C-parity differential tests) and it caps how much any
interpreter-level optimisation can ever return.

---

## 8. SEPARATE FINDING — the flagged `test_genome_census_rc267` 240 s / core dump: **NOT REPRODUCED**

Reported: `test_genome_census_rc267.py` exceeds 240 s and dumps core; claimed
pre-existing on `origin/main` via a `genome.py` swap.

**Measured on a clean, consistent `rc280` tree with a `.so` rebuilt from the
live C source (so the native `srmech_genome_section_counts` symbol is genuinely
present — verified via `nm -D`):**

| run | result |
|---|---|
| `test_genome_census_rc267.py` alone, **no timeout** | **10 passed in 1.09 s** (wall 1.83 s, peak RSS 74 MB) |
| `test_plasmid_section_counts_rc280.py` alone, no timeout | **18 passed in 1.96 s** (wall 4.81 s, peak RSS 101 MB) |
| entire `test_genome_*` + `test_plasmid_*` cluster (457 tests) | **457 passed in 54.06 s**, peak RSS 390 MB, **no crash** |

No hang, no core dump, no failure, at any of isolated / paired / full-cluster
scope. Peak RSS across the *whole* 9,551-test serial run oscillated 248–420 MB
with **no monotonic growth**, so the OOM-under-memory-pressure hypothesis is not
supported either.

**Verdict: not reproducible on `main` at rc280.** I cannot confirm it as
pre-existing.

### A concrete alternative explanation — and I demonstrated it on myself

The symptom set (very slow, then dies, on genome tests) is exactly what a
**stale/mismatched native library** produces. It happened to me during this
investigation: my first snapshot's `.so` predated the `section_counts` work, and
that single mismatch produced **60 spurious failures**, including the entire
`test_genome_native_dispatch_rc153` block and every `*_byte_identical` genome
comparison — plus it pushed `test_eigvals_complex_random_byte_identical` past a
120 s timeout because the comparison fell back to a pure path that never returns
in reasonable time.

The rc281 agent's stated control — swapping in `origin/main`'s `genome.py` —
**would not have removed either confound**, because it changes only one Python
file: their worktree's compiled `.so` and their new `test_genome_amplify_c_rc281.py`
both remain in the run. So that control does not establish "pre-existing".

**Recommended discriminating steps** (for whoever owns this, not done here):
1. In the rc281 worktree, `nm -D libsrmech.so | grep section_counts` and compare
   the library's build timestamp against `c/src/srmech_genome.c`. A stale `.so`
   explains the whole symptom class.
2. Rebuild the `.so` from that worktree's own C source, then re-run.
3. If it still dumps core, capture *which layer*: run under
   `gdb --args python -m pytest ...` or set `ulimit -c unlimited` with a file
   `core_pattern`; a native frame in `libsrmech.so` confirms a C defect, a pure
   Python traceback does not.
4. Only then compare against `main` **with a `.so` built from `main`'s C source**.

**On the runtime question specifically:** since the file measures 1.09 s here,
it is **not** the dominant contributor to the 25-minute wall clock. If it truly
takes 240 s in the rc281 worktree, that is **a crash that also happens to be
slow**, not a scheduling problem — and it needs its own task regardless of
anything in §10.

---

## 9. SEPARATE FINDING — C-side static arena: 39.9 MB BSS, 6 MiB memset per call, not reentrant

Found while chasing §8. In `c/src/srmech_genome.c` (~line 6099):

```c
static unsigned char g_sc_arena[SRMECH_GENOME_SC_ARENA_BYTES];   /* 32 MiB */
static sc_slot_t     g_sc_slots[SRMECH_GENOME_SC_HASH_SLOTS];    /* 2^18 × 24 B = 6 MiB */
static unsigned char g_sc_win[SRMECH_GENOME_SC_WINDOW_BYTES];    /* 64 KiB */
static size_t        g_sc_n_ids;
```

**Measured:** the built library's `.bss` is **39,911,536 bytes (39.9 MB)** —
confirming these four objects dominate the library's static footprint.

Three observations, offered as findings rather than as a proposed change:

1. **6 MiB zeroed on every call.** `srmech_genome_section_counts()` opens with
   `memset(g_sc_slots, 0, sizeof(g_sc_slots))` — a fixed 6 MiB write **regardless
   of genome size**. For the small fixtures the tests use, this overhead dwarfs
   the actual work. It is a per-call constant, not a leak, and not quadratic.
2. **Not reentrant.** Four mutable process-global objects mean two concurrent
   calls corrupt each other. This is safe under `xdist` (separate processes) and
   safe single-threaded, but it sits uneasily beside the "reentrant C core"
   (#772) claim in `docs/srmech/CLAUDE.md`, and it is a genuine hazard for any
   threaded host embedding `libsrmech`.
3. **39.9 MB of BSS is paid by every process that loads the library** — including
   each xdist worker and each of the 36 test subprocesses. It is demand-paged, so
   the resident cost is lower than the virtual, but it is not free.

These look like consequences of honouring **JPL Rule 3 (no dynamic allocation)**
by promoting buffers to file scope. That is a legitimate trade; the point here is
only that the trade has a measured cost and a reentrancy consequence that are
currently undocumented. **No change proposed** — flagging for the C owner.

---

## 10. Ranked proposals

Ordered by (estimated win) ÷ (risk × blast radius). **Nothing here reduces
coverage; every assertion in the suite survives every proposal.**

### P0 — make `test_c_bus_wire_is_decode_splice_recoverable`'s parametrize deterministic

**Prerequisite for P1, and worth doing on its own merits.** One line
(`tests/test_bus_cipher_transport_c_rc179.py:97`) currently calls
`os.urandom(2000)` at collection time, which makes the collected test-ID set
non-deterministic across processes. See §6 for the diagnosis and the exact fix.

- **Win:** none directly — but it is the *only* thing standing between this suite
  and P1.
- **Risk:** very low. Coverage is unchanged and the fuzzing gets strictly better
  (re-randomises per run instead of once per collection).
- **Touches:** one line in one test file.
- **Note:** a collection-time `os.urandom` is also a latent reproducibility
  problem independent of xdist — a failure today cannot be re-run, because the
  payload that triggered it is gone. Worth a lint rule if one is ever added.

### P1 — adopt `pytest-xdist` with `--dist loadfile` — **the single biggest lever**

- **Win: MEASURED 2.92× at `-n 4`** (2618 s → 897 s on the same tree, same
  deselect, back-to-back). Projects the CI wall-clock driver from **25.2 min to
  ~8.6 min**. This is the dominant lever by a wide margin — larger than every
  other proposal in this note combined.
- **Blocked by P0** — verified empirically: `-n 4` and `-n 8` both abort during
  collection until P0 lands.
- **Risk:** low, once P0 is in. The rest of the blocker audit in §6 came back
  clean, and `loadfile` keeps each file's tests together and in order, which
  neutralises the `chdir`/`environ` cases.
- **Touches:** `pyproject.toml` (`pytest-xdist` in the `dev` extra),
  `.github/workflows/srmech-ci.yml` (`pytest tests/ -q -n auto --dist loadfile`).
  No test file changes beyond P0.
- **Coverage:** unchanged — same tests, same assertions, distributed.
- **Ratchets:** unaffected. Every ratchet (`test_jpl_audit`, rosetta
  completeness/transitive, `stop_list`, `non_compute owed`, the `tools.total`
  pins) reads process-local or read-only state. Each worker is a fresh process
  with its own registry, so a count pin sees exactly the same registry it sees
  today.
- **Platform parity:** unchanged — all four cells still run the full suite.
- **Caveat:** bounded below by the slowest single file (453 s) until P2 lands.

### P1a — add `warmup_all()` to `test_signal_processing_rfft.py`

Surfaced by the P1 measurement (§6): `test_both_paths_registered` passes serially
only via another module's import side effect, and fails in an isolated worker.

- **Win:** none directly; it is a **correctness** fix that P1 requires, and it
  strengthens the assertion (verifies registration rather than assuming it).
- **Risk:** very low — one line, and `warmup_all()` is idempotent (measured
  0.07 ms/call, §4).
- **Touches:** one test file.
- **Coverage:** strictly increased in rigour; nothing removed.

### P2 — let `test_qm_so8_triality_c_rc146.py` spread across workers

At **453 s / 19.8 % of the suite in one file**, this is both the largest single
contributor *and* the eventual floor on P1's win.

- **Quantified:** under `--dist loadfile` no parallel run can finish faster than
  its slowest file. At the measured serial total of 2618 s that floor starts to
  bind at **n ≈ 5.8 workers** (2618/453). So at `-n 4` it is *not yet* the
  limiter — which is why P1 already returns 2.92× without it — but on any runner
  with ≥ 6 cores, or after other work lands, this file becomes the wall.
- **Win:** unlocks scaling past ~6 workers; on an 8-core runner this is the
  difference between ~453 s and ~330 s.
- **Options, in order of preference:**
  1. Keep `--dist loadfile` globally but mark this one file for distribution by
     test (xdist supports per-test distribution via `--dist load` group markers),
     **if** its tests are mutually independent — they appear to be (four are
     independent `native_equals_forced_pure` parameterisations).
  2. Or split the file into 2–3 files along its existing parameter axis.
- **Risk:** low-medium. Requires confirming the six tests share no
  module-level mutable state. **Must not** change what is asserted.
- **Touches:** one test file (split only — no assertion changes), possibly a
  marker registration in `pyproject.toml`.
- **Coverage:** identical assertions; only their file/worker placement changes.

### P3 — cache the rosetta ledger walk in `conftest.py`

- **Win:** removes 6 of 7 full `pkgutil` package-walks, and stops re-parsing the
  same function bodies across transitive walks. Expected to take the annex/rosetta
  ratchet files from ~14 s each toward low single digits.
- **How:** `@functools.lru_cache(maxsize=None)` on `rosetta_live_objects()` and
  `rosetta_load_classification()`; memoize `_rosetta_local_imports(fn)` by
  `fn.__code__`; hoist `seen_code` in `rosetta_reached_ledger_ops` into a
  shared memo so a function reachable from many roots is parsed once.
- **Risk:** **low, but requires care** — the cache must be keyed so that a test
  which *mutates* the registry (`register_profile_tools`) cannot observe a stale
  live-object map. The 4 files that mutate the registry do so for tool entries,
  not for module-level callables, so `rosetta_live_objects()` is safe to cache;
  this must be asserted, not assumed, when implementing.
- **Touches:** `tests/conftest.py` only.
- **Ratchets:** semantics **unchanged** — same objects walked, same ledger rows
  compared, same failure on drift. Caching changes *when* the walk happens, not
  *what* it concludes.

### P4 — batch the 9 `*_numpy_free_reachable_*` subprocess tests

Nine files each spawn a subprocess that imports srmech (1.18 s) to assert
"imports and runs with numpy absent". `test_octonion_cluster_numpy_free_reachable_rc122`
alone is **83.3 s**.

- **Win:** ~8 interpreter starts plus 8 × 1.18 s of import, and whatever the
  83.3 s case is doing beyond that.
- **How:** one subprocess running all nine reachability probes, still asserting
  each independently and still reporting per-probe failure.
- **Risk:** medium — the *point* of these tests is a genuinely clean interpreter
  with numpy absent. Batching preserves that (still one clean subprocess) but
  loses per-test process isolation between the nine probes. If any probe mutates
  import state, that must be surfaced rather than papered over.
- **Coverage:** the same nine assertions must still exist and still fail
  independently. If that cannot be preserved, **do not do this** — P1/P2 already
  carry the bulk of the win.

### P5 — investigate the two timeout-capped tests for an rc280-style algorithmic fix

`test_eigvals_complex_random_byte_identical` and
`test_rank2_kernel_sweep_never_yields_a_false_zero` both exceeded 120 s and are
bounded only by the timeout, so their true CI cost is unmeasured.

- **Win:** unknown, potentially large — rc280's precedent was 115 s → 10 s.
- **Risk:** low to investigate; any actual change must preserve the sweep's
  falsification power (these are soundness batteries — narrowing the sweep *is* a
  coverage reduction and is out of scope).
- **Note:** re-measure these on a **correct** `.so` first; at least one was
  inflated by my stale library (§1).

### P6 — add `--timeout` to CI

Not a speed-up; a diagnosability fix. A hung test currently burns the full job
budget and, per §8, a killed test may not appear in duration output at all —
which is precisely how a 240 s test can hide from `--durations`.

- **Touches:** `pyproject.toml` (`pytest-timeout`), CI invocation.
- **Risk:** low, but the timeout must exceed the slowest legitimate test
  (currently ≥ 120 s locally, so pick ≥ 600 s to avoid false failures on the
  slower ubuntu cell).
- **Caveat worth knowing:** `pytest-timeout`'s default SIGALRM method **cannot
  preempt a long-running native C call** that never returns to the interpreter.
  For native-heavy tests the `thread` method is the one that actually fires.

---

## 11. Explicitly NOT proposed

- **Do not collapse the 50 `tools.total` count-pins.** Measured at ~20 ms total
  (§4). The refactor is pure churn with no measurable win, and it would cost
  per-rc locality: today each rc's registration test fails *in that rc's own
  file* when its op vanishes. If it is ever done for tidiness rather than speed,
  the constraint is: keep each file's `"<op name>" in names` assertion (cheap,
  specific, and what actually localises the failure), and move only the single
  global `== N` integer to one canonical test — the pin must still exist and
  still fail on drift.
- **Do not trim a CI cell or shard by platform.** The measured spread (§7) is
  hardware, not coverage-bearing behaviour; dropping the py3.10 cell would save
  no shared minutes (cells run in parallel) and would forfeit the floor-version
  guard that the workflow comments say it exists for. A Windows-only or
  py3.10-only bug must stay catchable.
- **Do not reduce fuzz iteration counts.** The ~30,000 iterations are the
  falsification power of the soundness batteries. Parallelise them; do not shrink
  them.

---

## 12. Reproduction

All measurements are reproducible from this repo:

```bash
# native library (must match the Python tree — see §1/§8 on staleness)
cmake -S docs/srmech -B /tmp/srbuild -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/srbuild -j8
cp /tmp/srbuild/libsrmech.so docs/srmech/python/srmech/_native/

cd docs/srmech/python
python3 -c "from srmech.amsc import _native; print(_native.HAS_NATIVE)"   # must be True

# the load-bearing measurement
python3 -m pytest tests/ -q --durations=50 --timeout=120 -p no:cacheprovider

# the §8 re-test
python3 -m pytest tests/test_genome_census_rc267.py -q
python3 -m pytest tests/test_genome_*.py tests/test_plasmid_*.py -q --durations=10

# the §6 measurement
python3 -m pytest tests/ -q -n 4 --dist loadfile --timeout=600
```

Run from a **native** filesystem (not a `/mnt/<drive>` 9p mount) and on a quiet
box; both distort the ranking badly enough to invalidate conclusions.
