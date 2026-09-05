# srmech enforcement hooks — written, **not activated** (rc452 `#T1166`; rc455 `#T1169`)

Ten Claude Code hooks, each written against a failure this repo actually
suffered. **None of them is live.**

> **rc455 added three and repaired two.** New: `jpl_audit_gate` (the
> Power-of-Ten ratchet at the moment of declaring done or committing),
> `prose_currency_gate` (the four shipped-prose gates, armed per surface), and
> `sha256_routing_gate` (no NEW direct `hashlib.sha256(...)` in the package).
> Repaired: `derived_ledger_freshness` and `stale_native_tripwire` both keyed a
> decision on `git status --porcelain`, **which is not a platform-independent
> question on this checkout** — see "The git a hook runs is part of its answer".

> ⚠️ **Then a verification pass found that two of the three new hooks could not
> see their own subject, and that is the second-most useful thing in this file.**
> `prose_currency_gate`'s trigger went silent the moment a prose edit was
> *committed* — blind to the ordinary session shape and to rc452's actual
> defect. `jpl_audit_gate` let `git -C … commit` past a check its own sibling
> caught, blocked on a checkout where pytest *skips*, and degraded silently to
> the very glob its narrowing exists to avoid. Three shipped statements of one
> sha256 census disagreed with each other and with the live `--selftest`. All
> are measured and repaired below; the case count went 110 → 122.

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
| **`jpl_audit_gate.py`** *(rc455)* | Stop, SubagentStop, PreToolUse (`git commit`, **any option form**) | Declaring done or committing while any of `tests/test_jpl_audit.py`'s **13** checks is red — goto, new recursion, malloc, >60-line functions, <2 asserts, multi-line macros, new function-pointer declarators, and the three seed-tightness plus two detector-vacuity checks. Overrides: `SRMECH_ALLOW_JPL_VIOLATION=1`, or `[jpl-pending]` in the commit message. | in scope: **4.1–4.9 s, median 4.3 s** Windows-native / **4.5–9.5 s, median 5.4 s** WSL2-9p, 6 spaced samples each; **0.15 s** on any other Bash command | ~4.1 s — it imports the audit and calls its own functions |
| **`prose_currency_gate.py`** *(rc455)* | Stop, SubagentStop | Stopping while a prose gate armed by *this session's* edits is red — **committed drift as well as working-tree drift**. Four gates, each armed by its own pathspec. A SKIP is reported, never counted as a pass. Override: `SRMECH_ALLOW_PROSE_LAG=1`. | **0.46–0.47 s** Windows-native / 0.30–0.33 s WSL2 when no prose surface moved; **13.8 s** with all four armed | ~13.3 s — it re-enters pytest |
| **`sha256_routing_gate.py`** *(rc455)* | PreToolUse (Edit/Write/MultiEdit) | An edit that ADDS a direct `hashlib.sha256(` call site to a module under `srmech/`, bypassing the native dispatch `sha256_bytes` rides. Scope is applied BEFORE the one allowance. Override: `SRMECH_ALLOW_RAW_HASHLIB=1`. | **0.21–0.22 s** in scope, which IS the floor | ~0 — one file read, two `tokenize` passes |

Two rows deserve their own note rather than a cell. `ratchet_recount` at ~18 s
and `derived_ledger_freshness` at ~5 s are **Stop-only**, so they are paid once
per turn, not per tool call — that is why they are tolerable at a cost that
would be disqualifying on a `PreToolUse(Bash)` matcher. The two hooks that DO
fire on every Bash call are the floor row and the 0.69–0.89 s stale-native
check.

