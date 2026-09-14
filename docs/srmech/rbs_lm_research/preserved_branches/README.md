# Preserved branches — archive of commits that lived on no remote

Written 2026-09-14 when `research/rbs-lm-rolling-2` (PR #687) became the consolidation home for research findings, so that local and remote branch clean-up cannot delete work that still matters.

Each folder is one source, named after its branch with `/` written as `__`. It holds:

- `0001-…patch`, `0002-…patch`, … — `git format-patch <branch> --not --remotes`: every commit of that branch that was on no remote on 2026-09-14, oldest first, byte-exact (message, author, date, diff, binary files).
- `TIP.txt` — the branch name, the tip SHA, the commit list (SHA, author date, subject, whether it was also cherry-picked), the re-apply base, and the status of every touched path against `research/rbs-lm-rolling-2` at `4db51be25` (**absent** = clean add, **identical**, or **DIFFERS**, with one sentence on what differs).

The archive is complete by itself: every source is here, whether or not its commits were also cherry-picked. Commits whose paths were all absent on this branch were additionally cherry-picked with `-x`, so their files also sit at their original paths with history. The finding for each source (F1355–F1367) says what the commits found and whether the branch is safe to delete.

`.gitattributes` in this folder marks `*.patch` as `-text`, so no line-ending conversion touches the patches on checkout or check-in.

Re-apply a folder with `git am --keep-cr 0*.patch` on the base commit named in its `TIP.txt`.

| folder | finding |
|---|---|
| `rbs-lm-rolling-2` (the 308ddf701 F718 commit) | F1355 |
| `research__spike-28-asymptotic-vs-infinity-history` | F1356 |
| `research__spike-180-cmb-hidden-fiber-confirmatory-independent-data` | F1357 |
| `research-rc426-notation-torsor` | F1358 |
| `research__sm-inverse-decimation-spike` | F1359 |
| `research__killing-yano-literature-review` | F1360 |
| `research__spike-52-evolution-uncoupled-from-time` | F1361 |
| `research__spike-140-silicon-net-substrate-coupling-bridge` | F1362 |
| `research__spike-141-purple-team-falsification-spike-140-stances` | F1363 |
| `research-pal-cleanup` | F1364 |
| `research__v0.20.x-per-body-spectral-catalog-scoping` | F1365 |
| `task931-rbs-klein4-reconcile` | F1366 |
| `fix__rbs-lm-bigram-resonator-s57` | F1367 |

`srmech-rc427-research` also had commits on no remote, but all 23 paths they touch are identical on `main`, so it is recorded in the PR #687 body only and has no folder here.
