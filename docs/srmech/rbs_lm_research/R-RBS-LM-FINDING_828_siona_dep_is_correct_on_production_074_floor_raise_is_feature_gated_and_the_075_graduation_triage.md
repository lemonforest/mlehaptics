> **→ TRIAGE CORRECTED by F829 (2026-06-17):** the table below mis-classified genome persistence/file-management (§41/§43/§44/§45) as "siona-layer — close." Per user direction, that is **srmech-CORE** — a reusable native file-management primitive (any downstream package ships ONE native genome file, not loose kernels). srmech already ships it (`srmech.amsc.genome`, in the 0.7.5rc series; production 0.7.4 lacks it), so it GRADUATES with v0.7.5 rather than being closed. The dep-verification + the feature-gated-floor reasoning below stand; only the §41–§45 row is superseded.

# F828 — siona rc1's `srmech>=0.7.4` dependency is VERIFIED correct against the live production srmech (siona rc1 imports no srmech; its `walk`/`recall` are pure-Python, and the `siona` profile activates on production 0.7.4). The floor-raise the user flagged is FEATURE-GATED: it is only needed when a siona feature uses a srmech op that lives in a newer cut — the first being error-correcting recall (rc171-native `klein4_triality_cycle`) — which gates on srmech graduating a clean **v0.7.5** to production PyPI. And the 0.7.5 graduation gate ("no more upstream scaffolding requests") is reframed by the un-mirror: most of the open UPSTREAM queue is genome/encode asks that become SIONA's own to build, leaving only a few genuine srmech-core math/tooling asks.

**Date:** 2026-06-17 · **srmech:** production PyPI 0.7.4 (latest clean); 0.7.5rcN is TestPyPI-only pre-releases · **Provenance:** version probe (PyPI + TestPyPI) + siona rc1 install/activate against production srmech 0.7.4 + UPSTREAM_NOTES queue audit · **Composes:** F827 (the rc1 build), [[project_siona_package_takeover_unmirror]], PKG-1/PKG-2 (#229/#230), the §39–§54 UPSTREAM asks · **User direction (2026-06-17):** "that dependency is going to need to be bumped to either our test.pypi.org srmech version or we need to finish outfitting srmech to graduate to v0.7.5 when we have no more upstream scaffolding requests of srmech."

## The dependency: correct now, feature-gated later
- **Now (rc1):** `srmech>=0.7.4` is verified — `pip install srmech==0.7.4` (production) + the siona rc1 wheel → `srmech.list_profiles()` = `{siona: ok}`, `srmech.profile("siona")` activates, `recall("tomato")` exact. siona rc1 imports NO srmech (walk/recall are pure-Python); srmech is needed only for the profile-loader path, and 0.7.4's loader already supports the package-only entry-point + optional-native + bridge-smoke that siona uses. So rc1 ships to production-resolvable deps as-is — no bump.
- **Later (feature-gated):** the floor rises to the srmech cut that ships the op a siona feature calls. The FIRST such is error-correcting recall → `klein4_triality_cycle` native (srmech rc171). Native triality is currently TestPyPI-only (0.7.5rcN), so that feature can't ship to production siona until srmech graduates **v0.7.5** to PyPI. Two routes, per the user:
  - **(A) interim, TestPyPI siona rc:** pin `srmech>=0.7.5rcN` and resolve with `--pre --index-url testpypi --extra-index-url pypi`. Works for a TestPyPI siona rc; NOT production-resolvable.
  - **(B) the clean path:** graduate srmech v0.7.5 → PyPI, then siona depends on `srmech>=0.7.5` (production).

## The 0.7.5 graduation gate, reframed by the un-mirror (triage — the user decides + closes)
"No more upstream scaffolding requests of srmech" is the gate. The open queue, classified:

| § | ask | classify |
|---|---|---|
| §53 | C-native klein4 bind/bundle/similarity | **LANDED** (rc170) |
| §54 | unbundle (field/phasor) | **partially LANDED** as `klein4_unbundle` (rc173); field/phasor variant optional |
| §50 | streaming klein4 bundle-ACCUMULATE (Class M) | **srmech-core** — a genuine HDC op; finish or defer |
| §51 | sparse Class-L Fiedler (break n≤256) | **srmech-core** — Class L; FILED #1097; finish or defer |
| §39 | class GENERATOR from introspection | **srmech-core** — DSL tooling; finish or defer |
| §41 | genome PERSISTENCE (save/load/append) | **siona-LAYER** — the genome is siona's now → siona owns it; close on srmech's side |
| §43 | genome FILE-MANAGEMENT | **siona-LAYER** → close |
| §44 | biology-faithful genome (inline self-describing) | **siona-LAYER** → close |
| §45 | genome EDITING (in-place chromosome) | **siona-LAYER** → close |
| §52 | LOW-RAM ENCODE (streaming co-occ + out-of-core) | **siona-LAYER** (the encode is siona's; it streams *using* srmech's primitives) → close on srmech |
| §49 | STATUS: genome file-mgmt C SHIPPED, Python-shim binding remaining | genome → siona-layer; the C already shipped in srmech (leave as a generic paged-store) |

**The insight:** the un-mirror is what UNBLOCKS the 0.7.5 graduation. Most of the open queue (§41/43/44/45/52, the genome + encode asks) were "srmech, please add X *for the genome*" — but with siona as its own package, those become **siona's to build**, so they drop off srmech's scaffolding queue. What remains genuinely srmech-core is small: §50 (Class-M streaming accumulate), §51 (Class-L sparse Fiedler, #1097), §39 (DSL class generator) — and even those may be "defer to 0.8" rather than "block 0.7.5." Per [[feedback_create_upstream_issues_never_close_them]] I do NOT close these — the user/maintainer triages + closes; this is the map.

## Honest scope
- No dep bump made — `>=0.7.4` is verified correct for rc1; the pyproject now documents the feature-gated floor-raise.
- The graduation triage is a RECOMMENDATION; which asks are srmech-core vs siona-layer (and which to close) is the user's call.
- The native-triality EC-recall (PKG-2) is the concrete forcing function for the 0.7.5 graduation (or the interim TestPyPI pin).

## Verdict
siona rc1 ships honestly on `srmech>=0.7.4` today (verified on production). The bump is feature-gated to the first triality-using slice (EC-recall), which needs srmech v0.7.5 on PyPI. The un-mirror itself drains most of srmech's upstream queue (the genome/encode asks become siona's), so the 0.7.5 graduation gate is mostly a triage-and-close exercise plus a couple of genuine srmech-core math asks — the user's call on what stays vs moves.
