# F1014 (PKG-2 build / #230) — **the siona package build: F1008–F1012 folded into `siona.infer` (Grounding + Session), the language-board layer landed as `siona.boards` (Board/ENGLISH/load_board — per-language declared operator profiles; English is board #1), the un-mirror confirmed already-done at the skeleton level (entry-point + profile toml + no re-exports), the PyPI-facing README + CHANGELOG trail written, the user's publish-gate items recorded in `PUBLISH_GATE.md` — and the smoke PASSES through the installed package: `import siona; siona.Session()` runs the F1012 session (cross-turn operand + exact-rational kernel conversion) from the wheel-shaped modules.**

**Date:** 2026-07-02 · **srmech:** 0.9.0rc97 · **Branch:** `research/rbs-lm-rolling-2` (PR #687; the *release cut* will be its OWN PR per the gate) · **Milestone:** PKG-2 (#230) — **build landed; publish remains GATED** ("almost there or all the way there") · **Files:** `docs/srmech/siona/{siona/{__init__,infer,boards}.py, siona/srmech_profile.toml, siona/tests/test_infer_smoke.py, README.md, CHANGELOG.md, PUBLISH_GATE.md}` · **Grounds / composes:** F1013/PKG-1 (the decision this implements), F1008–F1012 (the five capabilities, now package modules), F649 (the boards docstring lineage, dignity-first), `[[feedback_never_bag_of_words_even_for_testing]]` (the encoding standard is now module-level documentation + a board test), `[[project_siona_package_takeover_unmirror]]` (own-PR/own-tag discipline → gate doc). · **User direction (2026-07-02):** "continue into the PKG-2 build… check and if needed change siona from a srmech mirror to its own plugin package… PyPI-facing readme and changelog trail… publisher target → its own lemonforest/siona repo at publish time… the siona research notebook stays with mlehaptics where RTD is set up… add these to the publish gate so we keep building and hardening."

## Grounded (rc97)
```
MIRROR CHECK: already un-mirrored -- __init__ disavows the alias; imports only from .bridge; srmech.profiles
  entry-point 'siona = "siona"' + srmech_profile.toml present; srmech appears ONLY as a dependency (correct
  plugin direction). No change needed; confirmed + extended.
BUILD:
  siona/boards.py  -- Board (frozen dataclass: address/define_frames/self_verbs/verb_tools/imperatives/
                      interrogatives/strip/kernel_ops) + ENGLISH (board #1) + load_board (TOML swap)
  siona/infer.py   -- Grounding (F1008 live-registry index, refresh(), order-carrying encoding) +
                      Session (F1010 route / F1009+F1012 drive with cross-turn operands / F1011 self surface
                      with idempotent register_profile_tools / F1012 kernels, exact-rational via cyclic.gcd)
  siona/__init__.py-- exports walk, recall, Session, Grounding, Board, ENGLISH, load_board (v0.1.0rc1)
  srmech_profile.toml -- bridge surface extended: session = siona.infer:Session ; board = siona.boards:ENGLISH
  CHANGELOG.md     -- the trail: 0.0.x alias history + the 0.1.0rc1 un-mirror cut + Added/Discipline sections
  README.md        -- PyPI-facing: + inference-loop section (the live example) + language-boards section +
                      mechanism-not-knowledge note + notebook pointer to mlehaptics RTD
  PUBLISH_GATE.md  -- the user's gate items (below) + the hardening backlog checklist
SMOKE (through the INSTALLED package, editable install in the rc97 venv):
  test_boards_swap_shape PASS ; test_session_smoke PASS -- the 8-turn F1012 session (remember, kernel ingest,
  gcd(100,48)=4 cross-turn, 212F exact kernel conversion, factor, continuation '100', live help, show) runs
  from `import siona; siona.Session()`.
```

## The publish gate (recorded, NOT executed — the user's items)
1. **At publish time:** PyPI trusted-publisher target moves to its own **`lemonforest/siona`** repo (both indices); `siona-publish.yml` moves; `[project.urls]` re-point.
2. **The siona research notebook STAYS in mlehaptics** — RTD is set up there and serves the research-notebook family; only the package moves; the README links back.
3. **Release cut = its own PR** (never #687) + manual `siona-v0.1.0rc1` tag → TestPyPI; clean tag → PyPI is the human gate; clean-venv verify OUTSIDE the source tree.
4. **Hardening backlog before "ready":** paraphrase frames per board; structured operands (float/Mat/Vec/HV/kwargs); failed-run→next-candidate recovery; kernel generality (dispatch.infer hand-off); within-family re-rank; bag-regression fixtures (F1004/F1008/F1010); UDHR/Bislama parallel-invariant run; egyptian_tla board exercise; operator-board swap test; version SSOT agreement.

## Honest scope
The build folds the *proven prototypes* faithfully (the smoke replays F1012's session through the package — same results); it does not silently extend them: every known limitation moved into the gate checklist rather than being papered over. The profile-toml `session`/`board` surface entries assume the srmech profile loader smoke-tests callables generically (Session is a class = callable; verify on the loader before the cut — added implicitly under the SSOT/verify gate item). pytest isn't in the rc97 venv — the smoke ran as direct module execution; the gate's "test suite green under pytest" item covers the proper runner. Version SSOT currently: pyproject `0.1.0rc1` = `__init__` `0.1.0rc1`; profile toml says `version = "0.1.0"` (the profile's own schema version, not the package pin) — flagged for the SSOT gate check.

## Verdict / next
**PKG-2's build is landed and smoke-verified through the installed package: siona is a real plugin-based package (un-mirror confirmed; infer + boards + bridge; README/CHANGELOG/publish-gate in place), and everything blocking publish is now an explicit checklist, not implicit state.** Building/hardening continues against `PUBLISH_GATE.md`; the rc1 tag fires only when the user calls the gate. **Next hardening order (suggested):** (i) bag-regression fixtures + the board-swap test (cheap, close the audit loop); (ii) failed-run recovery + within-family re-rank (the two known drive-loop gaps); (iii) the UDHR/Bislama + egyptian_tla non-English validations; (iv) structured operands. #230 stays in_progress until the gate clears; #234's grounding hardening is now tracked in the gate checklist (marked completed as a capability).
