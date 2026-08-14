# PAL resource-cleanup audit — `#T1129`

READ-ONLY code archaeology. Nothing in `docs/srmech/{python,c}` was edited.
Branch `research-pal-cleanup` off `origin/main` at `a3f9fc847` (srmech
v0.9.0rc430). Scanner: `_pal_resource_cleanup_audit.py`. Raw findings:
`_pal_resource_cleanup_audit.ndjson` (54 records: 1 meta, 31 Python scanner
hits, 3 C mkdir sites, 5 C held-handle sites, 14 manual-triage verdicts).

Environment used for every measurement below: WSL2, `python3` 3.10.12,
numpy absent, `PYTHONPATH=/mnt/d/GitHub/mlehaptics/docs/srmech/python`,
`SRMECH_EXPECT_PURE=1`. `srmech.__file__` =
`/mnt/d/GitHub/mlehaptics/docs/srmech/python/srmech/__init__.py`,
`srmech.__version__` = `0.9.0rc430`.

**The seed defect, restated:** `srmech.biology.genome.genome_save`
(`docs/srmech/python/srmech/biology/genome.py:8980`) does
`path.mkdir(parents=True, exist_ok=True)` as its FIRST executable line —
before `leaf_dim` derivation, `_split_into_chromosomes`, `_disk_block`
width validation, or `_resolve_attestation`, every one of which can raise.
A rejected call still leaves `path` on disk.

---

## Q1 — Does the C side have a PAL, and what does it cover?

**YES.** `docs/srmech/c/src/srmech_platform.{c,h}` (1954 + 554 lines,
since v0.7.5rc5). One compilation unit; POSIX / Windows / bare-metal
`#ifdef` lives ONLY here — every other C source file is `#ifdef`-free.

| Surface | Symbols | file:line |
|---|---|---|
| Threads | `srmech_plat_thread_spawn/join`, `has_threads` | `srmech_platform.h:67-76` |
| Mutex | `srmech_plat_mutex_init/lock/unlock/destroy` | `:104-113` |
| Stream IPC (AF_UNIX/named-pipe) | `stream_listen/accept/server_close/connect/read_exact/write_all/conn_close` | `:173-202` |
| **File read** | `file_read`, `file_read_region`, `file_open_ro/read_at/close_ro`, `rstream_open/read/close` | `:225-257`, `:416-426` |
| **File write** | `srmech_plat_file_write` (`append` flag; single fopen→fwrite→fclose) | `:261-262` |
| **Mutating FS (rc284)** | `srmech_plat_mkdir`, `file_remove`, `file_replace` | `:324-338` |
| **Directory iteration** | `dir_open/next/close` | `:381-391` |
| Wall clock / stdio / TCP / sleep | `now_ns`, `stdin_read`/`stdout_write`, `tcp_*`, `sleep_ms` | `:439-552` |

Implementation: `docs/srmech/c/src/srmech_platform.c`, definitions at
lines 74–1947 (grep-listed, one POSIX + one Windows + one
no-filesystem-stub body per symbol where the OS surface differs).

**Does it TRACK anything — open-handle table, created-node registry,
cleanup list?** **Measured: NO.** `grep -in 'registry\|leak\|track\|
accounting\|handle_table\|open_count\|refcount' srmech_platform.{c,h}`
returns zero hits that are actual tracking machinery (the handful of
prose hits are about ThreadSanitizer and unrelated genome/streams
registries). The ONE piece of accounting that exists is
`srmech_plat_file_opens()` / `_opens_reset()` (`:294-298`) — a **read-path
open COUNTER**, diagnostic-only, counting attempts not pairing them with
closes. It cannot answer "is everything this call opened now closed?" —
it only answers "how many `fopen`s happened." **No open-handle table, no
created-node registry, no cleanup list exists anywhere in the PAL.**

**Can a caller/test ask "is everything this call opened now closed?"**
**Measured: NO — YES/NO is a hard NO**, evidenced by the absence above.

---

## Q2 — The `goto` question

