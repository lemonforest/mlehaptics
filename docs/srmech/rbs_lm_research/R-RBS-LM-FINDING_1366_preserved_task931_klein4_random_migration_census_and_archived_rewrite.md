# F1366 — **preserved: the `#T931` klein4_random reconciliation — a 433-site census by regime (landed here) and a four-commit rewrite (archived) that this branch has since overtaken in most of its files**

Consolidation record (2026-09-14). Source: local branch `task931-rbs-klein4-reconcile`, six commits on no remote (2026-07-20): one merge of `origin/main`, the census, and four rewrite commits.

## What the commits found (their own words and figures)

- **Census** (`51907645e`). *"The research branch forked at srmech rc256 and has never merged the rc290/rc292 regime split (F1259/F1260)."* It records 433 klein4_random call sites across 193 files, one record per site: `klein4_expand` 291 (280 PRESERVED byte-for-byte, 11 CHANGE); `klein4_address` 48 CHANGE; REVIEW 7; UNRESOLVED 87 (70 STATEFUL_STREAM + 17 unclassifiable). *"PRESERVED is not an assumption"*: `klein4_expand(D, seed)` is byte-identical to `random.Random(seed).randrange(4)` over seeds {0,1,42,7919,123456}. The migration tool is committed alongside.
- **1/3** (`2406d2522`): 280 sites, *"numbers UNCHANGED"*, verified over 240 (D, seed) combinations with zero mismatches; all 152 touched files byte-compile. The message says *"274 insertions / 274 deletions"*; the commit's diffstat prints 263 insertions / 263 deletions across 152 files.
- **2/3** (`873f6461d`): 11 sites, *"numbers CHANGE"*. The underlying stream moves from numpy PCG64 to stdlib MT19937, while distinct keys stay distinct.
- **3/3** (`e035d2495`): 48 sites to `klein4_address`, *"numbers CHANGE"*. Its reasons: 21 sites keyed on builtin `hash()` of a str (*"hash("the")%80000+11 returned 51649, 19229, 66627 on three consecutive interpreters"*), and the 80000-wide seed band overlapped the role and rung keys. Its own limit: *"of these 48 files, 47 cannot be executed in any compliant environment here … The 1 that runs, runs clean."*
- **3b/3** (`dff66d754`): the last 7 addressed sites. `seed=sum(t.encode())` is order-insensitive, so *"dog"* and *"god"* got the same vector.

## Where it lives on PR #687

- **Census, cherry-picked with `-x`:** `docs/srmech/notes/task931_klein4_migration_tool.py` and `docs/srmech/notes/task931_klein4_random_migration_census.ndjson`. Both paths were absent here; the tool mentions numpy only in text.
- **Rewrite, archive only:** `preserved_branches/task931-rbs-klein4-reconcile/` holds five patches (the census and the four rewrite commits).
- The merge `458437918` is not a patch. Both of its parents are on remotes (`57a4b44af` on this branch, `ff3ae1dd8` on `main`), and `git show --cc` on it prints no hunks.

## DIFFERS (112 of the 171 touched paths; one sentence per path in the archive's `TIP.txt`)

Measured 2026-09-14 against this branch at `4db51be25`:

| class | paths |
|---|---|
| identical — this branch already has the exact post-rewrite blob | 57 |
| DIFFERS — this branch edited the file after the rewrite's merge base, so the two edits diverge | 106 |
| DIFFERS — this branch's file is unchanged since the merge base and differs only by the rewrite | 6 |
| absent — clean add (the census pair) | 2 |

klein4_random occurrences across the 112 DIFFERS paths: in neither version 85, in both 17, in the branch tip only 8, in this branch only 2. The rewrite therefore does not re-apply cleanly here; the archive keeps it exact for reading, and for re-application on its own base.

Branch safe to delete once this commit is on origin: yes
