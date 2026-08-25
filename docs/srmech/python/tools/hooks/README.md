# srmech enforcement hooks — written, **not activated** (rc452, `#T1166`)

Seven Claude Code hooks, each written against a failure this repo actually
suffered. **None of them is live.**

> ⚠️ This line read "each watched doing both things it must do". That was
> false for two of the seven, and the correction is the most useful thing in
> this file. `generated_file_edit_blocker` was watched blocking `_tool_docs.py`
> and allowing `rational.py` — both true — while one of its two predicates was
> dead and a real `regen_all` output went unprotected; and
> `stale_native_tripwire` was watched blocking and allowing *fixtures*, while
> on the real tree it blocked unconditionally at 43 s a call. **Watching a hook
> block and allow is necessary and not sufficient**: it proves the verdict
> logic, not that each predicate is live, and not that the thing is affordable.
> See "The two hooks that could not do their job" below.
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

**Every figure below is a wall-clock measurement of the whole invocation** —
`subprocess` launch to exit — taken three times on this WSL2 / 9p mount at
rc452, reported best–worst. The previous table was wrong on **five of seven
rows**, because most of its numbers timed the predicate rather than the call.

**There is a floor, and it dominates most rows.** `git_add_all_blocker.py`
does nothing but split a string, and it costs **332–359 ms**. That is CPython
startup plus `_hooklib` import on this mount, and no hook can be cheaper. So
"~0" and "~1 ms" were not merely imprecise, they were unreachable. The
*marginal* column is the interesting one: cost above that floor.

| Hook | Event | Blocks | Cost per invocation | Marginal |
|---|---|---|---|---|
| **`ratchet_recount.py`** | Stop, SubagentStop | Declaring done while `tests/test_status_conflation_ratchet_rc404.py` is red — a `return SRMECH_ERR_OVERFLOW` count above its down-only ceiling that has not been root-fixed or explicitly adjudicated. | **18.0–20.0 s** (was stated ~11 s) | ~17.7 s — it runs the gate |
| **`stale_native_tripwire.py`** | PreToolUse (Bash), Stop | Running pytest/parity/`ripple_check` when the `libsrmech` that command would **load** is older than `c/src`; `ctest` is checked against `build/` instead. Rebuild commands are exempt. At Stop it fires only if `git status -- docs/srmech/c` is dirty. | **0.69–0.89 s** (was stated <0.5 s; **shipped at 43 s** before the rewrite) | ~0.36 s — 8 stats + one `scandir` of 139 files |
| **`git_add_all_blocker.py`** | PreToolUse (Bash) | `git add -A`, `git add --all`, `git add .`, `git commit -a`/`-am`. Not `git add -u` (tracked-only, cannot sweep). Not a mention inside `echo`. | **0.33–0.36 s** (was stated ~0) | ~0 — this row **is** the floor |
| **`generated_file_edit_blocker.py`** | PreToolUse (Edit/Write/NotebookEdit) | Hand-edits to any `regen_all.py` output (6, from `codegen_manifest.GENERATORS`) or any file whose first five lines carry a generated-file banner — *"generated"* **and** *"do not edit"*, case-insensitively. Regeneration is never blocked: `regen_all.py` writes via Bash, not the Edit tool. | **0.59–0.71 s** (was stated ~1 ms — **the largest error in the old table, ~590×**) | ~0.26 s — it execs `codegen_manifest.py` |
| **`ssot_agreement.py`** | Stop, SubagentStop, PreToolUse (`git commit`) | A disagreement among the **five** version SSoT files (ADR-0007 §2.1) or among the **seven** ABI surfaces — the `srmech.h` macro, `EXPECTED_ABI_VERSION`, and **five** prose/generated statements (`docs/srmech/CLAUDE.md`, `c/README.md`, `python/README.md`, the notebook stamp, and the generated `_c_claims.py`). **Twelve surfaces, not nine.** | **0.50–0.53 s** (stated <0.5 s — the only row that was nearly right) | ~0.17 s — 12 regex reads |
| **`derived_ledger_freshness.py`** | Stop, SubagentStop | Stopping while `tests/worked_examples_result.ndjson` records results for ops whose defining module changed after the ledger's own commit. | **4.5–5.7 s** (was stated ~0.3 s, **~15–19×**) | ~4.2 s — the git calls cost 2.4–8.1 s on this mount |
| **`ripple_stamp_before_push.py`** | PreToolUse (`git push`) | Pushing an op-touching branch with no green `tools/hooks/ripple_stamp.py` record at the current HEAD. Escape token: `[ripple-pending]` in the HEAD commit message. | **1.42–1.49 s** (was stated <1 s) | ~1.1 s — diff against upstream |