**Rule 1 violations: 0**, mechanically pinned. `test_rule_1_no_goto`
(`docs/srmech/python/tests/test_jpl_audit.py:71-85`) regexes for
`\b(goto|setjmp|longjmp)\b` after stripping comments, across every `.c`/`.h`
in `c/src` + `c/include`. A raw grep for the bare word found **198 hits**,
but every one is inside a prose comment of the shape `Rule 1 (no
goto/recursion): OK` — a per-file self-audit note, not code (spot-checked
15 of the 198; all are `*   - Rule 1...` audit-comment lines).

**What replaced it: early return, with the release call INLINED on the
same guard line whenever a resource is actually held at that point.**
The idiom, uniform across the tree:

```c
st = OPEN_FN(...);
if (st != SRMECH_OK) { return st; }              /* nothing acquired yet */
...
if (st != SRMECH_OK) { CLOSE_FN(&h); return st; } /* acquired -- release inline */
...
CLOSE_FN(&h);
return SRMECH_OK;
```

No single-exit jump exists; each exit point re-states its own release.
This is affordable specifically because **Rule 3 (no malloc)** removes
almost everything a `goto cleanup;` would normally free — the only
resources ever actually *held across statements* are the handful of
PAL held-handle opens below.

**Count of functions with an acquire + ≥1 early return between acquire and
release, and whether each release fires:**

| Acquire primitive | Call sites (excl. definitions) | Early returns between open/close | Unsafe (no release) |
|---|---:|---:|---:|
| `srmech_plat_file_open_ro` | 1 (`srmech_genome.c:8588`) | 1 | 0 |
| `srmech_plat_rstream_open` | 2 (`srmech_laplacian.c:2021`, `srmech_ndjson.c:198`) | 3 + 3 | 0 |
| `srmech_plat_dir_open` | 2 (`srmech_genome.c:4804`, `:6607`) | 2 + 2 | 0 |
| `srmech_plat_mkdir` | 3 (all `srmech_laplacian.c:2760/2762/2764`, `rcut_setup`) | 2 sequential-acquire hazard points (see Q4) | see below |

**Is there any function where an error return leaks an open handle or
leaves a created node? Zero for handles.** Every held-handle open/close
pair was verified two ways: (1) the corrected scanner (self-tested against
a planted leak — see Q4 methodology) reports **0 unsafe early returns**
across all 5 held-handle call sites; (2) manual read of each site —
`srmech_genome.c:4804-4824`, `:6607-6623`, `:8588-8592`,
`srmech_laplacian.c:2021-2049`, `srmech_ndjson.c:198-239` — confirms
`CLOSE_FN` on every early-return line and at the natural function end.
**For CREATED NODES (mkdir), the answer is not zero** — see Q4/Q5, the
one real C-side instance is `rcut_setup`'s 3-mkdir sequence.

**Constructor-shaped handles (`srmech_plat_stream_listen` /
`srmech_plat_tcp_listen`) are a separate class**, deliberately excluded
from the open==>close-in-same-function check: their contract is "bind,
then hand the live handle to the caller" (`srmech_bus_serve` /
`srmech_bus_serve_encrypted` return `*out_handle = h` with the listener
still open; the close lives in the separate teardown function
`srmech_bus_server_stop:704`). Manually verified clean: `srmech_bus.c:625,
666` close the allocated handle struct on the LISTEN call's OWN failure
(nothing PAL-level was opened yet) and otherwise correctly hand off;
`srmech_mcp_sse.c:724,732,757` — same shape.

**Does `test_jpl_audit.py` check acquire/release symmetry at all?**
**Measured: NO.** It covers exactly Rules 1 (goto), 3 (malloc), 4 (≤60
lines), 5 (≥2 asserts), 8 (multi-line macros) — see the 5 `test_rule_*`
functions in the file. **Acquire/release pairing is an UNGATED axis.**

---

## Q3 — Dual-projection: does the C peer share the Python defect?

**`genome_save` — DISAGREEMENT, and it is the finding.**