> ⚠️ **`jpl_audit_gate`'s cost is a property of the MOUNT, and writing one range
> hid that.** This note used to give a single figure — "4.5–9.5 s, median 5.4 s"
> — with no environment attached. It does **not** reproduce on a fresh
> Windows-native run. Both measurements, six spaced whole-invocation samples
> each, Stop payload:
>
> | environment | samples (ms) | min / median / max |
> |---|---|---|
> | WSL2 over the 9p mount, cache churned by other work | 5275, 4491, 5056, 5560, **9507**, **8208** | 4.5 / 5.4 / **9.5 s** |
> | Windows-native on `D:`, warm cache | 4285, 4090, 4320, 4883, 4278, 4261 | 4.1 / 4.3 / **4.9 s** |
>
> This is not a retraction of the tail — both rows are real. The predicate
> re-reads 9.4 MB of C on **every** call and there is deliberately **no disk
> cache** (a blob-OID cache buys ~4.5 s at the price of cache-invalidation bugs,
> which for a gate is the worse trade), so a cold or contended page cache is
> exactly what produces the long samples. It is a correction of the claim's
> *scope*. The honest statement: **~4–5 s typically, approaching ~9–10 s when
> the page cache is cold or the mount is slow**, on Stop / SubagentStop /
> `git commit` only, and **0.15 s** on every other Bash call (146/149/149 ms
> Windows-native; 152/214/161 ms WSL2 — the earlier "0.26–0.31 s" reproduced in
> neither). That is still ~6× cheaper than the pytest shell-out it replaces
> (~30 s native, ~53 s WSL) and cheaper than `ratchet_recount`, which is already
> wired at 18–20 s. If the tail gets it switched off, the documented narrowing
> is to drop the Stop arm and keep the `git commit` arm, which is the moment the
> gate actually protects.
>
> **The same caveat binds the whole table above**, which is attributed to "this
> WSL2 / 9p mount". `prose_currency`'s Stop floor is the mirror case: 0.46–0.47 s
> Windows-native (459/469/462 ms), which is what the table said, against
> 0.30–0.33 s (302/329/326 ms) on the WSL2 mount. A cost figure without an
> environment is not a measurement of anything.

`ssot_agreement`'s row previously said "five ABI surfaces … and three prose
statements". The code carries **seven** ABI surfaces and has since surfaces 11
and 12 were added — the hook's own docstring heading also still said "THE NINE
SURFACES" over a list of twelve. Both are corrected; `_ABI_SURFACES` in the
source is the SSoT.

## The git a hook runs is part of its answer (rc455)

Two shipped hooks keyed a decision on `git status --porcelain`. That is **not a
platform-independent question on this checkout**, and the difference is not
small. Measured at rc454 on ONE tree, at ONE commit, with nothing edited:

| query | Windows git 2.53.0 | WSL2 git 2.34.1 |
|---|---|---|
| `status --porcelain -- python/README.md CHANGELOG.md` | **0** | **2** |
| `status --porcelain -- docs/srmech/python/srmech` | **0** | **324** |
| `derived_ledger_freshness.py` exit status | **0** | **2** — 266 modules "changed", all **581** ledger rows declared unverified |

*(That module count read **263** here until the verification pass; measured
**266**. The predicate, so it is re-measurable without WSL: the distinct results
of `_module_of` over the tracked `.py` files under `docs/srmech/python/srmech`,
since WSL git reports every one of them modified. Two routes agree — the hook's
own block message enumerates 8 modules and then says "(+258 more)", and
`git ls-files` gives 266 tracked `.py` mapping to 266 distinct modules.)*

Neither git is misbehaving. The checkout carries `core.autocrlf=true` in the
*Windows user's* global config: index blobs are LF, working files are CRLF
(`git ls-files --eol` says `i/lf  w/crlf` on every one), and the conversion that
reconciles them lives where WSL git cannot read it — a different `HOME`. WSL2 is
the standing build-subagent environment, so under an agent
`derived_ledger_freshness` blocked **every stop, permanently, on a clean tree**:
the same unsatisfiable shape `stale_native_tripwire` shipped with at rc452, from
a different cause.