Two rows deserve their own note rather than a cell. `ratchet_recount` at ~18 s
and `derived_ledger_freshness` at ~5 s are **Stop-only**, so they are paid once
per turn, not per tool call — that is why they are tolerable at a cost that
would be disqualifying on a `PreToolUse(Bash)` matcher. The two hooks that DO
fire on every Bash call are the floor row and the 0.69–0.89 s stale-native
check.

`ssot_agreement`'s row previously said "five ABI surfaces … and three prose
statements". The code carries **seven** ABI surfaces and has since surfaces 11
and 12 were added — the hook's own docstring heading also still said "THE NINE
SURFACES" over a list of twelve. Both are corrected; `_ABI_SURFACES` in the
source is the SSoT.

## Evaluation

```
python3 tools/hooks/check_hooks.py          # 59 cases: 58 passed, 0 failed, 1 skipped
python3 tools/hooks/check_hooks.py ratchet  # substring-filtered

python3 tools/hooks/generated_file_edit_blocker.py --selftest   # predicate POPULATIONS
python3 tools/hooks/stale_native_tripwire.py     --selftest     # artifact set + timings
```

The case count is tree-dependent by design, and watching it move is the point:
it read **43 passed / 0 failed of 43** while the shipped ABI lag described
below was still present, then **43 passed / 1 skipped of 44** once the lag was
repaired (the two real-tree `ssot_agreement` cases collapsing into one
self-announcing SKIP, plus two ceiling-adjudication cases), and **58 passed /
0 failed / 1 skipped of 59** now that the two broken hooks are repaired —
`stale-native` 5 → 14 cases and `generated-edit` 4 → 11. A harness whose count
never moved would not be observing the tree.

**Both new instrument kinds were red-planted, because neither reports through
an exit status.** Deleting the one-line `sys.modules[spec.name] = mod` fix
returns `generated_file_edit_blocker` to its shipped state: the vacuity case
goes **1 failed of 11**, and every invocation now prints `manifest predicate
UNAVAILABLE (AttributeError: 'NoneType' object …)` to stderr instead of
silently swallowing it. Note what *doesn't* move — `_c_claims.py` still blocks,
via the banner conjunction, which is the two predicates being genuinely
independent and is precisely why only a population check can see one of them
die. Dropping the wall-clock ceiling from 5 s to 50 ms gives `1 failed of 14`
at `701 ms against a 50 ms ceiling`.

Every hook has at least one planted violation it must catch (exit 2) **and** at
least one legitimate case it must let through (exit 0); the loop guards are
exercised too. Where a real fixture existed it was preferred over a contrived
one:

- `ratchet_recount` **passes** against this rc's genuine adjudicated state
  (`CEIL_CONFLATING_RETURN_LINES = 745`, measured 745) and **blocks** against a
  real planted `return SRMECH_ERR_OVERFLOW;` in a temporary `c/src` file,
  removed in a `finally`. The distinction the hook exists to draw is then shown
  end to end on that same planted line: **blocked** while unaccounted for,
  **allowed** once the ceiling is adjudicated up to meet the measured count,
  and **blocked again** if the ceiling overshoots it — because the gate asserts
  equality in both directions, "just add slack" is not an exit, and the marker
  cannot be gamed. The ratchet file is restored from bytes captured before the
  run.
- `ssot_agreement` **blocks the tree exactly as it stands** — see below.

The harness was itself red-planted: inverting five expectations produced
`5 passed, 5 failed` and a non-zero exit, so it can report failure.

`check_hooks.py` is deliberately not named `test_*` — a `test_` file under
`tools/` would be swept into the suite by a bare `pytest` run and perturb pinned
collection counts in a slice whose mandate is not to change the suite. Move it
into `tests/` when the hooks are switched on.

## What the hooks found on their first outing

Written to catch future mistakes, they were run against the present tree and
the class they target was already there. `ssot_agreement` blocked on a live
shipped falsehood; chasing it, and then chasing the full sweep properly,
closed every red on the branch:

