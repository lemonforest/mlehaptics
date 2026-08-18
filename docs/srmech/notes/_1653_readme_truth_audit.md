# gh #1653 — definition-of-done item 8: the README / introspect TRUTH AUDIT

**Round 2 PRE-rcN research.** Which statements in the tree assert co-equal projections, or claim a
host with no Python can drive the same capability set — and which of them are actually true.

- **Reproducible check:** `docs/srmech/notes/_1653_readme_truth_audit.py` (runs, exit 0, 36 NDJSON
  records → `_1653_readme_truth_audit.ndjson`).
- **Measured at:** srmech `0.9.0rc444`, native ABI 17, `has_native=True`, `dispatching=True`.
- **Grounded on:** the round-1 measurements in `_1653_PRERCN_REPORT.md` (re-verified live by this
  script's PASS 3b — parse 11/20, run 0/20, reproduces exactly).

```bash
cd docs/srmech/python && python3 ../notes/_1653_readme_truth_audit.py
```

---

## 0. Headline — three findings, in order of consequence

**FINDING 1 — the issue names README line 16, and line 16 carries FIVE separate claims, not one.**
It is a single ~1.5 KB paragraph. Two of the five are fine, one is a literal, one is misleadingly
unscoped, and **one is flatly false**. Grading "line 16" as a unit is what let the false clause hide
behind the true ones. The verbatim clause that is false is:

> so a host with **no Python present** can serve tools, **run cascades**, and speak the bus

**FINDING 2 — the two-grammar split is the entire mechanism.** "Run cascades" is **TRUE of Surface B
and FALSE of Surface A**, and the sentence names neither. Round-1 measured both in *one* bare-C
binary with no libpython linked:

| grammar | population | C parse | C run |
|---|---|---|---|
| **SURFACE B** `[[catalog.operator_chain]]` / `[[stage]]` | 7 targets | **7 / 7** | **7 / 7** (attested parity 7/7) |
| **SURFACE A** `[[cascade.chain]]` — *the packaged cascade catalog* | 20 declared variants | 11 / 20 | **0 / 20** |

All 21 shipped `cascade_catalog` descriptors are Surface A. So the population a reader would *call*
"the cascade catalog" is exactly the population C cannot run.

**FINDING 3 — a number in the tree has ALREADY rotted, and it rotted into the compiled C binary.**
This is the `#T992` failure the issue warns about, live, right now. The
`srmech.dsl.run_cascade_chain` ToolEntry says the catalog holds **17 executable / 3 leaf**. Live:
**18 / 3** (`klein4_from_one` landed at rc438; the prose did not follow). It ships in **three
projections of the same sentence**, and the third is a `const` C table compiled into `libsrmech`:

```
python/srmech/introspect/_tool_docs_curated.py:3834   says 17, live is 18   [WHEEL — hand-edit source]
python/srmech/introspect/_tool_docs.py:294            says 17, live is 18   [WHEEL — generated]
c/src/srmech_tool_registry.c:16809                    says 17, live is 18   [WHEEL — COMPILED]
```

The bare-C MCP server hands its clients the wrong count with no Python in the process. `describe()`
and the C registry are supposed to be co-equal projections of one tool schema (ADR-0009) — and here
they are faithfully co-equal **in being wrong together**.

---

## 1. The audit table

`wheel?` = does this text reach a user through the PyPI page, `describe()`, the MCP tool list, or the
compiled binary. Verified: `python/pyproject.toml:42` makes `README.md` the dynamic
`long_description`, and `:192` packages it.

Verdicts are graded against the round-1 measurements. **Cite the `id`, never a line number** — the
script locates every claim by regex and reports the current line, so ids are stable and line numbers
are not.

| id | file:line | verbatim (clause) | verdict | surface | corrected | wheel? |
|---|---|---|---|---|---|---|
| `R16-A-capability-set` | `python/README.md:16` | "**Two implementations, one capability set.**" | **MISLEADING** | both | *Two implementations, one capability set — as the governing **discipline** (ADR-0009), not as a claim of achieved coverage. Where coverage is short it is enumerated, never asserted away.* | **YES** |
| `R16-B-no-python-run-cascades` | `python/README.md:16` | "so a host with **no Python present** can serve tools, run cascades, and speak the bus" | **FALSE** | A false / B true | *…can serve tools, run the `[[catalog.operator_chain]]` / `[[stage]]` chain grammars, and speak the bus. The `[[cascade.chain]]` grammar of the packaged cascade catalog is **not yet C-runnable** — the live count is `describe()["cascade_catalog"]["c_runnable"]` of `["executable"]`, pinned down-only (#1653).* | **YES** |
| `R16-C-663-registry` | `python/README.md:16` | "in-C tool dispatch over the 663-entry tool registry" | TRUE-BUT-LITERAL | n/a | *…over the tool registry (`describe()["tools"]["total"]` entries, `["mcp_callable"]` of them MCP-callable)* | **YES** |
| `R16-D-neither-is-reference` | `python/README.md:16` | "related by projection rather than by rank — neither is the reference" | **TRUE** | both | — | **YES** |
| `R16-E-parity-byte-identical` | `python/README.md:16` | "parity means *byte-identical results*, not similar behaviour" | **TRUE** | both | — | **YES** |
| `R18-coverage-enumerated` | `python/README.md:18` | "Coverage is **not** yet complete, and the gap is enumerated rather than asserted away" | **MISLEADING** | A | *…and each gap is enumerated rather than asserted away — the genome wire-glue surface under [C-host coverage], **and the `[[cascade.chain]]` C-run gap under its own down-only ratchet (#1653)**, read live from `describe()["cascade_catalog"]`.* | **YES** |
| `R575-adr-framing` | `python/README.md:575` | "ADR-0003 commits srmech to running standalone on a C host with no Python present; ADR-0009 frames…" | **TRUE** | both | — (the **model paragraph**: it states the commitment, then immediately says "Neither is a claim that coverage is currently complete") | **YES** |
| `R579-ratchet-zero` | `python/README.md:579` | "As of v0.9.0rc334 that count is **0**" | TRUE-BUT-LITERAL | wire-glue | *As of this release that count is `len(CEIL_WIRE_GLUE_GAPS)` — asserted down-only by `tests/test_rosetta_transitive_standalone.py`. Quote the ratchet, not a transcribed integer.* | **YES** |
| `R60-c-only-host-q61` | `python/README.md:60` | "A **C-only host** reassembles the same exact rational from the peers" | **TRUE** | leaf scalars | — (verified: the 5 `*_series_truncate` chains ran correct exact values with no libpython **and no libm**) | **YES** |
| `TD-run-cascade-chain-17-explanation` | `_tool_docs_curated.py:3834` | "``describe()['cascade_catalog']`` counts the catalog (17 executable / 3 leaf)" | **FALSE** | A | *…counts the catalog (its `executable` / `leaf` split)* — name the live keys, stop transcribing their values | **YES** |
| `TD-run-cascade-chain-17-example` | `_tool_docs_curated.py:3800` | "'cyclic_gcd' — any of the 17 executable descriptors" | **FALSE** | A | *'cyclic_gcd' — any descriptor whose `describe()["cascade_catalog"]["status"]` is `executable`* | **YES** |
| `CREG-run-cascade-chain-17-compiled` | `c/src/srmech_tool_registry.c:16809` | "any of the 17 executable descriptors" (in a `const char *` table) | **FALSE** | A | regenerated, never hand-edited — see §4 | **YES (COMPILED)** |
| `TD-run-catalog-chain-bounded-MODEL` | `_tool_docs_curated.py:1960` | "When every step is in the bounded Class-N C dispatch table and the referenced integers fit int64, the whole chain runs in C (``srmech_catalog_run_chain``) to byte-identical output; anything else falls through to the complete pure path — never a wrong answer, only a slower one." | **TRUE** | B | — **THE MODEL SENTENCE.** See §3. | **YES** |
| `W-compose-run-bounded-table` | `c/src/srmech_compose_run.c:7` | "dispatching a BOUNDED set of shipped-chain ops (all Class N: …)" | **TRUE** | A | — **do not weaken this**; the README should be corrected *toward* it | **YES** |
| `W-catalog1341-barec-lists-runs` | `python/srmech/amsc/catalog.py:1341` | "A bare-C host lists / runs a catalog's declared chains with these peers + the srmech_toml parser" | **TRUE** | B | — (names its own peers, so the scope is explicit) | **YES** |
| `W-catalog1311-descriptor-read` | `python/srmech/amsc/catalog.py:1311` | "The descriptor discovery + FS read stay host-side (a bare-C host reads the descriptor with the srmech_toml parser)" | **TRUE** | B | — | **YES** |
| `W-catalog89-registry-kernel` | `python/srmech/amsc/catalog.py:89` | "a bare-C host runs the catalog registry/kernel/…" | **TRUE** | B / registry | — | **YES** |
| `W-tomlchain74-c-only-front-end` | `python/srmech/dsl/_toml_chain.py:74` | "C-only-host chain-spec TOML->canonical-JSON front-end (no Python TOML hop)" | **TRUE** | B | — | **YES** |
| `CLI-dsl-run-toml-chain` | `python/srmech/cli/main.py:109` | "run (execute a TOML chain spec), ops (list cascade-catalog ops)" | **TRUE** | B | — see §2.3: the CLI has **no** Surface-A run route at all | **YES** |
| `W-mcp321-coequal-literal` | `c/src/srmech_mcp.c:321` | "capability the invariant and the two projections co-equal, so this literal…" | **TRUE** | MCP registry | — (asserts the discipline, then points at the pinning test) | **YES (COMPILED)** |
| `W-header342-stale-lib` | `c/include/srmech.h:342` | "projections are co-equal. Rejecting the stale lib is the only safe read." | **TRUE** | ABI | — (co-equality used as a *premise*, not asserted as coverage) | **YES (COMPILED)** |
| `CM-full-c-parity-no-exceptions` | `docs/srmech/CLAUDE.md:451` | "full C parity for every primitive class, no exceptions" | **TRUE** | primitive classes | — see §2.2: the primitives really are there; the gap is the chain dispatch table | no |
| `CM-136-coequal-pure-python` | `docs/srmech/CLAUDE.md:136` | "pure-Python (co-equal parity — no C-callback; standalone-C sector dispatch is the tracked follow-up)" | **TRUE** | klein4 dispatch | — declares the C side **absent** and files it; the honest shape | no |
| `CM-464-toml-no-python` | `docs/srmech/CLAUDE.md:464` | "manifests and TOML descriptors with no Python present" | **TRUE** | TOML/JSON | — | no |

**Tally:** 24 anchored claims, 0 anchors missing. **4 FALSE**, **2 MISLEADING**, 2 TRUE-BUT-LITERAL,
16 TRUE. **6 of the 6 FALSE-or-MISLEADING ship in the wheel** — none of this is internal-only prose.

---

## 2. Why each FALSE / MISLEADING verdict, and the axis it hides

### 2.1 `R16-B` — "run cascades" is the load-bearing false clause

The plural noun does the damage. There is no qualifier, so a reader maps "cascades" onto the thing
the package calls a cascade catalog — 21 descriptors, all Surface A, **0 of 20 C-runnable**. The
clause is simultaneously true, because Surface B exists and genuinely runs in C. One sentence,
opposite verdicts on two grammars, no naming of either. Round 1 put it exactly right: **no single
number can describe both grammars, and any ratchet must name its surface.**

The gap is also **not** the arithmetic. Proven in one process: `srmech_gcd(12,18) → 6` and
`srmech_cascade_cyclic_gcd_u64(12,18) → 6`, both `SRMECH_OK`, in the same binary that had just
declined the `cyclic_gcd` chain declaring `class=I op=gcd`. The dispatch table is the wall.

### 2.2 `R16-A` — discipline read as coverage

ADR-0009 is a *governance* document and says so ("the capability is the invariant"). Read as
governance the sentence is right. Read as coverage — which is how a bolded headline reads — it is
false on Surface A. Note that **ADR-0009 itself never over-claims**: §1.2 tabulates four rcs that
"shipped without a C implementation while carrying language asserting they had one", and §5 requires
a decline to file a tracked gap. The ADR is the cure; the README headline is an instance of the
disease the ADR was written about.

`CLAUDE.md:451` shows the same words used correctly — "full C parity for every primitive class"
scopes itself to the **classes**, which measurement upholds.

### 2.3 `R18` — the enumeration promise outruns the enumeration

"the gap is enumerated rather than asserted away" is the right instinct and the section it links
enumerates only the **genome wire-glue** surface (`CEIL_WIRE_GLUE_GAPS`, down-only, currently 0).
The Surface-A cascade-chain gap is enumerated **nowhere**. So today the sentence over-promises the
*enumeration*, not the coverage — a subtler failure than an over-claim, and the one an rcN can
actually fix, because the fix is to add the missing ratchet rather than to soften the prose.

Consistency check on the CLI half of the same README sentence: `srmech dsl run` executes a **TOML
chain spec** (Surface B) and `srmech dsl ops` only *enumerates* Surface A. There is no CLI route that
runs a `[[cascade.chain]]` descriptor, in C or otherwise — so the CLI clause is Surface-B-only too.

### 2.4 `TD-*` / `CREG-*` — the rot is not hypothetical

Two sites (`explanation` and `example.input.op_name`) × three projections = the same wrong integer in
four textual occurrences across three files. Confirmed reaching users from the **live** ToolEntry, not
just from a file:

```
LIVE ToolEntry srmech.dsl.run_cascade_chain
  transcribed 'N executable' literals ... [17, 17]
  live cascade_catalog.executable ....... 18
  WRONG literals shipping to users ...... [17, 17]   <== FALSE prose in the wheel
```

The irony is instructive: the sentence's whole purpose is to send the reader to the live read, and
then it transcribes the value anyway. That is the shape to hunt for — **not** "is this number
currently right", but "is this number a copy".

---

## 3. The model sentence — what a corrected claim looks like

There is already a sentence in the tree that does this correctly, and every fix in §1 is this
sentence's shape applied to a different surface. From `run_catalog_chain`
(`_tool_docs_curated.py:1960`), shipping in the wheel:

> When every step is in the bounded Class-N C dispatch table and the referenced integers fit int64,
> the whole chain runs in C (`srmech_catalog_run_chain`) to byte-identical output; anything else falls
> through to the complete pure path — never a wrong answer, only a slower one.

Four properties worth naming, because a corrected README:16 needs all four:

1. **States the precondition** ("every step in the bounded table", "integers fit int64") instead of
   asserting the capability unconditionally.
2. **Names the symbol** — `srmech_catalog_run_chain` — so the claim is checkable by `grep`, which is
   what `introspect/_c_claims.py` exists to mechanise.
3. **States the fallback and its cost** — "never a wrong answer, only a slower one".
4. **Implies its surface** by naming a peer that only exists on that surface.

`c/src/srmech_compose_run.c:7` is the Surface-A counterpart and is equally honest ("a BOUNDED set of
shipped-chain ops (all Class N…)"). **Both should be left alone.** The correction runs one way: the
README moves toward the C comments, never the reverse.

---

## 4. Ships-in-wheel — flagged separately, because these need the regen path

This is the part a text-edit pass would get wrong.

| tier | items | what a fix requires |
|---|---|---|
| **free prose in the wheel** | `R16-A/B/C`, `R18`, `R579` (`python/README.md`) | edit the file. It is the dynamic PyPI `long_description` (`pyproject.toml:42`) **and** a packaged file (`:192`), so it reaches users on the PyPI page and in the sdist. |
| **generated ToolEntry prose** | `TD-run-cascade-chain-17-explanation`, `TD-run-cascade-chain-17-example` | edit **`_tool_docs_curated.py`** (the hand-edit source) then **`tools/regen_all.py`**. `_tool_docs.py` is GENERATED and its own header says text written there "is destroyed by the next `tools/gen_tool_docs.py` run" — which the file records as having actually happened between rc274 and rc290. Editing the generated file is the known-failing move. |
| **COMPILED into `libsrmech`** | `CREG-run-cascade-chain-17-compiled` | `regen_all.py` **plus a rebuild and restage of `libsrmech`**. `srmech_tool_registry.c` is a `const` data table whose own header reads "GENERATED … DO NOT EDIT BY HAND." Until the rebuild lands, the **bare-C MCP server** keeps serving the wrong count — with no Python in the process, which is precisely the host the claim is about. |
| **not shipped** | `CM-*` (`docs/srmech/CLAUDE.md`) | plain edit; all three are TRUE anyway. |

**One edit, one regen, one rebuild — not three edits.** The three stale sites are one sentence in
three projections; correcting them independently would be the ADR-0009 drift failure in miniature.

---

## 5. The blocker on the issue's own requirement — and what the rcN must add

The issue requires the statements be **"keyed to live values rather than literals."** For the
`663`-entry registry that is available today (`describe()["tools"]["total"]`). **For the claim that
actually matters it is not.** Measured:

```
describe()["cascade_catalog"] keys: ['enumerate','executable','leaf','run','status','total']
MISSING live-read fields ..... ['c_runnable', 'c_parse_accepted', 'c_run_accepted']
```

There is **no live value anywhere in the package** that a corrected README:16 could be keyed to.
`describe()` will tell you the catalog holds 18 executable descriptors; nothing will tell you that a
bare-C host runs 0 of them.

**So the corrected sentence and the new field are one deliverable, not two.** Rewriting the prose
without adding the field just swaps one literal for a different literal, and the rot recurs. The
audit measures the number in the meantime, which is what the field should carry:

```
SURFACE A — the 18 executable [[cascade.chain]] descriptors, 20 declared chain variants:
   srmech_chain_spec_parse ACCEPT ... 11 / 20
   srmech_chain_run        ACCEPT ...  0 / 20
```

(Reproduces round 1 exactly — 11 parse-accept, 0 run-accept.)

**Recommended for the rcN**, in dependency order:

1. Add `c_runnable` (and ideally `c_parse_accepted`) to `describe()["cascade_catalog"]`, derived from
   the shipped `_chain_c_eligible` gate rather than from a table — so it moves when the dispatch
   table widens, with no prose edit.
2. Correct README:16 keyed to that field, in the §3 shape, **naming the surface**.
3. Fix the three stale-17 sites via the §4 regen path, in one commit with the rebuild.
4. Add the down-only ratchet `R18` now promises, so the enumeration claim becomes true.
5. Only then edit the issue text itself — round 1 already showed the issue's own "11 of 18 chains
   rejected" figure does not reproduce (the measured split is 11 **accepted** / 7 rejected on parse,
   20 of 20 declined on run).

A caution carried forward from round 1: **do not make a bare-C counter a strict-equality CI gate.**
The `B_attested_parity_ok` counter was observed once at 2 instead of 7 in 36 runs, unexplained and
non-reproducing. A strict-equality ratchet on that counter would have failed on its first run.

---

## 6. Honest scope

**MEASURED in this session** — every verdict in §1 (24 anchors located live, 0 missing); the live
ToolEntry `[17, 17]` vs live `18`; the three stale-17 sites and the compiled C one; the Surface-A
`11/20` parse and `0/20` run; the absent `describe()` fields; `pyproject.toml` packaging the README;
the CLI having no Surface-A run route.

**INHERITED from round 1 and not re-run here** — the bare-C host's Surface-B `7/7/7`, the 16.4 MB
arena / MCU sizing, and the one-off `B_attested_parity_ok = 2` anomaly.

**NOT attempted** — no shipped file was edited (this session is read-only outside `notes/`); the
corrected sentences are drafts, not applied diffs; and `describe()["cascade_catalog"]["c_runnable"]`
is a *recommendation* — no prototype of that field was built, so its derivation from
`_chain_c_eligible` is reasoned from the shipped gate, not measured.

**Where this is weaker than it looks** — PASS 2's open sweep finds 390 claim-shaped lines across 89
files and only 24 are on the anchored roster. The remaining 377 are dominated by *per-op scoped*
statements ("a bare-C host reaches THIS op"), which are individually correct and out of #1653's
scope, but **I did not verify all 377 individually.** The roster covers every statement that makes a
*global* co-equality or capability-set claim; a scoped per-op over-claim could still be hiding in the
tail. PASS 2 exists so the next pass starts from the list rather than from a grep.

One vocabulary note the sweep surfaced, worth carrying: **"cascade" is overloaded in the tree.**
`c/include/srmech.h:3834`, `srmech_explog.c:9`, `srmech_kuramoto.c:21` and `srmech_sqrt.c:9` all say
"runs the cascade" meaning *the transcendental series cascade instead of libm* — a completely
different sense from "runs a declared chain". Any corrected sentence should name the grammar
(`[[cascade.chain]]` / `[[stage]]`) rather than the bare word.

---

## 7. Artifacts

| path | contents |
|---|---|
| `docs/srmech/notes/_1653_readme_truth_audit.py` | the runnable 4-pass audit (anchored roster / open sweep / live values + Surface-A measurement / literal-rot scan) |
| `docs/srmech/notes/_1653_readme_truth_audit.ndjson` | 36 records — one per claim, plus tallies, live values, per-variant Surface-A verdicts, and the remediation path |
| `docs/srmech/notes/_1653_readme_truth_audit.md` | this report |