| | mkdir/create call | Ordering vs. validation |
|---|---|---|
| **Python** `genome_save` | `path.mkdir(parents=True, exist_ok=True)` — `genome.py:8980` | **BEFORE.** First executable line. |
| **C** `srmech_genome_save` | **none.** `genome_save_validate(...)` runs FIRST (`srmech_genome.c:3964-3966`); no `srmech_plat_mkdir` call exists anywhere in `srmech_genome.c` (confirmed: `grep -c srmech_plat_mkdir srmech_genome.c` = 0). | N/A — C never creates the directory at all. |

The C function assumes the directory pre-exists; if it doesn't,
`genome_write_file` → `srmech_plat_file_write` → `fopen(path,"wb")` simply
fails with `SRMECH_ERR_IO` (fopen does not create parent directories). This
is **proven by the C test harness itself** —
`docs/srmech/c/test/test_srmech_genome.c:102-125`'s `ensure_dir()` helper
does a raw `mkdir`/`_mkdir` **before every single `srmech_genome_save`
call** in the file (17 call sites, lines 207, 383, 443, 479, 530, 601,
621, 656, 740, 786, 863, 889, 1024, 1042, 1071, 1090, 1099, 1233, 1336 —
every one preceded by `ensure_dir(dir)` or reuses a dir already
`ensure_dir`'d earlier in the same test).

So: **Python has the seed defect (mkdir-before-validate, orphan-on-error).
C does NOT have it — but only because C does not implement the "path/ is
a DIRECTORY this persists into" half of the contract at all.** C is not
immune by being more careful; it is immune by not doing the job the
docstring claims ("Persist a genome `strand` to `path/` (a DIRECTORY)").
A bare-C host with no pre-existing directory and no Python wrapper cannot
call `srmech_genome_save` successfully on a fresh path. This is exactly
the shape the project's own stance on co-equal dual construction predicts:
the disagreement doesn't validate either side — it says one of them is
wrong, and here BOTH are arguably wrong in different ways (Python:
orphans on error; C: doesn't fulfill the directory-creation contract at
all).

### 3–5 other file-touching op pairs, Python vs. C

| Python op | mkdir-before-validate? | C peer | C mkdir? |
|---|---|---|---|
| `genome_save` | **YES** (`:8980`) | `srmech_genome_save` | **NO** (0 calls) |
| `genome_import` (native branch) | **YES** (`:11600`, inside try/except, before native's own integrity checks) | `srmech_genome_import` (invoked via `_native.genome_import_c`) | **NO** — same as above, no `srmech_plat_mkdir` anywhere in `srmech_genome.c` |
| `genome_explode` | **YES** (`:11680`, before per-label safety loop) | `srmech_genome_explode` (`_native.genome_explode_c`) | **NO** |
| `genome_pack` (native branch) | safe — mkdir at `:11769` runs only AFTER the native pack round-trips successfully into a scratch dir | `srmech_genome_pack` (`_native.genome_pack_c`) | **NO** |
| `genome_from_graph` (native branch) | safe — validated first (`:7460`-area) | `srmech_genome_from_graph` | **NO** |
| `recursive_cut` / `srmech_laplacian_recursive_cut` | narrower hazard: 3 sequential `os.makedirs` (`laplacian.py:7200,7203,7204`), no rollback on a later step's failure | `rcut_setup` (`srmech_laplacian.c:2760-2765`) | **YES, and shares the identical narrow hazard** — 3 sequential `srmech_plat_mkdir` calls, no rollback |

**Pattern across ALL 10 genome C write entry points**
(`srmech_genome_save/_append/_remove/_replace/_export/_import/_pack/
_from_graph/_plasmid_extract/_add_plasmid`): **zero** call
`srmech_plat_mkdir`. The ONLY C function anywhere that calls
`srmech_plat_mkdir` is `rcut_setup` in `srmech_laplacian.c` (3 calls, lines
2760/2762/2764). Every genome C write op requires its target directory to
already exist — confirmed by the C test file's `ensure_dir()`-before-every-
call pattern.

**The one place C and Python genuinely AGREE (both have the same
narrower hazard):** `recursive_cut` (Python) / `rcut_setup` (C) — both
validate their real caller-input FIRST, then both create their work
directory in **3 sequential steps with no rollback of earlier steps** if a
later `mkdir` fails (a real IO failure, e.g. permissions/disk-full — not a
caller-input-validation failure). See Q4 for file:line on both sides.

---

## Q4 — How big is the class, in each language?

### Scanner validation (mandatory before trusting any count)

Both scanners (Python AST-walk, C brace-bounded grep) carry a
`--self-test` mode with **planted positive AND negative controls**, run
before every real scan (`_pal_resource_cleanup_audit.py`, invoked
`--self-test` then `--scan`; both must PASS or the script exits 1 and
refuses to run the real scan).

**v1 of the C scanner was itself a measured false-REFUTED/false-positive
instrument, caught by its own controls before being reported:**

| Bug | Symptom | Root cause | Fix |
|---|---|---|---|
| Definition lines counted as calls | `srmech_plat_mkdir`: 5 "call sites" (should be 3) | regex matched the function's own `srmech_status_t srmech_plat_mkdir(...)` signature line | filter lines where the fn name is immediately preceded by a return-type token |
| Unbounded 60-line lookahead, not scoped to the enclosing function | 20 "unsafe" held-handle sites (should be 0) | scan window could spill past the function's own closing brace into unrelated code | brace-depth function-span detection (ported from `test_jpl_audit.py`'s own `_scan_functions`) bounds the window to the call's OWN enclosing function |
| Open-call's own status-check counted as "unsafe" | even the corrected scanner initially flagged `safe_reader`'s FIRST `if (st != SRMECH_OK) return st;` | the guard checking the OPEN call's own result needs no close (nothing was acquired) | skip the first early return encountered after an acquire; only subsequent ones require the paired close |
| Constructor-shaped handles (`stream_listen`/`tcp_listen`) flagged on their SUCCESS return | 2 "unsafe" (`srmech_bus_serve`, `srmech_bus_serve_encrypted`) | those functions hand the live handle to the caller by design; the close lives in a separate teardown fn | excluded from the same-function-must-close check; verified clean by manual read instead |

Final counts (self-tested, `_pal_resource_cleanup_audit.ndjson` `meta`
record): **3** `srmech_plat_mkdir` call sites, **5** held-handle open sites,
**0** unsafe.

The Python scanner's OWN documented false-positive class (Tier-B bare-name
cross-contamination, line-order-not-CFG reachability, try/except-with-
return not recognized as protection) is proven by 4 of the 31 raw hits
being REFUTED on manual read — see the triage table below. This is the
"an instrument that cannot return otherwise is not a measurement" — and
also the "it can also return a FALSE REFUTED" — discipline in practice:
**both directions of scanner error were caught and are reported**, not
just the reassuring one.