| | before | after |
|---|---|---|
| `tools/ripple_check.py` (WSL2, native loading) | 12 failed | **0 failed — 2081 passed, 1 skipped, 1 xfailed** |

Four surfaces still said **ABI 21** after the 21→22 bump (`python/README.md`,
the generated `_c_claims.py`, the notebook's live stamp, and `CLAUDE.md` which
Phase 2 had already fixed), and `_chain_c_eligible` refused five ops the C
runner actually runs — making shipped C work unreachable from the package, the
rc447 defect in miniature. **The first version of `ssot_agreement` caught one
of the four and reported the tree clean**, which is the same error it exists to
prevent; it now censuses the class across twelve surfaces rather than the one
instance.

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

## The two hooks that could not do their job

Written to catch defects, two of them shipped carrying the defect class they
target. Neither was visible from an exit status, which is the whole lesson.

**`generated_file_edit_blocker` ran on one predicate, not two.** Its manifest
predicate returned `[]` on *every* invocation. `codegen_manifest.py` opens with
`from __future__ import annotations`, so every field annotation on its
`@dataclass(frozen=True) class Generator` is a string; `dataclasses` resolves
those textually via `sys.modules[cls.__module__]`; and loading through
`spec_from_file_location` + `exec_module` never puts the module there, so the
class body raised `AttributeError: 'NoneType' object has no attribute
'__dict__'` before `GENERATORS` was bound. A bare `except Exception: return []`
swallowed it. The fix is `sys.modules[spec.name] = mod` before `exec_module`.

Measured against the HEAD hook: **`_c_claims.py` exited 0** — a real
`regen_all` output that ships in the wheel and reaches users through
`describe()`, the MCP tool list and the compiled-in C registry. So did
`_unicode_fold_tables.py`. Only `_tool_docs.py` blocked, and only because it
spells its banner in capitals: the banner match was case-*sensitive*.

The banner predicate is therefore re-derived as a **conjunction** — a
do-not-edit phrase **and** "generated", case-insensitively, in the first five
lines. Measured over 3331 tracked files:

| predicate | hits | generated | false positives | missed |
|---|---|---|---|---|
| shipped: case-sensitive `DO NOT EDIT`, 3 lines | 6 | 6 | 0 | **7** |
| case-insensitive alone, 3 lines | 11 | 10 | **1** | 3 |
| **conjunction, 5 lines** | **13** | **13** | **0** | **0** |

The single false positive is `rbs_nn_research/UPSTREAM_NOTES.md`, whose third
line is the prose "Do not edit srmech package files in this session." — a
sentence about *other* files. Requiring "generated" as well removes exactly it.
`_carrier_examples.py` is exempted with a warning: its own banner says
hand-curated rows "may be added here and are preserved", so blocking it
outright was a false block.

**`stale_native_tripwire` was unsatisfiable and expensive**, and either half
alone gets a hook switched off. It cost **43 s per Bash call** — `glob("build*")`
plus `rglob` for four library names across **16 build directories, ~4800
files**. And it blocked permanently while the library Python actually *loads*
was fresh:

```
python/srmech/_native/libsrmech.so   2026-08-24 23:55:31   <- loaded, HAS_NATIVE=True, ABI 22 == 22
c/src/srmech_compose_run.c           2026-08-24 16:02:43   <- newest source
```

The block came entirely from **14 abandoned rc-numbered snapshots**
(`build_rc41`…`build_rc46` from 2026-06-05, `build_rc342*`/`349`/`355`/`359`/
`363` from July) plus two alternate-config trees. No rebuild refreshes any of
them, so the block could never be cleared. It also listed `cmake --build` as a
command that *trusts* the native path, so it refused the rebuild printed in its
own block message — a category error: a rebuild **produces** a library.

The repair is to ask the question the **loader** asks. `_find_library` resolves
`srmech.__path__` to one directory, `srmech/_native/`, and never consults a
build tree; `ctest` adds the canonical `build/`. The artifact set is now chosen
**by the command**, named explicitly, never globbed — `43 s → 0.69–0.89 s,
~93×`.

Both hooks now carry `--selftest`, which prints each predicate's **population**.
That exists because a dead predicate and a satisfied one are the same shape from
outside — both exit 0 on a hand-written file — and a permanent block looks
exactly like a working block. `check_hooks.py` asserts the manifest population
is 6 and asserts a 5 s wall-clock ceiling the shipped 43 s would have failed.

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
