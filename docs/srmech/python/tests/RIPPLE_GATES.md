# Ripple gates -- the dispatch-surface CI gate set (`#T1063`)

## What this is

When you **register a new public op** or **edit a `ToolEntry`**, the change
*ripples* to a fixed family of CI gates. That list used to live only in a
private memory file, so each build brief hand-transcribed a subset and dropped
gates -- rc385 (`quaternion_log` / `quaternion_slerp`) ate two CI-red rounds on
the worked-example gate family alone. This directory now carries the list **in
the repo**, as one runnable command:

```
python3 tools/ripple_check.py
```

The gate set is the committed manifest **`tools/ripple_gates.txt`** (one pytest
target per line; `#` comments and blank lines ignored). `ripple_check.py` reads
that manifest and runs exactly those gates -- the FAST dispatch-surface subset,
never the full **15.5k**-test suite. *(Measured at v0.9.0rc450 by the runner's own
collect-only sweep: `15500 tests collected in 58.81s`. This line said `~10k` until
rc450 — but so did a first attempt at correcting it, which copied
`tools/ripple_check.py`'s `~14.5k` rather than measuring. That figure is itself an
rc421-era number and is now ~6% low, so `ripple_check.py:49` and `:148` are FILED to
the `#T1159` bucket rather than fixed here. Three files, three different sizes for one
suite, and the only defensible one is the number the run just printed.)* A meta-test,
`tests/test_ripple_manifest_covers_known_gates.py`, guarantees the manifest can
never silently shrink below the known families.

## When to run it

Run it **before pushing any rc that registers/edits an op or a `ToolEntry`** --
i.e. any change that moves `describe()["tools"]["total"]`, the C tool registry,
the carrier / rosetta / MCP surfaces, the worked-example ledger, or the emitted
docstrings. If in doubt, run it: it is fast.

## The two-step story: regen, THEN verify

A dispatch-surface change usually needs the generated tree **regenerated first**,
in this exact order (the second step is easy to forget -- it is *not* a codegen
step and `regen_all.py` does not run it, but the executed-example ledger gate
reds without it):

```
python3 tools/regen_all.py                        # rebuild every generated file + verify idempotence
python3 tools/run_worked_examples.py --only-stale # refresh the executed-example ledger
```

`ripple_check.py --regen` runs both, in order, and then runs the gates -- one
command for the whole "regen, then verify" story:

```
python3 tools/ripple_check.py --regen
```

Other modes: `--regen-only` (preamble only), `--list` (print the resolved
targets), `--manifest PATH` (alternate manifest).

After `--regen`, glance at `git status`: `run_worked_examples.py` *executes*
every snippet, so it refreshes `tests/worked_examples_result.ndjson` and can
leave an incidental scratch artifact from a snippet that writes a file. On a
CRLF (Windows) checkout the executor's LF writes also show as whole-file EOL
churn -- run the preamble on the WSL2 / LF checkout that build agents use, and
those are non-events.

## The gate set

Grouped by family (the manifest is the SSOT; this table is the human-readable
mirror):

