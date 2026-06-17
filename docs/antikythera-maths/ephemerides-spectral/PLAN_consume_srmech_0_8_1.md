# PLAN — ephemerides-spectral → srmech 0.8.1 (consume + genome-storage review)

**Date:** 2026-06-17 · **Target version:** `ephemerides-spectral 0.31.0rcN` (minor bump — consumes a major srmech graduation) · **Discipline:** TestPyPI-rc-first, then clean-tag → PyPI (human gate).

---

## Context

- **srmech 0.8.1 is LIVE on production PyPI** (MIT-licensed, numpy-free; carriers `Mat`/`Vec`/`HV` replaced ndarray; `[scientific]` extra gone; tools 310, ABI 3).
- **ephemerides-spectral** is at `0.30.0rc10`, pins **`srmech>=0.7.4`** in three files: `python/pyproject.toml:43`, `python/pyproject-pure.toml:58`, `python/ephemerides_spectral/srmech_profile.toml:40`.
- ephemerides keeps its OWN `numpy>=1.24` dependency (its `_research/laplacian.py` reference impl + `_native_bip.py` ctypes interop). srmech being numpy-free does NOT force ephemerides numpy-free — independent.

## KEY FINDING — empirical introspection settles the "breaking changes" question

Static analysis (subagent) *guessed* the eigen-consumption sites would break (`eigvecs[:, 1]`, `-fiedler_vec`, `V[r][c]`). **Probed against the live srmech 0.8.1 — they DON'T.** The `Mat`/`Vec` carriers are a deliberate numpy-reflex sink and answer every idiom ephemerides uses:

| ephemerides idiom (file) | srmech 0.8.1 result |
|---|---|
| `dense_laplacian(n, edges, weights)` | OK → `Mat` (still takes `weights=None`) |
| `symmetric_eigendecompose(L)` | OK → `(Vec, Mat)` |
| `eigvals[1]` / `eigvals[i]` iterate / `len(eigvals)` | OK (Vec) |
| `V[:, 1]` 2-D **column slice** (hawaii/mars) | OK → `Vec` |
| `V[r][c]` nested / `V[r,c]` tuple index | OK → float |
| `fiedler_vec[i]` / `-fiedler_vec` negate / `len()` | OK (Vec) |
| `rational.log1p_series_truncate` → `(int,int)` ; `exp`/`sqrt`/`sin`/`cos`/`atan2`/`atan` → float | OK (unchanged) |
| `catalog.register_attested_root(path, *, source=)` ; `list_attested_sources()` → `{ok,n_sources,adapter_class,sources}` | OK (unchanged) |

**Conclusion: the core consumption is a near drop-in.** The real risk is only edge idioms the hot-site probe didn't reach — caught by running the FULL suite (Phase 0). The feared big-bang rewrite is mostly absent.

---

## Phase 0 — VERIFY (the real gate; do FIRST)

Install ephemerides (local) + **srmech 0.8.1 (from PyPI)** + numpy; run the **full ephemerides-spectral pytest suite**. Pin srmech to 0.8.1 explicitly. Green = the carrier idioms cover everything; any red = the precise remaining break (fix narrowly). Pay attention to: the 5 catalog consumers (`hawaii_chain`, `mars_tharsis`, `saturn_rings`, `solar_rotation`, `dynamical_regime`), the `_cascade.py` wrappers, and any `np.asarray(srmech_return)` / scipy hand-off.

## Phase 1 — floor bump + annotation honesty

- Bump `srmech>=0.7.4` → **`srmech>=0.8.1`** in all THREE (pyproject.toml, pyproject-pure.toml, srmech_profile.toml). Keep the two pyprojects congruent (CI guard).
- `_research/_cascade.py` return annotations say `Tuple[np.ndarray, np.ndarray]` but now return `(Vec, Mat)` — update to honest types (or a neutral `Tuple[Any, Any]`); cosmetic, not enforced, but keep introspection honest (`[[feedback_numpy_removal_must_preserve_carrier_format...]]` spirit).
- Note MIT: srmech is now MIT; ephemerides itself relicenses to MIT under `[[project_srmech_subprojects_mit_monorepo_gpl3]]` — **fold the ephemerides MIT relicense into this arc** (its own GPL→MIT flip across pyprojects + LICENSE + headers, same as srmech 0.8.1rc1).

## Phase 2 — version bump + CHANGELOG

`0.30.0rc10` → **`0.31.0rc1`** across the 3 version SSOT (pyproject.toml, pyproject-pure.toml, `ephemerides_spectral/version.py`). CHANGELOG entry: "consume srmech 0.8.1 (numpy-free carriers — drop-in; floor `>=0.8.1`) + MIT relicense".

## Phase 3 — ship rc1 → TestPyPI + verify

