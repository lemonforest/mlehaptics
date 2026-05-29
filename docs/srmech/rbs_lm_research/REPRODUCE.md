# REPRODUCE — get-ready harness for the fixed srmech rcN

Purpose: re-run the recent srmech-native experiments (R-RBS-LM-126..135) against a
**new srmech rc** and confirm bit-exact reproduction, or surface any changed number,
the moment the fixed package lands. Built 2026-05-29 (baseline: srmech 0.5.0rc8).

## What's insulated from the §10 srmech-mcp bugs

The two MCP bugs (UPSTREAM_NOTES §10.1 `naming_lookup` uncallable, §10.2
`klein4_random` non-reproducible-via-MCP) are in the **MCP wrapper layer**, NOT the
package math. Our work uses the **srmech package** exclusively:
- `srmech.amsc.laplacian.{dense_laplacian, hermitian_eigendecompose, jacobi_eigvals}` (Class L)
- `srmech.amsc.hdc.{klein4_*, similarity, bundle}` — `klein4_random(D, rng)` is always
  called with an **explicitly seeded** `np.random.default_rng(...)` (the package keeps
  the rng param; only the MCP wrapper dropped it), so determinism holds.
- `srmech.amsc.format.sha256_bytes`, `load_descriptor`, `descriptor_hash`.

So we EXPECT every experiment to REPRODUCE bit-exact under the fixed rcN — unless
rcN changes package math (which is exactly what `reproduce.py` is here to catch).

## When the fixed rcN arrives

Per CLAUDE.md TestPyPI-rc discipline — verify in a CLEAN venv OUTSIDE the source
tree (source-tree namespace shadowing silently loads `_native.py` without the
`.so`/`.dll`, giving a spurious `HAS_NATIVE=False`):

```bash
python -m venv /tmp/verify_srmech_rcN/venv && . /tmp/verify_srmech_rcN/venv/bin/activate
pip install --no-cache-dir \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    "srmech==0.5.0rcN"            # the fixed rc
python -c "from srmech.amsc._native import HAS_NATIVE, NATIVE_ABI_VERSION; \
           import srmech; print(srmech.__version__, HAS_NATIVE, NATIVE_ABI_VERSION)"
# then, from this directory:
/tmp/verify_srmech_rcN/venv/bin/python reproduce.py        # all 10 experiments
/tmp/verify_srmech_rcN/venv/bin/python reproduce.py 134 135 # subset by substring
```

## Interpreting the report

- **REPRODUCED** — every measured number (and the catalog `descriptor_hash`) matches
  the committed baseline; only version/timing fields differ. Determinism held across
  the bump — the discipline's promise kept.
- **CHANGED** — a result moved. Investigate: an intended package improvement (e.g. a
  numerically-better eigensolver) vs a regression. The report names the first
  differing record + the changed keys.
- **ERROR** — a script failed under rcN. A break to report upstream (UPSTREAM_NOTES).
- **NO-BASELINE** — no committed baseline (a newly-added experiment); recorded fresh.

## Baseline self-check (rc8, 2026-05-29)

`reproduce.py 130 134 135` → **3/3 REPRODUCED bit-exact** on the baseline rc8 (the
harness re-runs a script and diffs the fresh NDJSON against `HEAD`). This confirms
(a) the harness logic and (b) that the experiments are deterministic, before any rc
bump.

## rc14 validation (2026-05-29) — the fixed package, bit-exact

`reproduce.py` (all 10) against **srmech 0.5.0rc14** (the fixed package with §10.2
klein4_random `seed`, §10.1 root cause, and the 28-dim = 𝔰𝔬(8) packaging):
**every measured number reproduced bit-exact.** 4/10 reported REPRODUCED outright;
the other 6 reported CHANGED in `descriptor_hash` ONLY — a baseline-staleness
artifact (the catalogs grew sections across the F166→F173 steps *after* those
earlier NDJSONs were first committed, so their recorded catalog-hash predated the
final catalog). Verified by an all-keys diff: the ONLY differing field across all 6
was `descriptor_hash`; no numeric field moved. The native C path (Class-L
eigendecomp, klein4 ops) is version-stable — that is why the science survived the
rc8→rc14 bump. This re-baseline commit re-syncs all NDJSONs to rc14 + current catalog
hashes, so future `reproduce.py` runs (rc15+) compare cleanly with no hash false-alarm.

## The manifest (`reproduce.py` MANIFEST)

| script | output NDJSON | what it measures |
|---|---|---|
| R-RBS-LM-126 | inference_step1_context | F166 Step 1 context-encoder capacity |
| R-RBS-LM-127 | inference_step2_distribution | Step 2 conditional distribution vs bigram |
| R-RBS-LM-128 | inference_step3_temperature | Step 3 temperature / recall↔diversity |
| R-RBS-LM-129 | inference_step4_loop | Step 4 autoregressive loop coherence |
| R-RBS-LM-130 | inference_step5_instrument | Step 5 instantiable substrate + determinism |
| R-RBS-LM-131 | emergent_perplexity_resolution_depth | F168 resolution-depth profile |
| R-RBS-LM-132 | storage_vs_expression_two_axis | F169 confound-controlled two axes |
| R-RBS-LM-133 | translation_invariance_core | F171 core invariance (n-gram + shape) |
| R-RBS-LM-134 | srmech_native_spectral_invariance | F172 Class-L eigenspectrum invariance |
| R-RBS-LM-135 | isolate_content_storage | F173 envelope-subtraction + 28D chirality |

Drops `srmech_version` / `abi_version` / `has_native` / `build_seconds` /
`parser_version` from comparison (they legitimately change across a version bump);
everything else — every number + `descriptor_hash` — must match.
