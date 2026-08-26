# F1276 — issue #1454 relayed from the srmech rc-line session: **builtin `hash()` is PYTHONHASHSEED-salted, so 21 research sites keyed word vectors on a value that changes every interpreter invocation.** Verified independently on every checkable claim — **the issue is right.** Two of the sites are **mine** (F1266/F1267). Measured cost: the **effect survives** (revival gap 0.9184 under every salt; sha256 routing reproduces it), but **the exact digits never were reproducible.** The durable fix is not `PYTHONHASHSEED=0` — it is a **CLAUDE.md §2 STOP-list row**, because content-routing *is* a Class-A operation.

## The claim, verified before acting on it
Per MPM discipline a relayed finding gets checked, not assumed. Every checkable claim in #1454 reproduces:

| claim | verified |
|---|---|
| `hash()` salted for str **and bytes** | `hash('the')%80000+11` → **77384 / 76095 / 24618** on three fresh interpreters; bytes identical |
| `PYTHONHASHSEED=0` → 14908 | **MATCH** |
| 21 seed-from-hash sites in 21 files | **exactly 21 / 21** |
| the F1000 line verbatim | **exact** |
| `reproduce.py` exits 0 on CHANGED **and** ERROR | **confirmed** — both branches `print(...)`, `main()` returns `None` |
| `reproduce.py` covers 10 scripts | **confirmed** — 10, against **733** `R-RBS-LM-*.py` in this subtree alone |

*Count differences, stated so they are not mistaken for errors:* I get `/home/skirklan/` absolute paths **144** (issue: 146) and `the_one=` **399 sites / 64 files** tree-wide — but **33 of those files are the vendored `python/srmech` copy**, i.e. srmech's own rc256 source, not research drift; research-side is ~31 files against the issue's 28. My numpy count (514) is higher than the issue's 321 because mine is a grep and theirs is AST-counted. **Scope and method, not disagreement.**

## My own exposure, which the relay did not single out
F1266 (`CHUNKLAW`) and F1267 (`EXPONENT`) route items to chunks with `buckets[hash(k[i]) % n_ch]`. I wrote the comment:

> `# content-routed, deterministic per run`

**That phrase names the defect and I read it as reassurance.** Deterministic *within* a run is exactly what "not reproducible *across* runs" means. This is not only inherited debt — it is a live instance in work I shipped last week, and it went in *after* F1260 repaired the related word-hash defect at the same kind of call site.

**Two different defects, same call sites, worth keeping distinct:** F899/F1260 = `hash()`-as-seed **destroys morphology** (a representation defect). #1454/F1276 = `hash()` **is salted** (a reproducibility defect). Fixing one does not fix the other.

## What it actually cost — measured, not adjectives
Re-ran F1266's headline claim under pinned salts, 48 probes:

| PYTHONHASHSEED | flat store | chunked (hash-routed) |
|---|---|---|
| 0 | 0.0408 | 1.0000 |
| 1 | 0.0408 | 1.0000 |
| 2 | 0.0408 | 0.9592 |

- **spread across salts 0.0408**; **smallest revival gap (chunked − flat) 0.9184**
- **Class-A `sha256_bytes` routing: 1.0000** — inside the pinned band, so it is a **fix, not a substitution**
- `sha256_bytes` route value under `PYTHONHASHSEED` 0 / 1 / random: **17061 / 17061 / 17061** — stable across processes *and* independent of the env var

**Verdict on my sites: the CLAIM holds, the DIGITS never were reproducible.** That is a real defect and not a retraction — the distinction #1454 itself insists on ("cannot currently be trusted", not "disproven").

## Two bugs this harness made, both caught, both instructive
1. **A false PASS.** Part D's subprocess snippet contained `%%` in a *non*-formatted string → `SyntaxError` → every run returned `""` → `len(set(["","",""])) == 1` reported **STABLE**. A dead subprocess read as agreement. Fixed with an emptiness/returncode guard: **an empty result must never count as consensus.**
2. **A threshold finer than the measurement.** At 12 probes the granularity is 1/12 = **0.083**, coarser than the 0.05 threshold — so the test *could not resolve what it was asked* and printed "WITHDRAW". Fixed by raising to 48 probes (granularity 0.021), not by relaxing the threshold. **The F1268 lesson applied in the right direction: raise resolution, never move the bar to fit the data.**

## The fix that generalises
`PYTHONHASHSEED=0` makes stability an **environment variable** rather than a property of the code. Routing/seeding by content **IS Class-A content-addressing**, and the framework already ships the op. CLAUDE.md §2 routed `hashlib.sha256(...)` → `format.sha256_bytes` but said **nothing about builtin `hash()`** — that is precisely the gap all 21 sites and both of mine fell through. **A STOP-list row is now added**, which is what would have caught every one of them at code-writing time.

Historical harnesses are **preserved as-run** with a defect notice (the F1260 precedent: repair live code, preserve probes — rewriting a probe makes it no longer the thing that produced the finding).