**Windows git is the authority for this checkout**, and not by preference — the
worktree's own `.git` file holds `gitdir: D:/GitHub/mlehaptics/.git/worktrees/…`,
so WSL git cannot open the worktree at all without `GIT_DIR` overrides. But
pinning a binary would break under a WSL agent, so the repair is at the
**query**. `_hooklib.dirty_paths` asks for a difference in CONTENT —
`git diff HEAD --numstat --ignore-cr-at-eol`, keeping only rows whose
added/deleted counts are not both zero — plus `ls-files --others` for untracked.

| | Windows | WSL2 |
|---|---|---|
| `dirty_paths` over the three pathspecs above | 0 / 0 / **exit 0** | 0 / 0 / **exit 0** |
| the same, with one real 2-line edit planted | `2  0  tools/hooks/README.md` | `2  0  tools/hooks/README.md` |

The second row is the half that matters: an instrument that cannot return
otherwise is not a measurement. `--ignore-cr-at-eol` alone does **not** fix
`--name-only` (measured: still 324 rows); it is the `--numstat` 0/0 filter that
does the work.

`SRMECH_HOOK_GIT=<path>` forces a binary if you ever need one, and every
`--selftest` now prints which git and which interpreter answered.

**And `python3` is not `python` here — the sample no longer says either.**
Measured on this machine:

| launcher | resolves to | version | pytest | numpy |
|---|---|---|---|---|
| `python` | `C:\Python314\python.exe` | 3.14.4 | 9.0.3 | absent |
| `python3` | `…\Local\Python\pythoncore-3.14-64\python.exe` (WindowsApps shim) | 3.14.3 | 9.0.3 | absent |

Two independently-managed installs, resolved by PATH order. **`python` →
`C:\Python314\python.exe` is authoritative for this checkout**: it is a direct
install rather than a Store redirector, and it is the interpreter every
measurement in this file was taken with. They happen to be interchangeable
*today* — same pytest, both numpy-absent, both resolving `srmech` from the
worktree — but nothing keeps them that way, and the failure would be silent.

`settings.sample.json` said `python3` from rc452, which meant a user who merged
it unedited would launch the hooks under the interpreter that was **not** the
one they were tested with. The sample's commands now read
`<REPLACE-WITH-YOUR-PYTHON>`, which is **not a runnable program**: merging it
unedited produces a per-invocation harness warning instead of a working hook on
the wrong interpreter. That is the same trade the file already makes for
`.git/hooks/pre-commit` — a gate that silently does the wrong thing is worse
than one that visibly refuses. Print your own with
`python -c "import sys; print(sys.executable)"`.

The check that catches a wrong pin is `jpl_audit_gate.py --selftest`, which
exits 1 under an interpreter that cannot import the audit (which imports
pytest). Everything a hook re-enters uses `sys.executable`, so pinning the
launcher pins the whole chain.

## Evaluation

Run these with the interpreter you pinned above — on this machine `python`
(`C:\Python314\python.exe` 3.14.4), not `python3`.

```
python tools/hooks/check_hooks.py          # 122 cases: 121 passed, 0 failed, 1 skipped
python tools/hooks/check_hooks.py ratchet  # substring-filtered

python tools/hooks/generated_file_edit_blocker.py --selftest   # predicate POPULATIONS
python tools/hooks/stale_native_tripwire.py     --selftest     # artifact set + timings
python tools/hooks/jpl_audit_gate.py            --selftest     # populations + per-check timings
python tools/hooks/prose_currency_gate.py       --selftest     # base + BOTH trigger halves + pytest COUNTS
python tools/hooks/sha256_routing_gate.py       --selftest     # the census, at BOTH anchors
```

**The one SKIP is self-announcing, and a SKIP is not a PASS.** It is
`ssot-agreement BLOCKS the REAL tree`, which reports *"the ABI prose lag has been
repaired — re-plant a fixture to re-verify"*. That case deliberately runs against
the tree exactly as it stands rather than a fixture, so when the defect it tested
for is fixed it must say so out loud instead of silently passing. Its two
*planted* ABI-lag fixtures still block, so the instrument is still demonstrably
live on that class. Per-section, counted from the run rather than from memory:
ratchet-recount 5, stale-native 14, git-add-all 10, generated-edit 11,
ssot-agreement 6 (5 + the 1 skip), derived-ledger 6, ripple-stamp 7,
**jpl-audit 36**, prose-currency 14, sha256-routing 13 — 122.

