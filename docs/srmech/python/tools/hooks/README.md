# srmech enforcement hooks — written, **not activated** (rc452, `#T1166`)

Seven Claude Code hooks, each written against a failure this repo actually
suffered, each watched doing both things it must do. **None of them is live.**
`.claude/settings.json` is untouched — activating hooks mid-session changes the
behaviour of agents still running, which is the user's call and not an agent's.
To enable, merge the block in [`settings.sample.json`](settings.sample.json)
into `.claude/settings.json`; to disable any one of them, delete its entry.
There is no other state: the only file any hook writes is
`.git/srmech_ripple_stamp.json`, which lives inside `.git` and can never be
staged.

Every hook is POSIX-friendly Python 3 standard library — no new packages, no
imports from `srmech` itself. Each reads one JSON object on stdin and answers
with an exit status: `0` allows, `2` blocks and feeds its stderr back to the
model. An internal error (a missing file, a git binary that is not there) exits
`0` with a loud note, because a hook that crashes blocks *everything* and a hook
that blocks legitimate work gets switched off within a day — strictly worse than
no hook. Measurement failures, by contrast, always fail closed.

## What each one blocks, and what it costs

| Hook | Event | Blocks | Cost per invocation |
|---|---|---|---|
| **`ratchet_recount.py`** | Stop, SubagentStop | Declaring done while `tests/test_status_conflation_ratchet_rc404.py` is red — a `return SRMECH_ERR_OVERFLOW` count above its down-only ceiling that has not been root-fixed or explicitly adjudicated. | **~11 s** (measured), only at Stop |
| **`stale_native_tripwire.py`** | PreToolUse (Bash), Stop | Running pytest/ctest/parity/`ripple_check` when a built `libsrmech` is older than `c/src`. At Stop it fires only if `git status -- docs/srmech/c` is dirty, so pure-Python sessions never see it. | **<0.5 s** stat sweep |
| **`git_add_all_blocker.py`** | PreToolUse (Bash) | `git add -A`, `git add --all`, `git add .`, `git commit -a`/`-am`. Not `git add -u` (tracked-only, cannot sweep). Not a mention inside `echo`. | **~0** (string only) |
| **`generated_file_edit_blocker.py`** | PreToolUse (Edit/Write/NotebookEdit) | Hand-edits to any `regen_all.py` output or any file whose first three lines say `DO NOT EDIT`. Regeneration is never blocked — `regen_all.py` writes via Bash, not the Edit tool. | **~1 ms** |
| **`ssot_agreement.py`** | Stop, SubagentStop, PreToolUse (`git commit`) | A disagreement among the five version SSoT files, or among the five ABI surfaces (`srmech.h` macro, `EXPECTED_ABI_VERSION`, and three prose statements). | **<0.5 s** (9 reads) |
| **`derived_ledger_freshness.py`** | Stop, SubagentStop | Stopping while `tests/worked_examples_result.ndjson` records results for ops whose defining module changed after the ledger was written. | **~0.3 s** (2 git calls + one NDJSON parse) |
| **`ripple_stamp_before_push.py`** | PreToolUse (`git push`) | Pushing an op-touching branch with no green `tools/hooks/ripple_stamp.py` record at the current HEAD. Escape token: `[ripple-pending]` in the HEAD commit message. | **<1 s** (the 27-min sweep is the existing discipline, not a new cost) |

## Evaluation

```
python3 tools/hooks/check_hooks.py          # 43 cases: 43 passed, 0 failed
python3 tools/hooks/check_hooks.py ssot     # substring-filtered
```

Every hook has at least one planted violation it must catch (exit 2) **and** at
least one legitimate case it must let through (exit 0); the loop guards are
exercised too. Where a real fixture existed it was preferred over a contrived
one:

- `ratchet_recount` **passes** against this rc's genuine adjudicated state
  (`CEIL_CONFLATING_RETURN_LINES = 745`, measured 745) and **blocks** against a
  real planted `return SRMECH_ERR_OVERFLOW;` in a temporary `c/src` file,
  removed in a `finally`.