| Family | Gate(s) | What a new op ripples to |
|--------|---------|--------------------------|
| C tool registry | `test_tool_registry_c_rc184`, `test_tool_schema_ops_c_rc185`, `test_invoke_tool_c_rc188` | the compiled-in C tool registry + schema + invoke path |
| carrier schema | `test_carrier_schema_rc205` | the carrier-registry generated table |
| rosetta | `test_rosetta_transitive_standalone`, `test_rosetta_completeness` | standalone-C reachability + classification ledger (slowest gate ~30s) |
| c-claims | `test_c_claim_resolution_rc300` | the generated C-claims resolution table |
| MCP | `test_mcpb_emit` (tool list == advertised introspection), `test_mcp_marshal_c_rc187`, `test_mcp_sse_c_rc194`, `test_mcp_stdio_c_rc186` | a new op appears in the MCP surface (bundle + C marshalling over the SSE / stdio transports) |
| MCP coercer + signature drift | `test_mcp.py::test_all_param_types_json_coercible`, `test_mcp.py::test_schema_signature_alignment_no_drift` (by NODE-ID) | the **novel param-type** axis: a new op declaring a param TYPE with no `_PARAM_COERCERS` handler, or declared params drifting from the signature (the rc273 / rc328 failure class). `test_mcpb_emit` does NOT cover coercion and the C-marshalling gates test the wire, not the Python coercer registry -- so these two carry the axis. They run pure (~sub-second, no server / no fixture). The rest of `test_mcp.py` (socket SSE server + subprocess round-trips) stays EXCLUDED -- as a whole file it hangs a fast runner (>90s, no clean exit) |
| regen graph | `test_regen_all_rc346` | the codegen dependency graph + idempotence |
| worked-example family | `test_worked_examples_strict_zero_rc353` (registry-only, strict-zero), `test_worked_examples_execute_rc354` (executed ledger -- needs `run_worked_examples.py --only-stale`) | the two DIFFERENT-regen worked-example gates that bit rc385 |
| count-pin | `test_registry_smoke_rc127`, `test_rc15_describe_resolve` | representative `describe()["tools"]["total"]` pins (the full blast radius is 67 files / 74 lines at rc450 -- see note) |
| class-TOML op-ref | `test_class_catalog_oprefs_resolve_930` | the third generated C table (`srmech_class_registry.c`) op refs |
| ref-notation | `test_ref_notation_emitted_rc348` | bare-`#NNN` autolink guard on emitted artifacts |
| JPL audit | `test_jpl_audit` | C Power-of-Ten ratchet (any C-touching op) |
| version pin | `test_signal_processing_scaffolding` | the single hard version-literal gate |
| non_compute / annex | `test_non_compute_ratchet_rc170`, `test_annex_ratchet_rc177`, `test_annex_ratchet_rc183` | the non_compute / annex classification ratchets |
| self-hosting import ban | `test_selfhosting_import_ban` | the ONE table-driven ban list (`#T1073`): a new op-rc's **new test file** reaching for stdlib `fractions` (#845 / #870) — cost rc386 a full CI-red round because the runner omitted it — **and** a new package module reaching for `numpy` / `math` / `decimal`, or bypassing the `srmech._json` / `srmech._toml` front doors. Absorbed `test_no_stdlib_fractions_import` + `test_no_stdlib_math_import` + `test_numpy_carrier_ratchet` at rc405. Pure-Python, no native `.so` |
| decode-aware population pin | `test_namespace_prefix_decode_aware_rc361` | a new **cascade op** bumps the `srmech.cascade` DECODED-channel population (the ratchet's population half, invisible to a text grep). rc387 had to run it manually (100 → 102). Pure-Python (reads regen'd artifacts + decodes their byte arrays), ~seconds; no native `.so` |
| cascade / chain C-parity (rc450, gh #1653) | `test_c_cascade_parity_ratchet_rc446`, `test_c_cascade_value_parity_rc450`, `test_blocked_row_agrees_with_gate_matrix_rc450`, `test_step_mutation_witness_rc447`, `test_combinator_kernel_closure`, `test_t1146_rejection_parity_rc447`, `test_t1158_refusal_set_equality_rc449`, `test_abi_prose_currency_rc449` (frozen) + 16 more listed | the WHOLE FAMILY was unlisted until rc450. Predicate: the file's source references `srmech_chain_run`, `srmech_dsl_chain_run`, `_compose_lib`, `cascade_chain_specs`, `run_cascade_chain`, `cascade_catalog`, `compose.run_chain` or `dsl_chain` -- 47 files match, 20 were listed, **27 were not**, and the 27 included every gate gh #1653 items 3/4/5 move plus all three gates rc449 itself added. Measured cost of the 24 additions: ~230 s. Kept anyway -- a fast runner that omits the surface under change is fast about nothing |
| emitted ToolEntry prose currency (rc454, gh #1653 item 11) | `test_cascade_catalog_prose_currency_rc454` (frozen) | strict-zero on a cascade-catalog CARDINAL written as a literal in `ToolEntry` prose -- the axis an op rc edits by hand and no gate read at all before rc454. Four layers: the curated SSoT read as a **loaded dict** (Black splits the claim across two source lines, so `grep -c '17 executable'` returns 0 on the file containing it and `git log -S` is defeated the same way), the live registry, every `codegen_manifest.GENERATORS` output in BOTH its text and its embedded byte-array channel, and the compiled `libsrmech` (skip-clean when absent). Shape, not value: `any of the 18 executable descriptors` was TRUE at rc453 and is rejected too, because rc447 bumped one of two literals in that same entry and the sibling then shipped stale for six releases. Carries a seeded detector in all three encodings and a dated-clause carve-out so a Type-A `At v0.9.0rcNNN:` ledger line is never touched. ~13 s, pure-Python apart from the optional native read |

### Note on the count-pin blast radius

A tool-count bump ripples to **67 test files across 74 lines** that assert
`describe()["tools"]["total"] == N`. *(Measured at v0.9.0rc450, predicate
stated: `git grep -c "== 663" -- tests/`, where 663 is the live
`describe()["tools"]["total"]`. The `~55` written here was an rc362-era
figure and had gone ~22% low; `docs/srmech/CLAUDE.md` separately carried
`73 lines across 66 files`, so the tree stated two different numbers for one
quantity and neither was current. Note also that this predicate CANNOT see
three further shapes -- a bare `EXPECTED_N` assignment, derived arithmetic
such as `692 frames (663 ops + 29 carriers)`, and percentage prose such as
`8.7% of 663` -- plus an `"n": 663` field in a data file. A bare-word search
finds 81 files against this predicate's 67, so the invisible class is ~14
files, not the one file the CLAUDE.md note names.)* Running all 55 here would blur into the full
suite, so the manifest carries two cheap `describe()`-based representatives; if
they red on a count change, the fix is to update *all* the count-pins (CI runs
the full suite and will confirm). The point of including them here is early
detection: you learn the count moved before you push.

### Why a standalone runner (not a `pytest -m ripple` marker)

The gate list lives in ONE committed file the runner reads. A marker would
require either editing the ~15 gate test files (churn, and it collides with
concurrently-running rcs editing those same files) or a `conftest`
`pytest_collection_modifyitems` hook (this package ships no pytest config today,
and editing the shared `conftest.py` is exactly the collision risk we want to
avoid). A standalone `tools/ripple_check.py` reading `tools/ripple_gates.txt` is
fully non-invasive: new files only, no edits to any existing gate test.

### ⚠️ This table is a PARTIAL mirror, and says so as of rc450

The manifest holds **101 targets across 98 files**; this table enumerates
roughly a third of them by name. It is a reading aid for the FAMILIES, not a
line-by-line mirror, and it was described as *"the human-readable mirror"* while
carrying no entry at all for the 24-file cascade/chain C-parity family — which
is the family gh #1653 has been moving for six releases. A mirror that is
missing the surface under active change is worse than no mirror, because a
reader checks it and concludes the family is not gated. `tools/ripple_gates.txt`
is the SSOT; when the two disagree, the manifest wins and this file is the bug.