### Thirteen plants, one per predicate

The retraction at the top of this file is the design brief for the JPL section
of `check_hooks.py`. `test_jpl_audit.py` carries **13** check functions, and a
single block/allow pair would have said nothing about the other twelve — which
is exactly how `generated_file_edit_blocker` shipped a dead predicate with a
clean bill of health. So each of the thirteen has its own plant, and `case()`
now takes `contains=`, which requires the block message to **name** the check
that fired. A predicate that can never fire cannot satisfy its row.

Plants that could not be made single-predicate are not pretended to be: removing
a recursion cycle also trips the ceiling check. What is asserted is that the
named predicate fired, not that it fired alone.

### The concurrency hazard, tested rather than assumed

`check_hooks.py` writes a Rule-5-violating C file into the **real** `c/src` as a
ratchet fixture. A working-tree scan racing it blocks for a reason nobody can
reproduce afterwards. `jpl_audit_gate` scans the **tracked** file set, so the
untracked fixture is invisible by construction. Measured both ways:

```
check_hooks.py ratchet running; jpl_audit_gate invoked in a loop
  invocations during the overlap              : 5
  invocations that OBSERVED the planted file  : 5
  invocations that BLOCKED                    : 0

counterfactual, same planted file, one call each:
  working-tree glob (naive)  -> 1 red   test_rule_5_minimum_two_asserts_per_function
  TRACKED-ONLY   (shipped)   -> 0 red
```

The narrowing is a scope, not a hole: `check_hooks.py` also `git add`s that same
file and requires the hook to block on it.

The case count is tree-dependent by design, and watching it move is the point:
it read **43 passed / 0 failed of 43** while the shipped ABI lag described
below was still present, then **43 passed / 1 skipped of 44** once the lag was
repaired (the two real-tree `ssot_agreement` cases collapsing into one
self-announcing SKIP, plus two ceiling-adjudication cases), **58 passed /
0 failed / 1 skipped of 59** once the two broken hooks were repaired —
`stale-native` 5 → 14 cases and `generated-edit` 4 → 11 — and **121 passed /
0 failed / 1 skipped of 122** now: the three rc455 hooks took it 59 → **110**,
and the verification pass took it 110 → **122**, twelve cases for defects the
first cut could not see (the committed-prose plant ×5, the option-carrying
`git commit` forms ×4, the two fail-open boundaries ×3). A harness whose count
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
the MCP tool list and the compiled-in C registry. So did
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

## A design that was measured and rejected: `sha256_routing_gate`, first cut

The hook was scoped as "block an edit to any file containing
`hashlib.sha256`, allowances applied before scope".

**The predicate, because a count without one cannot be re-measured:** tracked
`.py` files under `docs/srmech/python` whose text contains the substring
`hashlib.sha256` —

```
git grep -l 'hashlib\.sha256' HEAD -- 'docs/srmech/python/*.py' | wc -l
```

Measured over the **972** tracked `.py` files, **at HEAD `84270a8a2` (rc454),
before this slice's own files**:

| design | blocks | true violations |
|---|---|---|
| as scoped — file CONTAINS the substring | **38** | **0** |
| …of which OUTSIDE the package scope (`tests/`, `tools/`) | 23 | — |
| **redesigned — scope first, literals masked, BEFORE vs AFTER** | **0** | **0** |

