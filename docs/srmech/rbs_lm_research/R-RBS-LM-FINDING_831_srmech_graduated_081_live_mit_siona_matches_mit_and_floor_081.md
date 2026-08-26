# F831 — srmech GRADUATED: 0.8.1 is live on production PyPI, relicensed GPL-3 → MIT (verified, clean venv). siona matches: license → MIT (LICENSE file + `license="MIT"` + `license-files`), and dep floor → `srmech>=0.8.1` (the live MIT math core, which ships everything siona's roadmap needs). The siona 0.1.0rc1 wheel rebuilds with `License-Expression: MIT`, the LICENSE bundled, `twine --strict` PASS, and it activates + recalls exactly on srmech 0.8.1. This resolves the 0.7.5-graduation gate (srmech went straight to 0.8.1) and makes PKG-3 (native-genome recall) + the EC-recall production-resolvable.

**Date:** 2026-06-17 · **srmech:** 0.8.1 (production PyPI, MIT) · **Provenance:** clean-venv verify of `srmech==0.8.1` (version/native/License/surface) + siona pyproject/LICENSE/README edits + a rebuilt+verified siona wheel against 0.8.1 · **Composes / supersedes:** F828/F830 (the 0.7.5-graduation thread — now moot), F827/F829 (the un-mirror rc1 + genome-core), [[project_siona_package_takeover_unmirror]], PKG-2/PKG-3 (#230/#231) · **User direction (2026-06-17):** "srmech 0.8.1 now on live pypi. license also changed from GPL-3 to MIT and we want to do that with siona as well."

## Verified (production PyPI, clean venv — ground truth)
- `pip install srmech==0.8.1` → `srmech.__version__ == 0.8.1`; `native_status()` has_native/dispatching True, abi 3, native_version 0.8.1.
- **`License: MIT`** in the installed metadata (was GPL-3.0-or-later).
- Carries everything siona's roadmap needs: `srmech.amsc.genome` (genome_save/load/window/recall/encode_shape), `hdc.klein4_triality_cycle`, `hdc.klein4_unbundle`, the profile loader. So srmech graduated PAST the 0.7.5rc series straight to **0.8.1** — the F828/F830 "0.7.5 graduation gate" is moot; it shipped.

## siona changes (match srmech)
- **License → MIT:** added `docs/srmech/siona/LICENSE` (MIT, © 2026 Steven Kirkland); pyproject `license = "MIT"` + `license-files = ["LICENSE"]` (was `GPL-3.0-or-later`); README license line GPL → MIT. (Relicensing is the author's prerogative — same move srmech made; MIT is strictly more permissive.)
- **Dep floor → `srmech>=0.8.1`** (was `>=0.7.4`): the live MIT math core. No TestPyPI pin needed — the native genome + triality + unbundle are all in the production 0.8.1 wheel, so PKG-3 (native-genome recall) and the EC-recall (`klein4_triality_cycle`) are now production-resolvable on this single floor.

## Verified (rebuilt siona 0.1.0rc1 wheel against srmech 0.8.1)
- `python -m build` → wheel metadata: `License-Expression: MIT`, `License-File: LICENSE`, `Requires-Dist: srmech>=0.8.1`; the LICENSE ships at `siona-0.1.0rc1.dist-info/licenses/LICENSE`.
- `twine check --strict` PASSED (wheel + sdist).
- post-install on srmech 0.8.1: `srmech.profile("siona")` activates; `recall("tomato")` → k=6, exact.

## Honest scope / gated
- The siona changes are committed on the research branch (the build); the release is still the user's gate: the `siona-v0.1.0rc1` branch → its OWN PR (NOT PR #687) → tag `siona-v0.1.0rc1` → TestPyPI; clean tag → PyPI (uploads the MIT README).
- I changed siona's license metadata as directed; I did not touch srmech's license (the maintainer relicensed srmech).
- Version stays `0.1.0rc1` (rc1 not yet published — license + floor folded in pre-publish).

## Verdict
srmech graduated to 0.8.1 on live PyPI under MIT; siona now matches — MIT license + `srmech>=0.8.1` floor — verified end-to-end on the production wheel. The graduation gate is closed by the 0.8.1 ship, and PKG-3 + EC-recall are production-resolvable. rc1 is ready for its release PR on the corrected MIT/0.8.1 footing.