- `ssot_agreement` **blocks the tree exactly as it stands** — see below.

The harness was itself red-planted: inverting five expectations produced
`5 passed, 5 failed` and a non-zero exit, so it can report failure.

`check_hooks.py` is deliberately not named `test_*` — a `test_` file under
`tools/` would be swept into the suite by a bare `pytest` run and perturb pinned
collection counts in a slice whose mandate is not to change the suite. Move it
into `tests/` when the hooks are switched on.

## Two things measurement changed

**1. `derived_ledger_freshness` does not use the mechanism it was specified
with, because that mechanism could not work.** The design said to recompute each
row's `src_sha256` as "the recorded op's current source hash". The field exists,
but `tools/run_worked_examples.py` defines it as
`sha256(setup + "\0" + worked)` — the hash of the **snippet text**. This
session's defect was an implementation flip underneath an unchanged snippet
(`rational_mul` began returning `Q`, and `'Q' object is not subscriptable`), so a
snippet-hash comparison could not have caught it. The tree's own
`run_worked_examples.py --only-stale` inherits the same blind spot and would not
have re-run those rows either. The hook therefore asks a different, decidable
question: *has the module that defines this op changed since the ledger's own
commit?* — per-row scoped, so one module's edit never demands the full
581-snippet run. C-source changes are reported as an advisory and do not block;
attributing them to individual rows is not decidable from the ledger, and
blocking would flag all 581 rows on any C edit.

**2. `stale_native_tripwire` uses mtime, and the tree bans mtime.** The ban in
`regen_all.py` is correct for the case it rules on — every file in its argument
is git-tracked, and checkout order scrambles tracked mtimes. The comparison here
has one untracked side: `libsrmech.{so,dll,dylib}` is a build artifact git never
writes, so its mtime comes from the compiler alone. A checkout that scrambles
source mtimes forward can only produce "source newer than lib", which is
resolved by a rebuild that was correct after a branch switch anyway. The same
runner's rule that a library-less checkout must stay green is honored: **no
library found is always ALLOW.**

## One hook to watch

`ripple_stamp_before_push.py` has a genuinely moderate-to-high false-positive
profile and it is the only one that collides with a standing instruction rather
than a convenience: quota discipline says commit and push incrementally, because
a prior 3h34m run died on a weekly limit with everything uncommitted. Forbidding
an incremental push would trade 27 minutes against the risk of losing hours. The
`[ripple-pending]` token resolves this — the push goes through and the hook
echoes the admission into history, so the goal is met: not preventing un-swept
pushes, but preventing un-swept pushes that *present as swept*. It ships
commented out in the sample. If it gets bypassed routinely, the documented
narrowing is to fire only on pushes whose head commit message claims closure
(`_claims_closure` is already in the file, in place and unused, for exactly
that).

## `ssot_agreement` blocked this branch on a real defect, which is now fixed

When it was first run, `ssot_agreement` blocked the tree as it stood — no
fixture involved. `docs/srmech/python/README.md` read **"**ABI 21** at this
release"** while `SRMECH_ABI_VERSION` was **22**: the 21→22 bump had not
carried the prose, and that README is the PyPI long-description, so the false
statement was shipped text. The existing gate
`tests/test_readme_currency_rc419.py` was red on it (3 failed / 2 passed) —
coverage existed, the repair did not. (A first hypothesis that the ABI-prose
gate had a *hole* was falsified by running
`test_abi_prose_currency_rc449.py`, which is green because it covers
`CLAUDE.md` and `c/README.md`, not this sentence.)

The defect is **repaired in the same slice**: the header, the bump-sentence
enumeration and the worked `native_status()` block all now read 22, sourced
from the CHANGELOG's own Phase 2 K1/K3 entries. Both gates are green (8
passed), and `check_hooks.py` — which tests for the lag rather than assuming
it — has flipped that case to a self-announcing SKIP instead of silently
passing, while its two *planted* ABI-lag fixtures still block. That is the
whole loop the hook exists to close: it found a live shipped falsehood, the
falsehood was fixed, and the instrument still demonstrably fires on the same
class.