Hand-push `ephemerides-spectral-v0.31.0rc1` (rc → TestPyPI auto). Verify in a clean venv: install ephemerides 0.31.0rc1 + srmech (resolve 0.8.1 from PyPI) + numpy; assert `ephemerides_spectral.__version__`, `srmech.__version__==0.8.1`, `srmech HAS_NATIVE`, `bridge.list_attested_sources()["n_sources"]`, and one ITN/cascade op (e.g. `gaussian_eigs_from_pairs` path + `find_itn_chains` / `predict_itn_accessibility`).

---

## Phase R1 — genome native-storage packaging (REVIEW / spike, go-no-go)

srmech `amsc.genome.*` = self-describing strand (`turns.bin`+`manifest.json`), chromosomes/genes, `.chr` bundles, `genome_pack/explode`, `genome_register_attested(chr_dir, amsc_root, *, source)` (one AMSC source per chromosome, composes the catalog).

**Tension (real):** a genome **leaf** is a fixed-width **Klein-4 `HV`** (sector-encoded bytes), `len(the_one)` wide — NOT a float array. ephemerides kernels are variable-width float coefficient sets (gravity SH to degree 2190; dynamical eigenvalue vectors; 6-float secular elements). Embedding raw float coefficients is lossy/awkward; padding to a max `leaf_dim` is wasteful.

**Recommended shape (subagent Option C):** the genome holds **provenance/metadata + references** (per-body chromosome, per-catalog gene; leaf = small descriptor: catalog key, epoch, `n_max`, SHA-256 of the coefficient archive), and `genome_register_attested` surfaces each as an AMSC source — coefficients stay in ephemerides' native tables. The genome becomes a **versioning/provenance checkpoint** ("which kernels were active at epoch T"), not a coefficient store.

**Smallest PoC:** `secular_elements` (51 bodies × 6 floats, fixed width) → one chromosome, `.chr` export, `genome_register_attested` → surfaces in `list_attested_sources`; round-trip equality. **Go-no-go output:** a spike report + decision; only ship a genome surface if it's clean and earns its place. **Likely a SEPARATE rc** (R-line), not rc1.

## Phase R2 — etak ↔ ITN unification (introspection CONFIRMED; class-TOML)

Introspection verdict (subagent): **etak navigation (PR #687 ETAK/BOARD/FLOCK triality, `mfo_spectral_research_notebook.md:6706`) and ephemerides `find_itn_chains` / `predict_itn_accessibility` (gateway-graph Laplacian Fiedler partition, `research/gateway_graph_laplacian.py` + `predict_itn_accessibility.py`) are the SAME structure** — hold an invariant reference frame (Class-C axis / Fiedler eigenbasis), the Class-L manifold's transport structure reveals accessible routes via Fiedler distance; Class-M bind = the k=3 triality. Shared primitives: **L (Laplacian) + C (frame) + M (bind)**.

**Per user direction** ("ephemerides may need its own `[class]` catalog TOML if we find ourselves wanting a new code path just for a different name"): do **NOT** add an `etak_*` code path alongside `find_itn_chains` — they're one cascade. Express the shared navigation cascade ONCE as an ephemerides **`[class]` catalog TOML** (`srmech.dsl.make_class` / `register_class_dir`), with `etak` and `itn` as two named views/methods over it. Prove with a DSL-class-vs-Python equivalence test (`[[feedback_prefer_config_driven_toml_classes]]`). **Likely a SEPARATE rc.**

---

## Discipline (load-bearing)

- TestPyPI rc BEFORE any clean tag → PyPI (the clean `ephemerides-spectral-vX.Y.Z` tag is the human gate; rc tags hand-pushed).
- 3 version SSOT must agree; 3 srmech-floor sites must agree; pyproject ≡ pyproject-pure (CI guards both).
- `gh pr merge --merge` (never squash). Autotag on clean semver. Scoped `git add`.
- **PREFER config-driven `[class]` TOML over a new bespoke code path whenever the only difference is a name** (`[[feedback_prefer_config_driven_toml_classes]]`).
- ephemerides relicenses GPL-3 → MIT (`[[project_srmech_subprojects_mit_monorepo_gpl3]]`).

## Open decisions (to confirm before the research phases)

1. **Genome packaging** — ship a genome surface in the 0.31.0 line (after the rc1 consumption update), or run it as a standalone spike/report first? (Real tension: leaf=Klein-4-HV vs float coefficients → likely "provenance checkpoint," not coefficient store.)
2. **etak/ITN class-TOML unification** — fold into this 0.31.0 line as a follow-up rc, or a separate arc?

**Spine that ships regardless:** Phase 0 verify → Phase 1 floor bump (+ MIT) → Phase 2 version → Phase 3 TestPyPI rc1.