Every one of the 38 is a false positive, and the shape of the miss is the
lesson. Inside `srmech/` the substring occurs **7 times in code-shaped text and
0 times as a banned call**: five are documentation *warning the reader off it*
(`_tool_docs.py`: *"WHAT YOU WOULD OTHERWISE WRONGLY HAND-ROLL:
hashlib.sha256(data).hexdigest()"*), and two are the sanctioned fallback in
`srmech/amsc/format.py` — the one place that must call hashlib, because it is
what `sha256_bytes` falls back *to*.

Two changes fix it, and the **ordering** is the load-bearing one. **Scope is
applied before allowances**, so 23 of the 38 stop at the first branch and no
allowance row is ever consulted for them — the difference between an allowance
list that must enumerate every test file that ever hashes something and one with
a single entry. Then the predicate stops asking what a file *contains* and asks
what an edit *adds*: the hook simulates the tool call from
`tool_input.new_string` / `.content` / `.edits`, masks Python string literals and
comments on both sides, and blocks only on an increase. Standing debt is
untouched; a docstring mentioning the call is not a violation, because the mask
removes it.

That the census still reports exactly one real site — `srmech/amsc/format.py`,
the allowance — is asserted by `check_hooks.py` as a vacuity check, because a
masker that ate everything would print 0 and every exit status would still look
right.

### The census is self-referential, and three places printed three numbers

This paragraph used to read *"the same census reads 39/24 rather than 38/23 once
this slice lands"*. **It was wrong, and so were the two shipped docstrings that
stated 38/23 flatly.** Measured on the working tree with this slice applied:

| where | said | live `--selftest` |
|---|---|---|
| `sha256_routing_gate.py` docstring table | 38 / 23 | 40 / 25 |
| `_hooklib.mask_python_literals` docstring | 38 / 23 | 40 / 25 |
| this README | 39 / 24 | 40 / 25 |

Three readings of one census. The cause is not staleness but **self-reference**:
a file that *documents* the rule contains the substring, so it enrols itself in
the population it describes. `comm` names the two additions exactly —
`tools/hooks/_hooklib.py` and `tools/hooks/check_hooks.py`, both written by this
slice. The README's 39/24 counted the first and missed the second (it did not
count `check_hooks.py`'s `_sha_fixture`, whose body embeds
`return hashlib.sha256(d).hexdigest()`). Committing `sha256_routing_gate.py`
itself will move it again.

**The repair is not to pick one of the three.** A self-referential count cannot
be pinned by restating it, so no prose in this tree restates the live number any
more. The first-design figure is quoted **only with its commit** (38/23 at
`84270a8a2`), and `sha256_routing_gate.py --selftest` now prints **both
anchors** with the delta explained:

```
AS SCOPED, at HEAD 84270a8a2          : 38 blocked, 23 of them OUT of scope
AS SCOPED, WORKING TREE               : 40 blocked, 25 of them OUT of scope
   ^ the two anchors differ by +2. This census is SELF-REFERENTIAL: ...
REDESIGNED (scope-first + masked call): 1 file(s) with a real call site
```

The stable figure — the one that is load-bearing, and the one `check_hooks.py`
asserts as a vacuity check — is the redesigned column: exactly **1**.

## A SKIP is not a PASS: `prose_currency_gate`

Measured at rc454 — the same four gates, the same tree, the same commit:

```
Windows :  55 passed, 1 skipped      SKIPPED tests/test_cascade_catalog_prose_currency_rc454.py:472:
                                             compiled srmech library absent
WSL2    :  56 passed, 0 skipped
```

**Both exit 0.** A hook reading the exit status calls the first one green while
one assertion never ran — and it is the arm that needs the native library, i.e.
the one most likely to have moved. So the hook parses the counts: `failed` or
`error` blocks; `passed == 0` with anything skipped blocks (a wholly-skipped run
measured nothing); a timeout is reported as "did not finish", never as a pass;
and any skip at all is printed with its reason, so no turn can end on an
unqualified "prose gates green".

Its trigger was the other half of the WSL-git defect: as designed it was
`git status --porcelain -- README.md CHANGELOG.md`, which under WSL fires
unconditionally, forever. `check_hooks.py` builds a fixture repo with LF blobs
and CRLF working files and asserts both directions — `porcelain=1, content=0`
for an EOL-only difference, and a real dirty path for a real edit.