### Python: 264 `.py` files, 4,756 functions scanned, 31 raw scanner hits, manually triaged to:

| Severity | Count | Instances |
|---|---:|---|
| **HIGH** (matches the seed-defect shape exactly, confirmed) | 5 | `genome_save:8980`, `genome_import:11600` (native), `genome_explode:11680`, `genome_register_attested:11927`, `pack_mcpb:318` |
| **MEDIUM** (confirmed, narrower — partial-file or partial-loop, not full seed-defect shape) | 3 | `write_ndjson:373`, `recursive_cut:7200/7203/7204`, `genome_register_attested` inner loop `:11941/11942/11953` |
| **LOW / benign** (structurally matches, but targets a shared idempotent resource or the real per-call resource closes correctly on its own path) | 3 sites | `_transport.py` bind() ×3 (`:211,312,682`) |
| **REFUTED** (scanner false positive, manually disproven) | 4 | `genome_import:11627` (mutually exclusive branch), `genome_pack:11829` (validated-before-acquire), `genome_partition:7340-7341` (validated-before-acquire), `genome_from_graph:7556-7557` (validated-before-acquire), `Writer.enter:165,174` (try/except-with-return, not try/finally — scanner limitation) |
| Not deep-dived (time-boxed; flagged `has_later_cleanup_attempt=True`, appears well-behaved) | remainder | `_kext_from_edges:642`, `genome_pack:11764` (tempfile+finally-rmtree — real protection the scanner's AST-adjacency check missed since the acquire sits BEFORE the try, not inside it), `_write_body_and_manifest:11153`, `genome_save:9059` (both are the terminal write step of an already-mkdir'd, already-validated path) |

