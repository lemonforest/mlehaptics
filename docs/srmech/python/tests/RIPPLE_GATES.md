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
never the full ~10k-test suite. A meta-test,
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
| MCP | `test_mcpb_emit` (tool list == advertised introspection), `test_mcp_marshal_c_rc187`, `test_mcp_sse_c_rc194`, `test_mcp_stdio_c_rc186` | a new op appears in the MCP surface (bundle + C marshalling over the SSE / stdio transports). NOTE: the heavyweight `test_mcp.py` is deliberately EXCLUDED -- it alone spins a real socket SSE server + subprocess round-trips that hang a fast runner (>90s, no clean exit). The four gates here are all ~10s and server-free (the `_c_` tests exercise C marshalling, not a live server) |
| regen graph | `test_regen_all_rc346` | the codegen dependency graph + idempotence |
| worked-example family | `test_worked_examples_strict_zero_rc353` (registry-only, strict-zero), `test_worked_examples_execute_rc354` (executed ledger -- needs `run_worked_examples.py --only-stale`) | the two DIFFERENT-regen worked-example gates that bit rc385 |
| count-pin | `test_registry_smoke_rc127`, `test_rc15_describe_resolve` | representative `describe()["tools"]["total"]` pins (the full blast radius is ~55 files -- see note) |
| class-TOML op-ref | `test_class_catalog_oprefs_resolve_930` | the third generated C table (`srmech_class_registry.c`) op refs |
| ref-notation | `test_ref_notation_emitted_rc348` | bare-`#NNN` autolink guard on emitted artifacts |
| JPL audit | `test_jpl_audit` | C Power-of-Ten ratchet (any C-touching op) |
| version pin | `test_signal_processing_scaffolding` | the single hard version-literal gate |
| non_compute / annex | `test_non_compute_ratchet_rc170`, `test_annex_ratchet_rc177`, `test_annex_ratchet_rc183` | the non_compute / annex classification ratchets |

### Note on the count-pin blast radius

A tool-count bump ripples to **~55 test files** that assert
`describe()["tools"]["total"] == N`. Running all 55 here would blur into the full
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
