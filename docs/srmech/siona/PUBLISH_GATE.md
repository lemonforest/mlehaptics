# siona 0.1.0rc1 — PUBLISH GATE (do these AT ready-to-publish, not before)

Recorded 2026-07-02 per user direction, so building/hardening continues unblocked. **None of these
executes until the rc1 cut is declared ready** ("almost there or all the way there").

## Repo / publisher moves (at publish time)
1. **PyPI trusted-publisher target → its own `lemonforest/siona` repo** (both indices,
   project=`siona`): move `siona-publish.yml` there; re-register the trusted publisher on
   TestPyPI + PyPI to point at `lemonforest/siona`; the package source tree moves with it.
2. **Update `[project.urls]`** (Homepage/Repository/Issues) from mlehaptics paths to
   `lemonforest/siona` in `pyproject.toml`.
3. **The siona RESEARCH NOTEBOOK stays in `lemonforest/mlehaptics`** — RTD is already set up there
   and serves the research-notebook family; only the *package* moves. The package README links back
   to the notebook on RTD.
4. **Release cut = its OWN PR** (never PR #687), then manual tag `siona-v0.1.0rc1` → TestPyPI
   (per `project_siona_package_takeover_unmirror` + `feedback_always_rc_first`). Clean
   `siona-v0.1.0` → PyPI is the human gate.
5. **Clean-venv verification OUTSIDE the source tree** — RUN (2026-07-03): wheel builds clean (all modules/descriptors/LICENSE/entry-points); imports from `/`; `Session()` constructs AND drives on production srmech 0.8.2 (gcd turn verified); byteglyph features FEATURE-DETECT and degrade gracefully on pre-0.9.0rc floors (cross-language recall test skips with reason). Re-run against the graduated srmech before the tag.

## SEQUENCING DECISION (user, 2026-07-03) — rc1 WAITS for the srmech rcN run to conclude
**siona does NOT base off TestPyPI srmech.** The byteglyph word encoder (and the exact-rational
transcendental returns) live in the srmech 0.9.0rc series, not production 0.8.2. Per user direction:
rc1 ships only after the srmech rcN run concludes and graduates to production PyPI; at the cut, bump
`dependencies`/`srmech_requires` from `>=0.8.1` to the graduated version, re-run the clean-venv verify
against it (expect full 17/17, no skips), then the release mechanics. The feature-detection stays
(graceful floors are correct regardless).

## Hardening backlog (before declaring ready)
- [x] paraphrase intent-frames — DONE (F1022: politeness prefixes = declared operators consumed before routing)
- [x] name ALIAS/morphology — DONE by pre-measurement (F1017): PREFIX-COVER chosen (Gram unchanged 0.271, eval kept, alias 3/5); byteglyph vecs REJECTED read-independently (+0.130 cross-talk AND worse alias)
- [x] code-switching (user question, F1017): merged bilingual board routes mixed input 5/5; the attested 'save' homograph drops to grounding (operators declared; colliding declarations -> operands decide); notes store UNDOCTORED (the len-1 tokenizer filter was an English-privilege artifact dropping Bislama 'i' — fixed)
- [x] rung-SUPERPOSED homographs — DONE (F1020: merge_boards keeps senses; language-vote dispatch over parent operator vocabs; the elliptic-ladder HDC store remains the N-language scale path, probe-proven 12/12)
- [x] operator ACCRETION with guards — DONE (F1020: k=3 unanimous, session-local learned_verbs, unlearn(); persistence-to-genome = PKG-3 scope)
- [x] byteglyph NOTE-encoding — DONE by pre-measurement (F1021: HYBRID adopted, Gram +0.029 within budget, cross-language 2/2 — 'water' finds 'wota'; pure glyph failed the rule; grounding stays token-exact)
- [x] conflict-fallback policy — DONE (F1020: margin<1 -> ASK listing the senses; never guess)
- [x] magnetic role-probe first tier — RUN (F1022: degree-diff null-by-construction reported; neighbor-overlap conj>det suggestive both languages, thin; full magnetic-mode analysis = research follow-on, NOT an rc1 blocker)
- [x] ASL-LEX sense-splits ATTESTED (F1022: data fetched, OSF zpha4, CC-BY-NC 4.0; save->2 signs, remember->2, right->3, run->4; EntryIDs = ready rung labels; wiring = follow-on, not a blocker)
- [x] structured operands — DONE as scoped (F1015 floats+kwargs; F1022 graph edge-pairs + n derivation; Mat/Vec/HV CONSTRUCTION documented out-of-scope for utterances — carriers arrive via tool returns)
- [x] failed-run recovery — DONE (F1015: fit-positive candidates in order, attempts recorded)
- [ ] kernel generality hand-off (multi-step / non-linear → srmech `dispatch.infer` axis)
- [x] within-family re-rank — DONE (F1015: whole-index name-coverage promotion)
- [x] bag-regression tests — DONE (F1015: fixtures pinned, suite green)
- [x] UDHR parallel-invariant run — DONE (F1015: 3–8× chance, zero dictionary; IR layer proven load-bearing)
- [x] egyptian_tla board exercised — DONE (F1015: distinct .386 + deterministic)
- [x] operator-board swap test — DONE (F1015 synthetic testlang full session; F1016 REAL Bislama board from UDHR-attested vocab, 2/2 tests)
- [x] test suite green under pytest — DONE (dev rc97: 17/17; clean venv on PRODUCTION srmech 0.8.2: 16 pass + 1 documented skip after byteglyph feature-detection)
- [x] version SSOT — DONE (pyproject = __init__ = profile toml = 0.1.0rc1; the flagged mismatch fixed). README/CHANGELOG final pass at the cut.

## Standing constraints
- TestPyPI-first, always; clean tag = human-only production gate.
- Never squash-merge. The wheel ships mechanism, not knowledge (PKG1_DECISION).