## What this does NOT claim
**Nothing about F976–F1001.** That cluster has a documented 4–13 pp self-noise band, and F1000 (+6 pp) / F1001 (−7/−9 pp) sit inside it. Per #1454 they are **"cannot currently be trusted", not "disproven"** — and re-running them is the tree owner's call, not a conclusion this harness gets to reach. What I can say is that the cheap experiment worked here: pinning and re-measuring converted "unreproducible" into a number, and the effect survived.

Composes **issue #1454** (relayed; verified), **F1266/F1267** (the two sites that are mine), **F899/F1260** (the *other* defect at the same call sites), **F1268** (the resolution lesson, applied), CLAUDE.md §2 STOP-list, `[[feedback_computational_provenance_discipline]]`, `[[feedback_three_things_called_random_derived_drawn_stochastic]]`.

## The enforcement question, answered — and what it exposed

**`hash()` comes from no library.** It is `builtins.hash`, a `builtin_function_or_method` baked into the interpreter. **There is nothing to import, so there is nothing to block.** That is precisely why it evaded every existing guard:

| guard | why it missed `hash()` |
|---|---|
| pip-refusal (how numpy was purged, #564) | **no package to refuse** |
| import-checking | **no import statement exists** |
| the pre-commit hook | patterns keyed on `import numpy` / `hashlib.sha256` — `hash(` needs neither |
| CLAUDE.md §2 STOP-list | routed `hashlib.sha256`, silent on the builtin |

The hook's own header already conceded this class of problem for `Counter`: *"stdlib so it can't be pip-blocked like numpy (no install to refuse) — this commit-gate is the equivalent guard."* **`hash()` is one level worse than stdlib: it is builtin.** So the only possible enforcement points are lint-time and commit-time. Both are now wired:

1. **`check_srmech_discipline.py`** — new HARD rule, AST-based (`ast.Call` with `func=ast.Name(id='hash')`), so prose can never false-positive. **Fires on 26 sites.**
2. **`git-hook-srmech-discipline.sh`** — `hash(` added to the blocked patterns, diff-aware so existing uses are grandfathered.

**Scope note, deliberate:** `hash()` on int/float/tuple-of-int is **NOT** salted (`hash(42)` is stable across runs) — verified. So the rule over-blocks slightly, on purpose; `# srmech-allow: <reason>` is the escape. Over-blocking with an escape hatch beats under-blocking.

### A hook defect fixed on the way
The hook grepped **every** added line including `.md`, so a finding that *discusses* an idiom tripped the guard — the script's own header admits it *"avoids the literal idiom spellings on purpose so it does not flag itself."* **A guard that forces its own documentation not to name what it guards is a defect, not a discipline.** Prose files (`.md/.txt/.rst/.ndjson`) are now excluded; verified prose-only staging exits 0 while prose+code exits 1.

**Residual limitation, not papered over:** prose *inside* `.py` docstrings still trips the grep, and I burned several rounds adding `srmech-allow` markers to documentation lines. The structural fix is for the hook to **delegate `.py` to the AST checker** (prose-safe by construction) and grep only non-Python. I did **not** make that change — it alters shared tooling semantics (whole-file AST vs diff-aware grep) and is the tree owner's call. **Proposed, not done.**

### What turning the rule on exposed
| | |
|---|---|
| total HARD now | **142** across 733 files |
| of which the new `hash()` rule | **26** |
| **pre-existing** (`abs`, `hashlib.sha256`, `np.linalg.*`) | **116** |
| `DISCIPLINE_BASELINE.json` | **32** across 21 files |
| ratchet exit | **71 regressions — FAIL** |

**The AST ratchet was already failing before my rule** — 116 of the 142 are pre-existing, against a baseline of 32. It is a *working* gate (exit code = regression count; my first reading of "exit 0" was `tail`'s status, not the checker's) that **nothing is running.** That independently corroborates #1454 §3: the research tree has essentially no verification.

**I did not regenerate the baseline.** Doing so would convert 110 real violations into a clean bill of health — the precise move the "violations only go DOWN, never up" rule exists to forbid. The debt is reported, not absorbed.

### A third guard defect, found by the guard failing to stop me
The pre-commit hook is installed by **manual `cp`** (`cp git-hook-srmech-discipline.sh "$(git rev-parse --git-path hooks)/pre-commit"`). The installed copy in `.git/hooks/` was dated **Jun 18 — a month stale.** So while I edited the source and watched it print CLEAN, `git commit` kept running a month-old copy that knew nothing about either fix.

**Source and enforced copy drift silently, and nothing detects it.** That is the same shape as every other finding here: a guard that is not guarding what you believe it is. It also means **any hook improvement anyone has made since Jun 18 was never in force** for this worktree. Reinstalled; but the install step is manual and will drift again. **A `.git/hooks` install is per-clone and per-worktree and is not version-controlled** — the durable answer is a checked-in `core.hooksPath` (or a make/CI step), which is a repo-level decision and is therefore **proposed, not done.**

**→ narrowed by F1277** — F1276 concluded "content-routing IS Class-A content-addressing -> sha256_bytes". That holds for ROUTING (which needs stability only) but must NOT be generalised: for REPRESENTATION, **sha256 is exactly as wrong as `hash()`** (cat/cats 0.2480 vs 0.6597; zero relational compression). The criterion is **resonant bit-serialization**, not a particular op.
