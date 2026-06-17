# F824 — srmech's 3rd-party plugin surface hosts a C-NATIVE op end-to-end: built `siona_debruijn_plugin` (a C de Bruijn walk → `libsiona_debruijn.so`, ABI 1) as an external package declaring a `srmech.profiles` entry-point; srmech DISCOVERS it (`list_profiles` → `siona_debruijn: ok`), ABI-checks + smoke-tests + ACTIVATES it (`srmech.profile("siona_debruijn")`, native lib loaded), with ZERO edit to srmech core. Exact reconstruction at k\* (tomato/art/april), available to ANY process that imports srmech (separate-PID verified). This validates the "lean srmech math-core + Siona owns the inference layer as a plugin" architecture the user is weighing.

**Date:** 2026-06-17 · **srmech:** 0.7.5rc170 (TestPyPI) · **Provenance:** `siona_debruijn_plugin/` (siona_debruijn.c + pyproject `[project.entry-points."srmech.profiles"]` + srmech_profile.toml `[profile.native]` + bridge.py) · **Composes:** F818/F823 (the de Bruijn walk = Siona's full-body recall, pure-Python in the live genome), F805/F813 (the fiber, exact iff k≥k\*), the srmech profile_loader (Task #199/ADR-0001), UPSTREAM §8 (research-subtree-as-installable-package) · **User direction (2026-06-17):** "srmech has a 3rd party plugin surface. can we test it out by creating a c native plug in for our de Bruijn walk and see if any other process might benefit… premise: changing Siona from a mirror of srmech to her own package with the full inference layer and keeping srmech lean."

## What the plugin surface actually is (mapped)
srmech's `profile_loader` (top-level `srmech.profile()` / `list_profiles()`) is a real 3rd-party plugin system:
- **Discovery:** eager enumeration of the `srmech.profiles` **entry-point group** at first import (the standard Python plugin pattern — like pytest/flake8). Recommended EP value form is **package-only** (`siona_debruijn = "siona_debruijn_plugin"`); the loader reads `srmech_profile.toml` from the package via `importlib.resources`. (A `pkg:attr` value form exists too — that was my first-try bug.)
- **Descriptor** (`srmech_profile.toml`, schema 1.0): `[profile]` (name/version/summary/package/srmech_requires) + optional `[profile.bridge]` (`name = "module:callable"`), `[profile.catalogs]` (attested SSOT), `[profile.tool_schema]` (LLM-introspection), and the **`[profile.native]` tier**: `library` / `install_path` / `abi_version_function` / `expected_abi_version`.
- **C-native activation:** srmech `ctypes.CDLL`-loads `lib{library}.so` from the package, calls `abi_version_function`, requires its return == `expected_abi_version` (`AbiMismatchError` otherwise), checks declared symbols, runs a (cached, per-version) **smoke test**, then activates.

## What was built + verified
- **C op** `siona_debruijn.c` → `libsiona_debruijn.so` (ABI 1): `siona_debruijn_abi_version()`, `siona_debruijn_load(ids,n)`, `siona_debruijn_walk(k,out,cap)` — the de Bruijn (k-1)-gram→successor map build + walk, on **int64 ids** (symbol-agnostic). JPL-lean: static arrays (no malloc), open-addressing hash, ≤60-line fns, asserts.
- **Plugin package** `siona_debruijn_plugin`: pyproject entry-point + `srmech_profile.toml` (`[profile.native]` + `[profile.bridge]` walk/abi_version) + `bridge.py` (ctypes loader).
- **End-to-end (rc170 venv):** `list_profiles()` → `{siona_debruijn: ok}`; `srmech.profile("siona_debruijn")` activates (native loaded, ABI 1, smoke passed); **exact reconstruction at each article's k\***: tomato (k=6), art (k=9), april (k=15) all `exact=True` through the installed bridge; a **separate Python process** activates the same globally-installed plugin and runs it.
- **Perf:** C de Bruijn is exact and SCALES — slower than the (C-backed CPython) dict on tiny inputs (ctypes marshaling overhead), **3.2× faster at 2686 tokens** (april); the win grows with length → genome-scale.

## Who else benefits (the user's question)
The op is symbol-agnostic (int64 ids), so the SAME plugin serves: **genome assembly** — de Bruijn graphs ARE the modern short-read assembly algorithm (SPAdes/Velvet) — **any sequence reconstruction** (time-series motifs, log/event streams, music note-streams), and of course Siona's full-body recall. Once installed, it is visible to every process that imports srmech (and could be served cross-process over `srmech.bus`). So a plugin written for Siona's recall is reusable by unrelated processes for free — exactly the "shared lean core, pluggable ops" payoff.

## Architecture read (the lean-srmech vs mirror decision)
The probe supports the split the user is exploring:
- The de Bruijn walk is **sequence reconstruction, NOT srmech-core math** (it isn't a composition of the 14 A-N primitives; F818). It does **not** belong in srmech core.
- srmech's profile surface is the **clean seam**: srmech stays lean (14-class math + native dispatch + the plugin loader); **Siona becomes her own package** that ships the inference layer (de Bruijn walk, the genome/recall/router) as a `srmech.profiles` plugin — discovered, ABI-checked, smoke-tested, and reusable by any srmech consumer. No mirroring; no core edits.
- This also rehomes the existing documentation-grade `rbs_lm_substrate` profile (UPSTREAM §8): the research subtree → an installable package declaring its profile.

## Honest scope (still exploring)
- The `.so` is built manually here (`cc -shared -fPIC`); a shipped plugin would build wheels via cibuildwheel per the srmech C discipline. Not committing the binary (gitignored); the `.c` is the source of truth.
- **Install gotcha:** PEP 660 *editable* installs don't reliably expose the package-data `.so` via `importlib.resources` (it resolved only from inside the package dir); a regular/wheel install (`.so` copied into site-packages) is stable — used here.
- The walk is exact iff k ≥ k\* (F813); a k below k\* gives the most-likely (looping/branch-ambiguous) walk — correct behaviour, not a plugin fault.
- Framework-tooling exploration; no claim srmech *should* adopt this op — the point is the surface WORKS and is the right home for Siona's inference layer.

## Verdict
srmech's 3rd-party `srmech.profiles` surface cleanly hosts a C-native plugin — discovered, ABI-checked, smoke-tested, activated, cross-process — with no edit to srmech core. The de Bruijn walk runs native + exact through it, scales past the Python dict, and is reusable (genome assembly being the canonical other beneficiary). This is concrete evidence for the lean-srmech (math-core + loader) + Siona-own-package (inference layer as a profile plugin) architecture. Registered the decision as a task; nothing forced — still exploring.