### …and then it could not see the state it was built for

The repaired trigger asked `_hooklib.dirty_paths` — the **working tree** against
HEAD — and nothing else. So it went silent the moment a prose edit was
**committed**. One file, three states, measured on a purpose-built fixture:

| state | trigger said |
|---|---|
| clean | `[]` |
| README carrying a planted ABI lag, **uncommitted** | `['docs/srmech/python/README.md']` |
| **the same lag, COMMITTED** | **`[]`** — no gate armed, silent allow |

This repo commits per step and never squash-merges, so *edit README, commit,
stop* is the **ordinary** session shape and the hook did nothing in it. And
rc452's actual defect — the shipped "**ABI 21** at this release" against macro
22 — was a *committed* falsehood that had already survived a release, i.e.
precisely the state the trigger was blind to. **A currency gate that only fires
on uncommitted work is blind to exactly the case that ships.**

Nothing could have caught it, because every prose fixture in `check_hooks.py`
plants an **uncommitted** edit: good tests of the wrong verb. Its own peer next
door had it right all along — `derived_ledger_freshness._changed_paths` unions
`git diff --name-only base..HEAD` with the working-tree half.

`prose_currency_gate.changed_prose_paths` now does the same, over a base
resolved in a stated order: `SRMECH_PROSE_BASE` if pinned, else `merge-base HEAD
origin/{main,HEAD,master}`, else the newest reachable `srmech-v*` tag, else
`HEAD~1` as an explicit floor. A base that cannot be resolved **at all** is
echoed to stderr, never swallowed — a trigger that quietly narrows itself is the
defect this section is about. On this worktree `origin/main` resolves and the
merge-base **is** HEAD, so the committed half is empty and nothing false-arms.

Measured after the repair, same fixture, same three states: `[]` / `[README]` /
`[README]`. `check_hooks.py` now carries the committed case end to end — plant,
`git commit`, Stop → **exit 2** — plus the two halves side by side in that same
state (`working-tree half=[] (blind), union=['…/README.md'] via HEAD~1 (floor)`),
and the clean-committed counterpart that must still allow.

## Three ways `jpl_audit_gate` could not see its own subject

**1. The `git commit` arm was narrower than its sibling in the same directory.**
`_commit_segment` required `args[0] == "commit"`. git takes options *before* the
subcommand, and three of them are ordinary here. Measured by calling `_scope`
directly:

| command | first cut | now |
|---|---|---|
| `git commit -m x` | `('committing', …)` | `('committing', …)` |
| `cd d && git commit -m x` | `('committing', …)` | `('committing', …)` |
| `git -C docs/srmech commit -m x` | **`None`** — out of scope | `('committing', …)` |
| `git --no-pager commit -m x` | **`None`** | `('committing', …)` |
| `git -c user.name=z commit -m x` | **`None`** | `('committing', …)` |
| `echo "remember to git commit later"` | `None` | `None` |

`git -C` is the normal invocation for an agent working from another cwd.
`ssot_agreement._is_commit` and `ripple_stamp_before_push` both use `in args`
and never had the hole; matching them is the whole fix. (The line also read
`if args and args and args[0] == "commit"` — the duplicated `args and` is
evidence it was not re-read.) The Stop arm always covered end-of-turn, so this
narrowed the commit-time arm rather than removing the gate. Proven both ways:
a direct 5-in-scope / 4-out census, and three end-to-end block cases under the
goto plant where in-scope → 2 and out-of-scope → 0.

**2. The documented fail-open boundary was not implemented for the case its own
docstring named.** The docstring has said since the first cut that "the C tree
not checked out" exits 0 with a loud note. Measured against a tree holding
`tests/test_jpl_audit.py` with no `docs/srmech/c/` present, it **exited 2**:

