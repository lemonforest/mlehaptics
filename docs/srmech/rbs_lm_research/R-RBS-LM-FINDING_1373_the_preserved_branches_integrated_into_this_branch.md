# F1373 — **the preserved branches integrated into this branch.** Every commit the earlier consolidation archived was replayed onto `research/rbs-lm-rolling-2` with `git cherry-pick -x`. 12 source commits now sit here as new commits: 8 picked cleanly and 4 integrated. Three of the four hit textual conflicts; the fourth applied cleanly but contradicted a measured fact. 5 source commits were already here and were skipped, with the commit that carries each recorded. 2 more had landed earlier the same day (`51907645e` by cherry-pick, `308ddf701` as F1355). One merge was not replayed. One exception is recorded: 19 lines of the `#T931` rewrite keep the op this branch chose for them later.

Integration record (2026-09-14). The maintainer's direction: *"I had meant to cherry pick the changes from those other branches and integrate into the PR#687 branch, not tracking more branches."* The consolidation earlier the same day had archived 13 at-risk branches as format-patch folders under `preserved_branches/` and cherry-picked 12 commits (F1355–F1367, F1372). This record replays the rest.

It also corrects a rule the consolidation applied. It refused seven commits because their scripts import numpy. The no-numpy rule governs the srmech package and its tests (`docs/srmech/python/srmech`, `docs/srmech/python/tests`), not research scripts. This branch already carried many numpy-importing research files. Measured at `66a97bab2`, `git grep -l 'import numpy'` finds 290 files under `rbs_lm_research` and 208 under `notes`. Restricted to `*.py` with the import at line start (`^[[:space:]]*(import numpy|from numpy)`), it finds 254 and 207. Those seven commits are now picked. Nothing in this integration touches `docs/srmech/python/tests`. Only the s57 integration touched `docs/srmech/python/srmech`, and it left `rbs_lm/inference.py` unchanged there: after it, `git diff --name-only 66a97bab2 HEAD` lists no path under either directory.

## Method

- **Order and start.** Work started from `66a97bab2`, taking commits oldest first within each source.
- **Clean pick:** kept. Verified with `git patch-id --stable` against the source commit.
- **Empty pick:** the change was already here. Every one of these also conflicted, because the branch's copy had moved on. In each case the conflicted files were resolved to the branch side, `git diff --cached HEAD` was confirmed empty, and the pick was skipped with `git cherry-pick --skip`. The carrying commit is named with its evidence.
- **Conflict:** integrated into the branch's newer text, never overwriting it. A cherry-pick keeps its original message and the `-x` line, and gets a resolution note and the two trailers.
- **Push:** a plain fast-forward after each source.

## Per-commit outcome

