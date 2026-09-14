# Addendum to the erratum — 2026-09-14

An independent read-only verification of the erratum commits (`2658bee5b..a18dad372`) found two more false sentences: one in `ERRATUM_2026-09-14.md` and one in F1372. It also found three smaller problems. This file corrects all five.

Under the additive-only rule, `ERRATUM_2026-09-14.md` and F1372 stay exactly as pushed. Read them together with this file; where they disagree, this file is the latest measured record. No archived content is affected.

## 1. The erratum's "corrected README sentence" was itself wrong

`ERRATUM_2026-09-14.md` §1 (lines 68–70) says the 12 cherry-picked commits are *"those that add no `import numpy`"*. Three of the cherry-picked rc426 commits do add `import numpy`, but only inside a `try` / `except ImportError` probe that checks numpy is ABSENT.

Measured:

```
git show --format= <commit> | grep -cE '^\+.*\bimport numpy|^\+.*\bfrom numpy'
```

| cherry-pick on this branch | original | added `import numpy` lines |
|---|---|---|
| `c9d5c6514` | `1d06ab4a8` | 1 |
| `febd5bcb9` | `e48d699ef` | 1 |
| `c95c99f05` | `992548b7e` | 5 |
| the other nine cherry-picks | | 0 |

Every one of those seven lines has this form:

```
+    try:
+        import numpy  # noqa: F401
+        print("!! numpy PRESENT — environment wrong")
+    except ImportError:
```

The seven archive-only commits are different. Each adds `import numpy as np` at module top level, so their scripts need numpy to run: `df7fb90a8`, `7993124a2`, `9eabb62c8`, `f25908163`, `1742bdea2`, `f7f3d5e30` and `ee39d6432`.

The README sentence should read:

> Of the commits whose paths were all absent on this branch, those whose scripts do not depend on numpy were additionally cherry-picked with `-x`, so their files also sit at their original paths with history. An `import numpy` used only to check that numpy is absent (inside `try` / `except ImportError`, in three rc426 commits) was not counted as a dependency. That is 12 commits: `6bb07db03`, the five rc426 commits, the three Killing–Yano commits, the two PAL commits and the task931 census `51907645e`. Seven all-absent commits were **not** cherry-picked, because their scripts import numpy at module top level: `research/sm-inverse-decimation-spike` commits 1–5, `research/spike-140-silicon-net-substrate-coupling-bridge` and `research/spike-141-purple-team-falsification-spike-140-stances`. They are in this archive only.

The per-commit table in `ERRATUM_2026-09-14.md` §1 is correct; the verifier's own comparison differed from it in 0 of 31 rows.

## 2. F1372's phrase count

F1372 (line 21) says that in `main`'s files *"only two of those phrases (plus a rc426 verdict row) appear"*. It names `six-to-eight op arithmetic rc` and `REVERSAL IS NOT REWIND, CONDITIONALLY`.

Measured with `git grep -l -F '<phrase>' b398b8c46`, for the five phrases F1372 lists on line 20:

| phrase | files on `main` (`b398b8c46`) |
|---|---|
| `SHIPPED-OP DEFECT: oct_torsor_act is an ANTI-action` | none |
| `FV1 REFUTED` | none |
| `the forcing law forced nothing` | none |
| `six-to-eight op arithmetic rc` | `docs/srmech/notes/rc427_research_round_synthesis.md` |
| `THE rc424 MUSIC REJECTION STANDS` | none |

So **one** of the five phrases appears on `main`, not two. `REVERSAL IS NOT REWIND, CONDITIONALLY` is not one of the five. It is a separate rc426 verdict phrase, and it appears in `docs/srmech/notes/reversal_is_not_rewind_rc426.py` and `reversal_is_not_rewind_rc426.ndjson`.

F1372's conclusion is unchanged: the other four verdict phrases exist only in the archived commit messages.

**A count that has since moved.** F1372 also says the five phrases occur *"0 times in the remote commit messages"*. That was true when measured. F1372's own commit, `a18dad372`, quotes `six-to-eight op arithmetic rc`. Measured now with `git log --remotes -F --grep='<phrase>'`: that phrase returns `a18dad372`, and the other four return nothing.

## 3. The `git am` commands need the patches extracted first

`ERRATUM_2026-09-14.md` §2 (line 126) and F1372 (line 88) run `git am` on patch paths under `docs/srmech/rbs_lm_research/preserved_branches/`. Those paths exist on this branch, not in a checkout of the re-apply base. So the command as written exits 128 (*"could not open"*). The verifier measured this.

Extract the patches from this branch first. The following was run on 2026-09-14 and proven for both folders:

```
B=origin/research/rbs-lm-rolling-2
D=<an empty directory>
for f in $(git ls-tree --name-only $B docs/srmech/rbs_lm_research/preserved_branches/<folder>/ | grep '\.patch$'); do
  git show "$B:$f" > "$D/$(basename $f)"
done
git worktree add --detach <scratch-worktree> <base>
git -C <scratch-worktree> am --keep-cr "$D"/0*.patch
git -C <scratch-worktree> rev-parse HEAD^{tree}
```

| folder | base | patches | tree after `git am` | tip tree |
|---|---|---|---|---|
| `task931-rbs-klein4-reconcile` | `458437918` (reachable through tag `archive/task931-rbs-klein4-reconcile`) | 5 | `beba45f1846818c5d4d4ee62c9151b6026e990e4` | `dff66d754^{tree}` = `beba45f1846818c5d4d4ee62c9151b6026e990e4` |
| `srmech-rc427-research` | `a532b2fa9` | 13 | `42edd00b8a3d4e61aa14f42317cc984af231d775` | `7018ec8cc^{tree}` = `42edd00b8a3d4e61aa14f42317cc984af231d775` |

## 4. Which `CHANGELOG.md`

`ERRATUM_2026-09-14.md` §3 (lines 170 and 176) cites *"`CHANGELOG.md` line 3926"*. The quoted text is at **`docs/srmech/python/CHANGELOG.md:3926`** on `main` (`b398b8c46`). The repository-root `CHANGELOG.md` has 2237 lines.