Full file:line detail for every HIGH/MEDIUM instance is in the `manual_triage`
NDJSON records (14 total) and reproduced in Q5's ranked list.

### C: 3 `srmech_plat_mkdir` call sites — ALL 3 in `rcut_setup`

```
srmech_laplacian.c:2760   srmech_plat_mkdir(work_dir)
srmech_laplacian.c:2762   srmech_plat_mkdir(s->queue_dir)
srmech_laplacian.c:2764   srmech_plat_mkdir(s->tomes_dir)
```

Each checked (`if (st != SRMECH_OK) { return st; }`), no rollback of an
earlier successful mkdir if a later one fails. **This is the one genuine
C-side instance of the orphaned-resource-on-error-path class** — and its
Python peer (`recursive_cut`) has the identical shape at the identical
granularity (3 sequential creates, no rollback). Reachability: real (an
IO failure on the 2nd or 3rd mkdir — permission/disk-full on a
concurrently-modified filesystem — leaves 1–2 already-created directories
behind while the whole op returns an error). Lower severity than the
HIGH Python-only class because (a) it requires an actual IO failure, not
merely bad caller input, and (b) `work_dir` is typically a scratch
directory the caller already owns and expects to manage, not a
surprise side effect.

---

## Q5 — Mechanical detectability: could this be a gate?

### Python predicate

What the scanner implements: *"a call to `mkdir`/`makedirs`/write-mode
`open`/tempfile-create, not inside a `with`, not inside a covering
`try/finally`, followed (directly or via a same-named callee anywhere in
the package) by a `raise`."*

**False-positive class, measured, not hypothetical — 4 of 31 raw hits
were false positives:**
1. Line-order heuristic has no real control-flow graph — a raise in a
   mutually exclusive branch reads as "later" (`genome_import:11627`,
   `genome_pack:11829`, `genome_partition:7340`, `genome_from_graph:7556`).
2. Bare-name Tier-B resolution is whole-package — two unrelated
   `_validate`-shaped functions in different modules would cross-
   contaminate (not observed to bite in this scan, but structurally
   possible and unratcheted).
3. `try/except`-with-clean-return is real protection the scanner doesn't
   recognize (only `try/finally` is checked) — `Writer.enter:165,174`.
4. A `try/finally` that cleans up a SIBLING statement before it (not one
   that wraps it) is also missed — `genome_pack:11764`'s
   `tempfile.mkdtemp()` sits before its own `try/finally: rmtree`, which
   is real protection the AST-adjacency check doesn't see.

**A deliberately-resumable/partial artifact (a journal, a lock file, a
resumable write) is NOT a defect, and this scanner cannot tell that case
from an orphan.** None of the 31 hits in this codebase are that shape —
every mkdir found targets either a fresh caller-named destination or a
scratch work directory the caller is told it owns (`recursive_cut`'s
`work_dir` docstring: *"the caller owns it; it is NOT auto-deleted"*) —
but the scanner has no way to KNOW that from source alone; distinguishing
"designed to persist" from "orphaned" requires reading the docstring/
contract, which is exactly what the manual triage did for every hit
above and what a gate cannot do unattended.

**Verdict: NOT directly gate-able as a zero-false-positive ratchet.** A
BOUNDED, honest version is possible: drop the raise-reachability
heuristic (its recall/precision tradeoff is the whole problem) and gate
on the coarser, purely STRUCTURAL fact — *"count of mkdir/write-open/
tempfile acquire call sites with NO covering try/finally and NO context
manager at all"* — then hand-maintain an allowlist for the confirmed-
benign ones (the 3 `_transport.py` sites, `Writer.enter`), exactly the
same shape as the existing `RULE_3_COLD_PATH_FILES` / `RULE_5_EXEMPT_
FUNCTIONS` allowlists in `test_jpl_audit.py`. That IS a legitimate
down-only ratchet pattern this codebase already uses successfully
elsewhere — it would need a documented-rationale entry per exclusion,
same discipline.