| source branch | commit | outcome | evidence |
|---|---|---|---|
| `research/sm-inverse-decimation-spike` | `1742bdea2` | cherry-picked as `2d49ce41e` | same `patch-id` (`e4022370…`) |
| | `f25908163` | cherry-picked as `3511c07c2` | same `patch-id` (`e6036889…`) |
| | `9eabb62c8` | cherry-picked as `e671bd080` | same `patch-id` (`f9d7ce88…`) |
| | `7993124a2` | cherry-picked as `d9d549835` | same `patch-id` (`e7607d20…`) |
| | `df7fb90a8` | cherry-picked as `e74032798` | same `patch-id` (`3cb338ca…`); all 18 `sm-*` / `sm_*` paths equal the branch tip (`git diff --stat` empty) |
| | `256ba6b78` | integrated with conflict resolution as `bd0101a54` (measurement committed first as `527955900`) | See the MFO note below. It applied without a textual conflict, but its §IV.2 hunk would have made §IV.2 disagree with its own born values. The §XIII.1 status update landed verbatim. 23 lines added, 0 deleted. |
| `research/spike-140-silicon-net-substrate-coupling-bridge` | `f7f3d5e30` | cherry-picked as `44157afe6` | same `patch-id` (`8bf8c6f1…`) |
| `research/spike-141-purple-team-falsification-spike-140-stances` | `ee39d6432` | cherry-picked as `2ac992c4c` | same `patch-id` (`fd30ba7e…`) |
| `task931-rbs-klein4-reconcile` | `458437918` (merge) | not replayed | `git show --cc` prints 0 lines. Parents `57a4b44af` (contained in `origin/research/rbs-lm-rolling-2`) and `ff3ae1dd8` (contained in `origin/main`). |
| | `51907645e` | already present at `df8f17c8c` | cherry-picked by the consolidation; its `patch-id` is among the 12 found in `4db51be25..66a97bab2` |
| | `2406d2522` (1/3) | already present at `5f55963cf` (F1285) | The pick conflicted in 43 files. All 207 hunks are already here: 157 verbatim, and 50 AST-equal, differing only in literal spelling (`10_000` vs `10000`, `0x7FFFFFFF` vs `2147483647`, quote style). All 152 files are in `5f55963cf`'s file list. Resolved to the branch with no staged change, then skipped. |
| | `873f6461d` (2/3) | cherry-picked as `75e77df71` | Clean pick, same `patch-id` (`b86c9edb…`), 11/11 lines in 7 files. See the note on F1285's untouched shapes below. |
| | `e035d2495` (3/3) | integrated with conflict resolution as `1d38f2160` | All 48 files conflicted, one site each. 29 sites were integrated and 19 were kept as the branch has them (see below). 29 lines added, 29 deleted. |
| | `dff66d754` (3b/3) | integrated with conflict resolution as `59ccd2405` | 4 files conflicted. All 7 sites were integrated. 7 lines added, 7 deleted. |
| `fix/rbs-lm-bigram-resonator-s57` | `00abf81c3` | integrated with conflict resolution as `f44333db7` | See the s57 note below. 3 lines added and 2 deleted; each staged changed line is a verbatim line of the source commit (4 of 4). |
| `research/spike-28-asymptotic-vs-infinity-history` | `2de949922` | already present at `9acd98467` | Same `patch-id` (`d04137e1…`) and the same blob (`98b11d22`). The pick hit an add/add conflict because the file has since changed by +240/−4 (`836c0b267`, `a9d14c6bc`, `5b3bacad4`). Skipped. |
| `research/spike-52-evolution-uncoupled-from-time` | `b17594fd0` | already present at `c6b34629a` | Same `patch-id` (`10789427…`). Both notebooks conflicted; resolved to the branch with no staged change, then skipped. The two 2026-05-17 cross-reference paragraphs, which come from its parent, are here through `3643822a1`. |
| `research/v0.20.x-per-body-spectral-catalog-scoping` | `3a12b113f` | already present at `9c7558bad` (PR #236) | The combined `patch-id` of `3a12b113f^..9c097aa1b` equals `9c7558bad`'s (`374bc232…`). The notebook blob is `537701d6` in both. One conflict; resolved to the branch with no staged change, then skipped. |
| | `9c097aa1b` | already present at `9c7558bad` | same evidence; one conflict, resolved the same way, skipped |
| `rbs-lm-rolling-2` (local) | `308ddf701` | already present as F1355 (`6c70e8fa1`) | All 27 body lines of the original F718 file are in F1355. Both `STALE_PATHS_QUEUE.md` lines are appended verbatim (with "See F718" renumbered). Both `UPSTREAM_NOTES.md` edits are present (`grep -c -F` = 1 each). |
| `srmech-rc427-research` | 15 commits | nothing to integrate | Of its 23 paths, 0 differ from this branch or from `origin/main`, and all 23 are present. The messages are in its archive folder and F1372. |
| `research/spike-180-…`, `research-rc426-notation-torsor`, `research/killing-yano-literature-review`, `research-pal-cleanup` | `6bb07db03`, `992548b7e`, `e48d699ef`, `1a1dc422c`, `1d06ab4a8`, `854ba4b95`, `4b49b16ec`, `11409fc8b`, `c85259c47`, `f8abb9dd6`, `153b7563f` | already present (cherry-picked by the consolidation) | 12 of 12 source `patch-id`s (these 11 plus `51907645e`) occur in `4db51be25..66a97bab2` |

## Is every change of each branch on `research/rbs-lm-rolling-2`?

- `research/sm-inverse-decimation-spike` — **yes.** The §IV.2 change is here in a different form: the λ(5−4λ) form and its inverse sit beside the kept equations, with the convention each belongs to, instead of replacing them.
- `research/spike-140-silicon-net-substrate-coupling-bridge` — **yes.**
- `research/spike-141-purple-team-falsification-spike-140-stances` — **yes.**
- `task931-rbs-klein4-reconcile` — **no.** 19 of `e035d2495`'s 48 line changes are not here, because this branch's later `145558237` (F1284) changed those same lines to a different op. They remain in the archived patch `preserved_branches/task931-rbs-klein4-reconcile/0004-*.patch`. Every other change of this branch is here.
- `fix/rbs-lm-bigram-resonator-s57` — **yes.**
- `research/spike-28-asymptotic-vs-infinity-history` — **yes.**
- `research/spike-52-evolution-uncoupled-from-time` — **yes.**
- `research/v0.20.x-per-body-spectral-catalog-scoping` — **yes.**
- `rbs-lm-rolling-2` (local `308ddf701`) — **yes** (as F1355).
- `srmech-rc427-research` — **yes.** The files are identical here, and the messages are in the archive and F1372.
- `research/spike-180-cmb-hidden-fiber-confirmatory-independent-data`, `research-rc426-notation-torsor`, `research/killing-yano-literature-review`, `research-pal-cleanup` — **yes.**

## The MFO §IV.2 polynomial (`256ba6b78`)

**The two sides.**

- **The source commit** replaced R(λ) = λ(5 − λ) and R⁻¹(w) = (5 ± √(25 − 4w))/2 with R(λ) = λ(5 − 4λ) and R⁻¹(w) = (5 ± √(25 − 16w))/8, calling the old form a transcription error.
- **`main`'s MFO Part-I notice** had declined that rewrite *"on prose authority"* and named the measurement that would decide it.

**The measurement** (`F1373_sg_decimation_convention.py`, output beside it). Pure Python 3.14.4, numpy absent, srmech `dense_laplacian` + `jacobi_eigvals`. It uses pre-gasket graphs of levels 1 to 4, with the three corners Dirichlet-pinned.

| Laplacian | R(λ) = λ(5 − λ) | R(λ) = λ(5 − 4λ) |
|---|---|---|
| D − A (combinatorial) | maps 6/6, 21/21, 66/66 non-exceptional level-(m+1) eigenvalues onto the level-m spectrum | 0/6, 0/21, 0/66 |
| (D − A)/4 (degree-normalised) | 0/6, 0/21, 0/66 | 6/6, 21/21, 66/66 |
| D − A, corners kept (no boundary condition) | 1/9, 6/26, 31/71 | (degree-normalised: 1/9, 6/26, 31/71) |

**The consequence.** The level-1 Dirichlet spectrum of D − A is {2, 5, 5}. That matches the born values {2, 5} that §IV.2 already names two sentences after the equations. So both forms are correct, each for its own Laplacian, and the replacement would have made §IV.2 disagree with itself.

**What landed.** The branch's equations stay. A paragraph records the second form, its convention (born values {1/2, 5/4}) and the counts above. `main`'s §IV.2 is unchanged by this; its Part-I notice still describes the question as open.

## The `#T931` rewrite

**Per-file outcome** over the 169 script paths the four rewrite commits touch (plus the 2 census paths, `df8f17c8c`; 171 in total):

| outcome | files |
|---|---|
| picked cleanly (2/3) | 7 |
| integrated (at least one site of 3/3 or 3b/3) | 33 |
| already present / kept as the branch has it | 129 |

Mixes: 129 files only already present, 23 integrated plus already present, 10 integrated only, 7 clean only.

**F1285's untouched shapes.** `5f55963cf` (F1285) deliberately left `klein4_random(D, rng)` and `klein4_random(D, rng=…)` alone, because a shared generator gives N distinct vectors and `klein4_expand(D, k)` gives one. The 11 sites of `873f6461d` pass a **fresh** `np.random.default_rng(<key>)` built inline at each call, so no generator is shared, which is what that commit's message argues. On this branch those sites still called `klein4_random`, which srmech removed, so none of them could run. Their numbers change: PCG64 is replaced by MT19937, as the commit says.

**How the 3/3 and 3b/3 sites were integrated.** On this branch every one of these call lines already read `klein4_expand(D, X)`, F1285's number-preserving rename. Each site was found by AST equality between that call and the source's removed `klein4_random(D, seed=X)` after the same rename. Only the call expression was replaced with the source's `klein4_address(...)` text, character for character. Nothing else on any line changed.

**Integrated: 36 sites.**

| group | sites | files |
|---|---|---|
| coordinate-digest sites | 20 | R-RBS-LM-872 to 896, FINDING_898 |
| `ord()`-rolling-hash token sites | 8 | FINDING_1005, 1008 to 1012, 1018, 1021 |
| `_word_seed` site | 1 | `leg_l3_real_grammatical_order.py` |
| 3b/3 sites | 7 | R-RBS-LM-863, 882 ×3, 883 ×2, 889 |

`klein4_address` is two-stage counter-mode SHA-256, so these vectors change. The 3/3 and 3b/3 messages say so.

**Kept as the branch has them: 19 sites.** FINDING_976, 981, 982, 983, 984, 985, 986, 991, 992, 993, 994, 995, 997, 998b, 998c, 998d, 999, 1000 and 1001. These are builtin `hash()` seeds. This is a disagreement between two commits, and the later one is kept:

- **`145558237` (F1284, 2026-07-21)** migrated them as *"representation (klein4_random(D, seed=hash(w))) : 20 -> hdc.klein4_encode_bytes"*.
- **`e035d2495` (2026-07-20, never pushed until now)** reads the same sites as addresses: *"So klein4_address is the faithful op, and klein4_encode_bytes would be WRONG here"*. Its reason: no script in the cluster compares two different tokens' vectors.

The later branch edit stays. Which reading is right is a research question these two commits answer differently. It is left to the maintainer, and the source's version of those 19 lines stays in the archived patch.

**Checks.**

- Range `f44333db7..59ccd2405`: 40 files, 47 lines added and 47 deleted. No path under `src/`, `test/`, `platformio.ini`, `sdkconfig*` or `docs/srmech/python/`.
- 39 of the 40 touched `.py` files compile. The 40th is next.

**Two defects found, not changed by this integration.**

- **`R-RBS-LM-123_religious_text_chirality.py` does not compile** (`from __future__ imports must occur at the beginning of the file`, line 35). It fails the same way at `f44333db7`, before any of this. It was last changed by `979c7d64d`.
- **`mechanism_loop_bind.py` now calls `klein4_expand`** (lines 64, 103, 104), but line 38 still imports only `klein4_random` from `srmech.amsc.hdc`. The source tip `dff66d754` has the same import line. `docs/srmech/python/srmech/amsc/hdc.py` does not exist on this branch (the module is at `srmech/math/hdc.py`), so the file already failed at that import before this integration. Fixing the import would be a new change beyond the source commit, so it is recorded here instead.

## s57 (`00abf81c3`)

- **`srmech/rbs_lm/inference.py`: the branch version is kept.** `c4b7d707a` (srmech 0.8.2rc1) landed the same removal. The branch copy has `candidates = self.vocab`, no `bigram_counts` or `next_after`, and a §56 greedy decode. It probes with `klein4_bind`, and on this branch `klein4_unbind` is defined as a call to `klein4_bind` (`math/hdc.py:1461`).
- **`_rbs_lm_inference.py`: the branch version is kept, with two hunks applied.** On the branch, `52de8979e` (F1287) had deleted the duplicate class and imports it from `srmech.rbs_lm`. The two hunks that were still missing are applied:
  - the Step 2 docstring line;
  - the removal of `from collections import Counter, defaultdict`, which nothing else in the file uses. `git grep` finds that line only, and the file compiles.
- **`UPSTREAM_NOTES.md`: the commit's two-line APPLIED note is inserted verbatim** at the end of §57, after its Compose line and before §58.

## Supporting files

- `F1373_sg_decimation_convention.py` and `.out.txt` — the §IV.2 measurement.
- `F1373_supporting/`:
  - `t931_classify.py` — classifies every hunk as present, applicable or diverged against the branch worktree. Its output is `t931_classify.json`.
  - `t931_ast_check.py` — the AST check of the 50 diverged 1/3 hunks. Its output is `t931_ast_check.txt`, with 50 of 50 AST_PRESENT.
  - `t931_integrate.py` — the site-by-site integration of 3/3 and 3b/3. Its outputs are `t931_integrate_3.json` and `t931_integrate_3b.json`, with before and after text per site.
  - Inputs: the four `-U0` diffs `t931_{1,2,3,3b}.diff`, and `f1284_files.txt` / `f1285_files.txt` (the file lists of `145558237` and `5f55963cf`).

  The scripts make no git calls. They read files beside themselves plus a hard-coded worktree path, `WT`. Point `WT` at a checkout of `f44333db7` to reproduce the classification.

## What was not changed

- The `preserved_branches/` archive, the errata and the three `archive/*` tags are untouched.
- No branch or tag was deleted. Nothing was force-pushed. PR #687 was not merged.

## Maintainer ruling 2026-09-14: the 19 task931 sites use klein4_address

**The ruling.** The section "Kept as the branch has them: 19 sites" above left 19 sites to the maintainer. The maintainer ruled that they use `klein4_address`, as `e035d2495` chose, and not `klein4_encode_bytes`, as `145558237` (F1284) chose. All 19 are now applied. The earlier paragraph and its per-branch answer **no** stay as they were written; this section supersedes both.

**The reasoning accepted.** It is `e035d2495`'s own argument:

- These vectors are **atomic addresses**. Each one is bound into a pair, superposed into a memory, and retrieved by exact-identity argmax.
- Relatedness between tokens enters only through corpus counts and Laplacian edge weights, never through vector geometry.
- `klein4_encode_bytes` builds a vector from position-bound per-byte vectors, so similar spellings get similar vectors. That commit measured cat/cats 0.6597 and cat/dog 0.2517 with it, against 0.2589 and 0.2454 with `klein4_address`. At these sites that similarity would inject morphological confusion the experiments do not want.
- The other 29 sites of `e035d2495` already use `klein4_address` on this branch (`1d38f2160`).

**The commits that disagreed.**

| commit | committed | op on these 19 lines | how it read the sites |
|---|---|---|---|
| `e035d2495` (`#T931` 3/3) | 2026-07-20T23:34:48−05:00 | `hdc.klein4_address(D, w)` | as addresses: *"So klein4_address is the faithful op, and klein4_encode_bytes would be WRONG here"* |
| `145558237` (F1284) | 2026-07-21T18:57:23Z, 14 h 22 m later | `hdc.klein4_encode_bytes(w.encode() if isinstance(w, str) else bytes(w), D)` | as representations: *"representation (klein4_random(D, seed=hash(w))) : 20 -> hdc.klein4_encode_bytes"* |

F1284 did not have the earlier argument to read: `git branch -r --contains e035d2495` prints nothing, on 2026-09-14 as before this integration.

**A third commit bears on these files.** `e791a4f83` (F1260, 2026-07-20T15:35:46Z) left these historical probes unedited on purpose: *"the generating code IS the attestation of a lodged number; editing it would mean the lodged result no longer reproduces"*. Both later commits change those numbers. Two measurements from today:

- The seeds the lodged numbers came from did not reproduce either. `python -c 'print(hash("the")%80000+11, hash("the")%90000+7)'`, run three times in a row on Python 3.14.4, printed `836 832`, `15404 5400` and `26490 46486`. Builtin `hash()` of a str is salted per process.
- None of the 19 scripts was re-run for this record. Each one reads an uncommitted corpus at `/home/skirklan/corpora/wikipedia/simplewiki_fullbody_instrument.ndjson` (19 of 19 files; 0 of them import numpy).

The findings' `.md` files, and the numbers lodged in them, are unchanged.

**The premise check.** Before changing a file, the ruling's premise was checked in it: the vector made at the site is used only as an address, and no code compares two different tokens' vectors. Each file was read, and `F1373_supporting/t931_ruling_premise_scan.py` checks the same thing on the AST (output `t931_ruling_premise_scan.ndjson`). Across the 19 files:

- every use of the site's dict is a lookup (`vec[t]`) or a membership test (`t in vec`), except one line in F981 that never runs (below);
- 0 `klein4_similarity` calls compare two tokens' vectors. In every read at a site vector, one argument is a probe unbound from the memory `M`, and the other is a candidate's vector;
- 0 comparisons (`==`, `<`, …) have a use of the dict on either side. The `==` tests compare the token a read returns with the target token.

| file | site line | how the vector is used (lines) | where the result is decided (lines) | compares two tokens' vectors | premise |
|---|---|---|---|---|---|
| FINDING_976 | 23 | bound 37–38, bundled 39, probes 40–41, read 27 | `s[0][1]==X` 28 | no | holds |
| FINDING_981 | 19 | bundled 33, probe 28, read 29 | `t1==T` 37, `tk==T` 41 | no. Line 28's `bind(bind(vec[c],ROLE),vec)` is in an `if False` branch and never runs | holds |
| FINDING_982 | 20 | bundled 22, probe 24, reads 26, 28, 35 | the top-4 tokens of each read are printed, 31–32; `fw in vec` 36 | no | holds |
| FINDING_983 | 20 | bundled 26, read 28–31 | `t==T` 34, 37; `w in vec` 38 | no | holds |
| FINDING_984 | 23 | bundled 24, read 26–29 | the top-3 tokens are printed, 31, 35–37; `docf.get(raw[0])` 36 is a corpus count | no | holds |
| FINDING_985 | 24 | bound and bundled 44, read 52–55 | `rd()==target` 56 | no | holds |
| FINDING_986 | 22 | bundled 38, read 41–42 | `==T` 47–48 | no | holds |
| FINDING_991 | 19 | bundled 31, read 33 | `!=seq[i]` 37, `p==seq[i]` 58 | no | holds |
| FINDING_992 | 48 | bundled 63, reads 65, 67–68, votes counted by token 72 | `==T` 78–80 | no. The similarity at 23 is Part A's `klein4_expand` vectors, not this dict | holds |
| FINDING_993 | 46 | bundled 61, reads 64, 66–68 (Klein-4 flips of the probe) | `==T` 74–76 | no | holds |
| FINDING_994 | 35 | bundled 51, and with each pair's three chiral images 57; read 59 | `==T` 64–65 | no. The similarity at 17 compares `klein4_expand(D, 1)` with `klein4_expand(D, 2)` for the isometry check, not this dict | holds |
| FINDING_995 | 26 | bundled 49, bound with rung keys and bundled 51, reads 53, 56, 59 | `==T` 65–67 | no | holds |
| FINDING_997 | 23 | bundled 47, read 49 | `read_M(a)==b` 50 | no | holds |
| FINDING_998b | 24 | bundled 45, read 47 | `==b` 48 | no | holds |
| FINDING_998c | 23 | bundled 42, read 47–48 | `b in rankfn(a)[:K]` 56 | no | holds |
| FINDING_998d | 23 | bundled 42, read 46–47 | `==b` 58–61 | no | holds |
| FINDING_999 | 28 | bound with rung keys and bundled 49, read 51 | `rk[0]==T`, `T in rk[:3]` 57 | no | holds |
| FINDING_1000 | 29 | bound with rung keys and bundled 50, reads 57–60 | `==T` 61 | no | holds |
| FINDING_1001 | 32 | bound with rung keys and bundled 53, reads 60–68 | `==T` 69 | no | holds |

Where relatedness does enter these scripts, it comes from corpus counts (`docf`, `freq`, `nexts`, `rankof`), from the edge weights of `recursive_cut`, and in F997 and F998b–d from `magnetic_laplacian` over directed edge counts. None of those reads a site vector.

**The change.** The premise held in all 19 files, so all 19 were changed.

- In each file, the line F1284 added was found exactly once and replaced with the line `e035d2495` added, character for character. The two commits had removed the same line, and at `4db9932dd` each site line still equalled F1284's added line.
- Nothing else in the files changed. All 19 were edited by later commits elsewhere: they are among the 548 research files that differ between `145558237` and `4db9932dd`. Those edits stay. `git diff --numstat` shows 1 line added and 1 deleted in each of the 19 files.
- Each site's before and after text is in `F1373_supporting/t931_ruling_apply.ndjson`.
- All 19 compile: `python -m py_compile` exits 0 for each (Python 3.14.4, with `PYTHONPYCACHEPREFIX` outside the tree).
- None of the 19 files was touched by the integration range `66a97bab2..4db9932dd`, so they are not among the 40 research scripts counted above.

**Is every change of `task931-rbs-klein4-reconcile` on this branch now?**

- task931-rbs-klein4-reconcile: every change is on this branch: yes. All 48 sites of `e035d2495` are here: 29 in `1d38f2160` and 19 in the commit that adds this section.

**Not done here.** The maintainer also chose to delete the three `archive/*` tags and remove `preserved_branches/` once every change is proven integrated. That cleanup is not part of this commit. The tags and the folder are unchanged.