```
6 of 13 JPL Power-of-Ten checks are RED
  test_rule_1_recursion_ceiling_is_not_slack     (live population 0 vs ceiling 9)
  test_rule_9_ceiling_is_not_slack               (live population 0 vs ceiling 10)
  test_rule_1_recursion_detector_is_not_vacuous
  test_rule_9_detector_is_not_vacuous
  test_rule_4_seed_is_tight_and_drains
  test_audit_doc_present_and_mentions_all_rules
```

`load_audit` checked only that the audit `.py` existed. The audit itself
declares `pytestmark = pytest.mark.skipif(not _C_SRC_DIR.exists())`, so **pytest
skips this gate in that state** — which makes the claim *"there is exactly one
copy of the rule logic in the tree, so this hook cannot drift from the gate CI
runs"* **false on the skip axis**: pytest's collection semantics are a second
copy of the scoping, and the hook did not honour it. It also inverts this
slice's own *a SKIP is not a PASS* into the strictly worse *a SKIP is a BLOCK*.

Two guards, because the two are different questions. `body` checks the directory
before paying the import; and `audit_skip_reason` **reads the audit's own
`pytestmark`** rather than restating its condition, which restores the
single-copy property on that axis too. Both fail open with "NOT a pass".
`check_hooks.py` gained the case, and the pre-existing *"audit file absent"*
fixture was given a C tree so that it isolates the boundary it names — with both
things missing it could not say which one answered.

**3. The tracked-set narrowing degraded silently to the naive glob.** The first
cut read `if names["src"]:` and simply skipped the narrowing when git returned
nothing — falling back to the **working-tree glob**, which is the exact flake the
narrowing exists to close. Measured with `SRMECH_HOOK_GIT=/nonexistent/git`:

```
_tracked_names(root)   -> {'src': 0, 'include': 0}
mod._C_SRC_DIR         -> still a raw WindowsPath (not narrowed)
mod._c_files()         -> 139 files, i.e. everything on disk
echoed to stderr       -> nothing at all
```

Combined with the counterfactual two sections up (naive glob + the planted
untracked fixture → 1 RED), an unresolvable git during a `check_hooks.py` run
reproduces **exactly** the unreproducible block the design section calls "closed
by construction". A silent degradation to the broken behaviour is worse than no
narrowing. It now raises `TrackedSetUnavailable` and the hook fails **open** with
a note naming the git binary that could not answer — and `check_hooks.py`
asserts that against a **red** fixture, so the row also proves an infrastructure
failure is never reported as a measurement in either direction.

**And one honesty item.** The `[jpl-pending]` HEAD-commit-message path said
"allowing this stop", which understates it: the token is read off HEAD, so it
allows **every** subsequent Stop for as long as that commit stays HEAD, not one.
It stops applying at the next commit whose message omits it. The note now says
so and names the commit. It is greppable in history, which was always the
point — but it is a standing waiver, not a single one.

## `PostToolUse` — what could and could not be established

The research could not verify `PostToolUse`, and there is no precedent for it in
this tree. What is measurable without activating anything: the installed Claude
Code binary (`2.1.227`) contains the literal string `PostToolUse` **23 times**,
the same count as `PreToolUse`, alongside `SubagentStop` (22), `SessionStart`
(22), `UserPromptSubmit` (14), `Notification` (12), `SessionEnd` (10) and
`PreCompact`/`PostCompact` (9 each). So it is a recognised event name on the
same footing as the events already wired.

**That is evidence the event exists, not proof that a hook bound to it fires.**
Observing it fire requires writing into `.claude/settings.json`, which changes
the behaviour of agents still running and is the user's call — so it was not
done, and nothing here rests on it. **None of the three new hooks uses
`PostToolUse`**: `sha256_routing_gate` runs on `PreToolUse(Edit|Write|MultiEdit)`
and *simulates* the edit from the payload, which is strictly better for a gate —
it can refuse the write, where a `PostToolUse` peer could only complain about a
file that had already changed.

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