### C predicate

Given no-`goto` (Rule 1, mechanically pinned at 0), the C predicate is
much cleaner: *"for every PAL held-handle acquire call, is there an early
return between it and the matching close call, within the SAME
enclosing function (brace-bounded), that does not call the close on that
line?"* This is what the corrected scanner implements, and after fixing
the three v1 bugs (see Q4 table) it found **zero** false positives against
its own planted leak/safe controls, and **zero** real hits against the
actual PAL consumers.

**Verdict: C-side IS realistically gate-able**, close to the existing
JPL ratchet discipline (`test_rule_1_no_goto` etc.) — the codebase's
uniform idiom (early-return + inline release, exactly one acquire/release
shape per resource type, no malloc) is precisely what makes it
mechanically decidable, unlike Python's branchier, exception-heavier
style. A companion `test_rule_11_pal_acquire_release_symmetry`-shaped
test in `test_jpl_audit.py` — same file, same down-only-ratchet
philosophy — is directly implementable from this session's corrected
scanner logic, EXCLUDING the constructor-shaped `stream_listen`/
`tcp_listen` pair (which need the SEPARATE "handle handed to an out-param
or struct field that a documented teardown fn closes" check, not the
same-function-close check).

**Does the mkdir-sequence-no-rollback narrower hazard generalize as ONE
check across languages?** Partially — `recursive_cut` (Python) /
`rcut_setup` (C) share the exact shape (N sequential creates, no
rollback), and a predicate of that specific form ("2+ create-type calls
in the same function/scope with no compensating removal of earlier ones
on a later failure") could be PHRASED identically in English for both,
but the IMPLEMENTATIONS cannot be the same instrument — Python needs an
AST walker, C needs the brace-bounded grep approach — so it would be two
gates sharing one spec, not one gate.

### Does the Rosetta/parity apparatus already cover this axis?

**No.** `grep -in 'cleanup\|leak\|orphan\|mkdir\|resource'
docs/srmech/c/ROSETTA_LEDGER.md` (1614 lines) returns 2 hits, neither
about resource cleanup (one is "schema leak" in an unrelated MCP row, one
is "sum-of-squares leak" in a linear-algebra proof). **This axis is not
carried by any existing cross-projection gate.**

### Bottom line

**Separate instruments for each language.** Python: not gate-able as a
strict ratchet without a real CFG (the honest bounded version drops
reachability and gates on bare structural coverage + a maintained
allowlist). C: gate-able now, following the exact pattern the JPL audit
already uses, EXCLUDING the constructor-handle class which needs a
different, still-mechanical, still-implementable check.

---

## Ranked areas to look at first

1. **`genome_save` (`genome.py:8980`)** — the seed defect itself, HIGH,
   confirmed. Fix shape: move `path.mkdir(...)` to just before the first
   disk write (after `record = _manifest_record(...)` succeeds), matching
   the discipline the code's OWN comment at `:9055-9057` already states
   for the pure-Python tail ("Build + VALIDATE the record BEFORE any bytes
   hit disk") — that principle just needs to also cover the mkdir, not
   only the write.
2. **`genome_import` native branch (`genome.py:11600`)** — HIGH,
   confirmed, and the try/except there converts the native error type
   without releasing the directory it just created.
3. **`genome_explode` (`genome.py:11680`)** and **`genome_register_
   attested` (`genome.py:11927` + inner-loop `:11941-11953`)** — HIGH +
   MEDIUM, same shape: mkdir before a label-safety check that can fail on
   ANY later item in a loop, not just the first.
4. **`pack_mcpb` (`mcp/_mcpb.py:318`)** — HIGH, confirmed via
   `build_manifest`'s `assert server_type in (...)`.
5. **`rcut_setup` / `recursive_cut`** (`srmech_laplacian.c:2760-2765` /
   `laplacian.py:7200-7204`) — MEDIUM, the one place BOTH projections
   share the identical narrower hazard; lowest-effort fix (track which
   of the 3 mkdirs succeeded, `rmdir`/`shutil.rmtree` on a later failure)
   and the one instance where fixing once and porting the fix is
   genuinely symmetric.
6. **The C genome write surface's missing mkdir entirely** — not a "bug"
   exactly, but worth a maintainer decision: either C should call
   `srmech_plat_mkdir` before validation-passed writes (inheriting the
   Python defect, so needs the SAME post-validation-only placement,
   not a copy of the current Python bug), or the docstring contract
   ("Persist ... to `path/` (a DIRECTORY)") should be corrected to state
   that C requires a pre-existing directory. Currently the C test suite's
   own `ensure_dir()`-before-every-call pattern is the only place this
   requirement is stated at all.
7. **`test_jpl_audit.py`** — add the acquire/release-symmetry ratchet for
   C (realistic, patterned on this session's corrected scanner); consider
   a bounded, allowlisted Python structural ratchet as a second, separate
   test.

---

## What turned out to be wrong in the brief (or usefully sharpened)

- **The `goto` framing was correct, but the "canonical idiom" tension
  resolves more simply than implied.** The brief frames "Rule 1 forbids
  goto, but `goto cleanup;` is the canonical idiom" as a real tension to
  resolve. In practice there is almost no tension IN THIS CODEBASE: Rule 3
  (no malloc) already eliminates nearly everything a `goto cleanup;` would
  exist to free, so the "replacement" is not a clever pattern — it is
  mostly the absence of the problem `goto cleanup` solves, plus manual
  per-site release calls for the small number of genuinely held handles.
  Worth stating plainly rather than as a resolved dramatic tension.
- **The seed defect's own narrative link between `genome_save` and
  `write_packed_graph` ("wants a FILE… hit IsADirectoryError") is about a
  PATH COLLISION between two unrelated ops sharing one node name — not
  about `write_packed_graph`'s own acquire-before-validate behavior.**
  `write_packed_graph` (`laplacian.py:6916`) does have a same-shaped
  weaker instance of its own (`open(path,"wb")` truncates before per-edge
  validation can raise `ValueError`), but that is a SEPARATE, secondary
  finding, not the mechanism the brief's framing implies — worth not
  conflating the two when writing this up further.
- **"Does srmech have a PAL" undersold how deliberately the PAL is
  scoped.** It is not a generic OS shim; its own header explicitly frames
  itself as "a second hardware-abstraction sibling of the HAL" (the SIMD
  layer) and each surface documents WHY it exists and WHICH consumer
  drove it (e.g. mutating FS ops exist specifically because
  `recursive_cut` needed them). That intentionality is why the "no
  tracking at all" finding in Q1 reads as a real gap rather than an
  oversight — the PAL's designers clearly thought hard about every
  surface they added, and resource-cleanup accounting was never one of
  them.
- **My own scanner was wrong twice before it was right** (documented in
  Q4's bug table) — both a false-REFUTED-adjacent bug (missed the 60-line
  window in the wrong function) and a false-positive bug (flagged
  definition lines and success-path constructor returns). Both are left
  in the shipped script as documented history + guarded by the
  self-test, per the brief's own discipline about controlling instruments
  rather than trusting a first pass.

---

## File index

- `docs/srmech/notes/_pal_resource_cleanup_audit.py` — the scanner
  (self-tested Python AST walker + C brace-bounded grep), run via
  `--self-test` then `--scan`.
- `docs/srmech/notes/_pal_resource_cleanup_audit.ndjson` — raw output: 1
  `meta`, 31 `py_finding`, 3 `c_mkdir_site`, 5 `c_held_handle_site`, 14
  `manual_triage`.
- `docs/srmech/notes/_pal_resource_cleanup_audit.md` — this file.
