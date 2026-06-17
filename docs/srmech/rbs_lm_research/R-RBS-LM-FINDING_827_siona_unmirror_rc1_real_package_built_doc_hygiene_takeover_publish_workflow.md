# F827 — the `siona` UN-MIRROR cut is built: `docs/srmech/siona` is repurposed from a metadata-only srmech co-name alias (`siona==0.0.4`, "import siona == import srmech") into Siona's OWN real package — `siona 0.1.0rc1`, a srmech PROFILE plugin (the de Bruijn recall layer) that DEPENDS on lean srmech. Builds clean (`py3-none-any` wheel + sdist, `twine check --strict` PASSED), and in a fresh venv with srmech rc173: `import siona` is a real package (has `walk`/`recall`, version ≠ srmech's), `srmech.list_profiles()` → `{siona: ok}`, `srmech.profile("siona")` activates, `recall("tomato")` reconstructs the full body exactly. Doc-hygiene'd the README + pyproject + `siona-publish.yml` comments (no longer "alias / co-name").

**Date:** 2026-06-17 · **srmech:** 0.7.5rc173 (TestPyPI; verified: `import siona` alias REMOVED, `klein4_unbundle` op present) · **Provenance:** `docs/srmech/siona/{pyproject.toml,README.md,siona/__init__.py,siona/bridge.py,siona/srmech_profile.toml}` + `.github/workflows/siona-publish.yml` comments · **Composes:** F824/F825 (the srmech.profiles plugin + the recall path), PKG-1 (#229), [[project_siona_package_takeover_unmirror]], UPSTREAM §8 (subtree-as-installable) · **User direction (2026-06-17):** "upstream srmech is removing siona as a mirror package … take over the existing siona pypi publish yml and pypi readme with corrected info … next version bump 0.x.0rc1 … rc1 needs doc hygiene + un-mirroring of srmech + the plugin object … don't use PR687 to merge test.pypi.org siona releases; rcN get their own PR."

## What the takeover found
- `siona 0.0.4` (the published package) was a **metadata-only metapackage** depending on `srmech>=0.4.6`, which bundled the in-wheel `import siona` alias. **srmech rc173 removed that alias** (verified: `import siona` → ModuleNotFoundError on rc173) and added a `klein4_unbundle` op (the F822 work, upstream).
- The infra is **already ours**: `docs/srmech/siona/` + `.github/workflows/siona-publish.yml` (tags `siona-vX.Y.ZrcN`→TestPyPI / `siona-vX.Y.Z`→PyPI; OIDC trusted-publisher set up project=siona on BOTH indices). So "takeover" = REPURPOSE these, not acquire them.

## rc1 build (the three required pieces)
1. **Un-mirroring** — `docs/srmech/siona/` is now a real package: `siona/__init__.py` (re-exports `walk`/`recall`, NOT a srmech alias), `siona/bridge.py` (the pure-Python de Bruijn walk + the F825 recall path), `siona/srmech_profile.toml` (the `siona` profile; `[profile.bridge]` walk/recall; no `[profile.native]` in rc1). pyproject: `name=siona`, `version=0.1.0rc1`, `dependencies=["srmech>=0.7.4"]`, `[project.entry-points."srmech.profiles"] siona="siona"`.
2. **Doc hygiene** — README rewritten (Siona = the grounded RBS-HDC inference instrument on srmech, with an explicit "un-mirror note"); pyproject description corrected; `siona-publish.yml` header + sanity comments corrected (no longer "alias / co-name"; added "each rcN via its OWN PR — never PR #687").
3. **The plugin object** — the de Bruijn recall plugin (F824/F825) folded in as the package's profile + bridge (pure-Python rc1; the C-native accelerator is the follow-on cibuildwheel rc).

## Verified (fresh venv, srmech rc173)
- `python -m build` → `siona-0.1.0rc1-py3-none-any.whl` + sdist; `twine check --strict` **PASSED**.
- wheel carries `siona/{__init__,bridge}.py + srmech_profile.toml` + the `srmech.profiles` entry-point.
- post-install: real package (`siona.__version__==0.1.0rc1 ≠ srmech.__version__`, has `walk`/`recall`); `list_profiles()`→`{siona: ok}`; `profile("siona")` activates; `recall("tomato")` → k=6, 390 tok, **exact**.

## Honest scope / what is GATED (the user's outward-facing actions)
- **Not published.** The actual release is the user's gate: a dedicated `siona-v0.1.0rc1` branch off `main` → its OWN PR (NOT PR #687) → merge → tag `siona-v0.1.0rc1` → the workflow auto-routes to TestPyPI. Clean `siona-v0.1.0rc1` (no rc) → PyPI is the production gate. The PyPI project README updates from this README on publish.
- These files are committed on the research branch as the BUILD; they need lifting onto the release branch for the rcN PR.
- rc1 is pure-Python; the C-native de Bruijn tier (F824) is a follow-on platform-wheel rc.
- **First consumer after rc1:** error-correcting recall (the rc171-native `klein4_triality_cycle` 2-of-3 over the de Bruijn non-unique tail, F813/F826).

## Verdict
Siona's un-mirror rc1 is built + verified: a real `siona 0.1.0rc1` package (the inference layer / srmech profile) replacing the retired srmech-alias metapackage, with corrected docs + publish workflow. srmech stays the lean math core; siona is its own package on top. The release (its own PR + tag, not PR #687) and the C-native tier + EC-recall are the queued next steps.
