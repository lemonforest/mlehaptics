#!/usr/bin/env python3
"""gh #1653 definition-of-done item 8 — the README / introspect TRUTH AUDIT,
as a runnable check rather than a snapshot.

WHY THIS IS A SCRIPT AND NOT A TABLE
------------------------------------
The issue's own requirement is that the prose "become true, and be keyed to
live values rather than literals". A markdown table of verdicts is itself a
literal: it rots exactly the way `#T992` rotted. So the audit ships as three
cooperating passes:

  PASS 1  ANCHORED CLAIMS. A fixed roster of the statements that assert
          co-equal projections / "a host with no Python can drive the same
          capability set". Each is located by a REGEX, not a line number, so
          the audit survives line drift and reports the CURRENT line.
          A vanished anchor is a finding (edited or deleted), not a crash.

  PASS 2  OPEN SWEEP. The same claim-shaped regexes run over the whole
          shipped tree, and any hit NOT already on the anchored roster is
          reported as UNAUDITED. This is what stops a future rc from adding
          a fresh over-claim that the audit silently ignores.

  PASS 3  LIVE VALUES. Every number a corrected sentence wants, read from the
          live package: describe()["cascade_catalog"], describe()["tools"],
          native_status(), describe()["c_claims"]. Then the audit MEASURES
          the Surface-A C parse/run acceptance over the shipped descriptors
          — because that is the number the README's line 16 is really making
          a claim about, and `describe()` currently has NO field carrying it.
          The absence of that field is reported as a hard GAP.

SURFACES (round-1 measurement, gh #1653 — do not conflate them)
---------------------------------------------------------------
  SURFACE A  ``[[cascade.chain.steps]]``  — srmech/cascade/compose.py,
             C peers srmech_compose.c + srmech_compose_run.c.
             ALL 21 shipped cascade_catalog descriptors use this grammar.
  SURFACE B  ``[[stage]]`` / ``[[catalog.operator_chain]]`` — srmech/dsl,
             C peer srmech_dsl_chain_run.c.

A claim can be TRUE of surface B and FALSE of surface A. That is exactly how
this stayed invisible, so every verdict this script prints names its surface.

Run:
    cd docs/srmech/python && python3 ../notes/_1653_readme_truth_audit.py

Exit 0 always (this is a research audit, not a CI gate); the NDJSON beside it
carries every record. No numpy, no RNG, no stdlib fractions, no ALU-magnitude
idiom — exact integers only.
"""
from __future__ import annotations

import ctypes
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRMECH_ROOT = os.path.abspath(os.path.join(HERE, ".."))       # docs/srmech
PY_ROOT = os.path.join(SRMECH_ROOT, "python")
OUT = os.path.join(HERE, "_1653_readme_truth_audit.ndjson")

if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

import srmech                                        # noqa: E402
from srmech import _native                           # noqa: E402
from srmech.cascade import compose as _compose        # noqa: E402
from srmech.cascade import catalogs as _cat_pkg       # noqa: E402  (namespace)
from srmech.dsl import _cascade_chain as _cc          # noqa: E402

RECS = []


def rec(**kw):
    RECS.append(kw)
    return kw


def hr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# ══════════════════════════════════════════════════════════════════════════
# PASS 1 — the ANCHORED claim roster.
#
# Each entry:
#   id        stable audit id (cite this, never a line number)
#   path      repo-relative, from docs/srmech/
#   pattern   regex that locates the claim's own line
#   verdict   TRUE | FALSE | MISLEADING   (against round-1 measurement)
#   surface   which grammar the claim is being graded against
#   wheel     does this text SHIP INSIDE THE WHEEL / the compiled binary?
#   why       the measured reason for the verdict
#   fix       the corrected sentence, keyed to a LIVE READ where a number appears
# ══════════════════════════════════════════════════════════════════════════

CLAIMS = [
    # ---------------------------------------------------------------- README
    dict(
        id="R16-A-capability-set",
        path="python/README.md",
        pattern=r"\*\*Two implementations, one capability set\.\*\*",
        verdict="MISLEADING",
        surface="both",
        wheel=True,           # python/README.md is the PyPI long_description
        why=("The headline is a capability-EQUALITY claim with no scope. "
             "Measured: on SURFACE A (the 21 shipped cascade_catalog "
             "descriptors) the C run peer declines 20 of 20 declared chain "
             "variants, so the two implementations do NOT span one capability "
             "set on that surface. True as a DISCIPLINE statement (ADR-0009), "
             "false as a coverage statement — and the sentence does not say "
             "which it is."),
        fix=("Two implementations, one capability set — as the governing "
             "DISCIPLINE (ADR-0009), not as a claim of achieved coverage. "
             "Where coverage is short it is enumerated, never asserted away: "
             "see the live `srmech.describe()[\"cascade_catalog\"]` "
             "C-reachability read and the down-only ratchets below."),
    ),
    dict(
        id="R16-B-no-python-run-cascades",
        path="python/README.md",
        pattern=(r"so a host with \*\*no Python present\*\* can serve tools, "
                 r"run cascades, and speak the bus"),
        verdict="FALSE",
        surface="A (false) / B (true)",
        wheel=True,
        why=("'run cascades' is FALSE for SURFACE A and TRUE for SURFACE B. "
             "Measured at rc444 in one bare-C binary with no libpython: "
             "SURFACE B `[[catalog.operator_chain]]` parse 7/7, run 7/7, "
             "attested parity 7/7; SURFACE A `[[cascade.chain]]` spec-parse "
             "11 ok / 9 rej, RUN 0 ok / 20 rej. The unqualified plural "
             "'cascades' reads as the config-driven cascade catalog, which is "
             "exactly the population C cannot run."),
        fix=("so a host with **no Python present** can serve tools, run the "
             "`[[catalog.operator_chain]]` / `[[stage]]` chain grammars, and "
             "speak the bus. The `[[cascade.chain]]` grammar of the packaged "
             "cascade catalog is **not yet C-runnable** — the live count is "
             "`srmech.describe()[\"cascade_catalog\"][\"c_runnable\"]` of "
             "`[\"executable\"]`, and it is pinned down-only (#1653)."),
    ),
    dict(
        id="R16-C-663-registry",
        path="python/README.md",
        pattern=r"in-C tool dispatch over the (\d+)-entry tool registry",
        verdict="TRUE-BUT-LITERAL",
        surface="n/a (registry size)",
        wheel=True,
        why=("The literal currently AGREES with the live read, so the "
             "statement is true today. It is still a hard-coded count in "
             "prose — the #T992 rot shape. It must be keyed to the live "
             "value, and the audit compares them every run."),
        fix=("in-C tool dispatch over the tool registry "
             "(`srmech.describe()[\"tools\"][\"total\"]` entries, "
             "`[\"mcp_callable\"]` of them MCP-callable)"),
        live=("tools_total",),
    ),
    dict(
        id="R16-D-neither-is-reference",
        path="python/README.md",
        pattern=r"related by projection rather than by rank — neither is the reference",
        verdict="TRUE",
        surface="both",
        wheel=True,
        why=("A statement about GOVERNANCE, not coverage, and ADR-0009 §1 "
             "backs it verbatim. Round-1 found no counter-instance: where C "
             "declines, Python runs and the decline is a typed status, never "
             "a silent wrong answer. Leave as-is."),
        fix=None,
    ),
    dict(
        id="R16-E-parity-byte-identical",
        path="python/README.md",
        pattern=r"parity means \*byte-identical results\*, not similar behaviour",
        verdict="TRUE",
        surface="both",
        wheel=True,
        why=("Definitional, and the definition is upheld where both paths "
             "run: round-1's bare-C SURFACE B run returned the exact rational "
             "53000000000000137/2062800000000000137 matching its own attested "
             "row. Leave as-is."),
        fix=None,
    ),
    dict(
        id="R18-coverage-enumerated",
        path="python/README.md",
        pattern=r"Coverage is \*\*not\*\* yet complete, and the gap is enumerated rather than asserted away",
        verdict="MISLEADING",
        surface="A",
        wheel=True,
        why=("The disclaimer is honest and load-bearing, but the section it "
             "points at (`C-host coverage`) enumerates only the genome "
             "WIRE-GLUE surface. The Surface-A cascade-chain gap measured by "
             "#1653 is enumerated NOWHERE, so at the moment this sentence "
             "over-promises the enumeration, not the coverage."),
        fix=("Coverage is **not** yet complete, and each gap is enumerated "
             "rather than asserted away — the genome wire-glue surface under "
             "[C-host coverage], and the `[[cascade.chain]]` C-run gap under "
             "its own down-only ratchet (#1653), read live from "
             "`srmech.describe()[\"cascade_catalog\"]`."),
    ),
    dict(
        id="R575-adr-framing",
        path="python/README.md",
        pattern=(r"ADR-0003 commits srmech to running standalone on a C host "
                 r"with no Python present; ADR-0009 frames"),
        verdict="TRUE",
        surface="both",
        wheel=True,
        why=("This is the model paragraph — it states the commitment and "
             "immediately says 'Neither is a claim that coverage is currently "
             "complete.' Round-1 found nothing to correct. The fix for the "
             "other statements is to make them read like this one."),
        fix=None,
    ),
    dict(
        id="R579-ratchet-zero",
        path="python/README.md",
        pattern=r"As of v0\.9\.0rc334 that count is \*\*0\*\*",
        verdict="TRUE-BUT-LITERAL",
        surface="wire-glue (neither A nor B)",
        wheel=True,
        why=("Scoped correctly and explicitly ('a scoped claim, not a blanket "
             "one'), so not misleading. But the 0 and the rc are literals in "
             "prose whose SSoT is `CEIL_WIRE_GLUE_GAPS` in the test suite. "
             "Same rot shape as the 663."),
        fix=("As of this release that count is "
             "`len(CEIL_WIRE_GLUE_GAPS)` — the enumerated genome wire-glue "
             "gap list, asserted down-only by "
             "`tests/test_rosetta_transitive_standalone.py`. Quote the "
             "ratchet, not a transcribed integer."),
    ),
    dict(
        id="R60-c-only-host-q61",
        path="python/README.md",
        pattern=(r"A \*\*C-only host\*\* reassembles the same exact rational "
                 r"from the peers"),
        verdict="TRUE",
        surface="n/a (leaf scalar ops)",
        wheel=True,
        why=("Verified in round 1's bare-C binary: the five "
             "`*_series_truncate` chains produced correct exact values with "
             "no libpython and no libm linked. The claim is about LEAF scalar "
             "peers plus exported model constants, and it holds."),
        fix=None,
    ),

    # -------------------------------------------------- docs/srmech/CLAUDE.md
    dict(
        id="CM-full-c-parity-no-exceptions",
        path="CLAUDE.md",
        pattern=r"full C parity for every\s*\n?primitive class, no exceptions",
        verdict="TRUE",
        surface="primitive classes (not the chain grammars)",
        wheel=False,
        why=("Scoped to the 14 PRIMITIVE CLASSES, and round-1 confirmed the "
             "primitives are there: in the same bare-C process that declined "
             "the `cyclic_gcd` CHAIN, `srmech_gcd(12,18)` and "
             "`srmech_cascade_cyclic_gcd_u64(12,18)` both returned 6 / "
             "SRMECH_OK. The gap is the chain DISPATCH TABLE, not the class."),
        fix=None,
    ),
    dict(
        id="CM-136-coequal-pure-python",
        path="CLAUDE.md",
        pattern=r"default-on at ≥4 cores; value-preserving; pure-Python \(co-equal",
        verdict="TRUE",
        surface="klein4 sector dispatch",
        wheel=False,
        why=("Reads 'pure-Python (co-equal parity — no C-callback; "
             "standalone-C sector dispatch is the tracked follow-up)'. It "
             "declares the C side ABSENT and files it. This is the honest "
             "shape the README statements need."),
        fix=None,
    ),
    dict(
        id="CM-464-toml-no-python",
        path="CLAUDE.md",
        pattern=r"manifests and TOML descriptors with no Python present",
        verdict="TRUE",
        surface="TOML/JSON parsing",
        wheel=False,
        why=("Measured true in round 1 — the bare-C host read the shipped "
             "descriptors through srmech_toml with no libpython. Note this is "
             "the READ, and it is precisely the reason the Surface-A gap is a "
             "DISPATCH-TABLE gap and not a parsing gap."),
        fix=None,
    ),

    # ----------------------------------------------- ships inside the wheel
    dict(
        id="W-catalog1341-barec-lists-runs",
        path="python/srmech/amsc/catalog.py",
        pattern=(r"A bare-C host lists / runs a\s*\n?#\s*catalog's declared "
                 r"chains with these peers"),
        verdict="TRUE",
        surface="B",
        wheel=True,
        why=("SURFACE B only, and the comment names its own peers "
             "(`srmech_catalog_list_chains` / `srmech_catalog_run_chain`) so "
             "the scope is explicit. Round-1 bare-C: parse 7/7, run 7/7. "
             "TRUE — and it is the sentence the README's unqualified 'run "
             "cascades' is over-generalising from."),
        fix=None,
    ),
    dict(
        id="W-catalog1311-descriptor-read",
        path="python/srmech/amsc/catalog.py",
        pattern=r"The descriptor discovery \+ FS read stay host-side \(a bare-C host reads",
        verdict="TRUE",
        surface="B",
        wheel=True,
        why=("Confirmed by the bare-C host, which did exactly this. The "
             "docstring correctly separates the host-side READ from the "
             "PARSE/RUN dispatch."),
        fix=None,
    ),
    dict(
        id="W-tomlchain74-c-only-front-end",
        path="python/srmech/dsl/_toml_chain.py",
        pattern=r"C-only-host chain-spec TOML->canonical-JSON front-end",
        verdict="TRUE",
        surface="B",
        wheel=True,
        why=("Surface B's front end; round-1 exercised it via "
             "`c_toml_chain_to_json`. Scoped and correct."),
        fix=None,
    ),
    dict(
        id="W-catalog89-registry-kernel",
        path="python/srmech/amsc/catalog.py",
        pattern=r"a bare-C host runs the catalog registry/kernel/",
        verdict="TRUE",
        surface="B / registry",
        wheel=True,
        why=("Registry + kernel surface, not the `[[cascade.chain]]` "
             "grammar. No counter-measurement in round 1."),
        fix=None,
    ),
    dict(
        id="W-mcp321-coequal-literal",
        path="c/src/srmech_mcp.c",
        pattern=r"capability the invariant and the two projections co-equal",
        verdict="TRUE",
        surface="MCP tool registry",
        wheel=True,           # compiled INTO libsrmech
        why=("A comment on the in-C tool-count literal, guarding it with a "
             "pin. It asserts the DISCIPLINE and then points at the pinning "
             "test — the correct shape. NOTE: this text is compiled into "
             "libsrmech, so any edit needs a rebuild, not just a text change."),
        fix=None,
    ),
    dict(
        id="W-header342-stale-lib",
        path="c/include/srmech.h",
        pattern=r"projections are co-equal\. Rejecting the stale lib is the only safe read",
        verdict="TRUE",
        surface="ABI",
        wheel=True,
        why=("An ABI-safety argument that FOLLOWS FROM co-equality rather "
             "than asserting coverage. Correct as written."),
        fix=None,
    ),
    # ---- ToolEntry prose: reaches users through describe() + the MCP list --
    dict(
        id="TD-run-cascade-chain-17-explanation",
        path="python/srmech/introspect/_tool_docs_curated.py",
        # The prose is a Python implicit-concatenation of adjacent string
        # literals, so the count and the word "executable" are separated by
        # `" \n 'executable ...`. The anchor has to cross that seam.
        pattern=(r"counts the catalog \((\d+)[\s\"'\n]*executable"
                 r"[\s\"'\n]*/[\s\"'\n]*(\d+)[\s\"'\n]*leaf\)"),
        verdict="FALSE",
        surface="A",
        wheel=True,
        why=("A HARD-CODED COUNT THAT HAS ALREADY ROTTED — this is the #T992 "
             "failure the issue names, live in the tree. The prose says '17 "
             "executable / 3 leaf'; the live read "
             "`describe()['cascade_catalog']` says 18 executable / 3 leaf "
             "(`klein4_from_one` arrived at rc438 and the prose did not "
             "follow). It ships in the wheel and surfaces as the "
             "`srmech.dsl.run_cascade_chain` ToolEntry `explanation`, so every "
             "MCP consumer reads a wrong count. NOTE the irony: the sentence's "
             "whole point is to send the reader to the LIVE read, and then it "
             "transcribes the number anyway."),
        fix=("``describe()['cascade_catalog']`` counts the catalog (its "
             "``executable`` / ``leaf`` split), ``srmech.dsl.list_catalog_ops`` "
             "carries per-descriptor ``status``, and this runs the declared "
             "chain. — i.e. NAME the live keys and stop transcribing their "
             "values. Edit `_tool_docs_curated.py` (the hand-edit source), "
             "then REGENERATE `_tool_docs.py` via tools/regen_all.py; editing "
             "the generated file alone is destroyed by the next generator run."),
    ),
    dict(
        id="TD-run-cascade-chain-17-example",
        path="python/srmech/introspect/_tool_docs_curated.py",
        pattern=(r"'cyclic_gcd' — any of the (\d+)[\s\"'\n]*executable"
                 r"[\s\"'\n]*descriptors"),
        verdict="FALSE",
        surface="A",
        wheel=True,
        why=("The SECOND site of the same rotted count, in the ToolEntry's "
             "`example.input.op_name` field rather than its prose — so a fix "
             "to the explanation alone leaves the wrong number shipping. Live "
             "value is 18. Both sites exist in BOTH `_tool_docs_curated.py` "
             "(hand-edit source) and `_tool_docs.py` (generated), i.e. 4 "
             "occurrences to correct."),
        fix=("'cyclic_gcd' — any descriptor whose "
             "``describe()['cascade_catalog']['status']`` is ``executable``. "
             "A worked example must not restate a catalog size at all; the "
             "example probe (tools/gen_curated_probe.py) can emit the live "
             "count if a number is genuinely wanted."),
    ),
    dict(
        id="CREG-run-cascade-chain-17-compiled",
        path="c/src/srmech_tool_registry.c",
        pattern=r"any of the 17 executable descriptors",
        verdict="FALSE",
        surface="A",
        wheel=True,           # COMPILED INTO libsrmech
        why=("THE THIRD PROJECTION OF THE SAME WRONG NUMBER, and the one that "
             "makes this a registry problem rather than a docs problem: the "
             "stale '17 executable' is baked into `srmech_tool_registry.c`, a "
             "GENERATED const C data table compiled into libsrmech. So the "
             "**bare-C MCP server** hands the wrong count to its clients with "
             "no Python involved. `describe()` and the C registry are supposed "
             "to be co-equal projections of one tool schema (ADR-0009) — and "
             "here they are faithfully co-equal in being wrong together."),
        fix=("Regenerated, never hand-edited. The file's own header says 'DO "
             "NOT EDIT BY HAND. Regenerate with python3 tools/regen_all.py'. "
             "The fix is ONE edit in `_tool_docs_curated.py` + `regen_all.py` "
             "+ a libsrmech rebuild and restage. A text-only correction to the "
             "two Python files leaves the compiled table wrong."),
    ),
    dict(
        id="TD-run-catalog-chain-bounded-MODEL",
        path="python/srmech/introspect/_tool_docs_curated.py",
        pattern=(r"When every step is in the bounded Class-N C dispatch table "
                 r"and the referenced integers fit int64"),
        verdict="TRUE",
        surface="B",
        wheel=True,
        why=("THE MODEL SENTENCE — quote this shape when rewriting README:16. "
             "It states the PRECONDITION ('every step in the bounded Class-N C "
             "dispatch table', 'integers fit int64'), NAMES the symbol "
             "(`srmech_catalog_run_chain`), and states the fallback ('never a "
             "wrong answer, only a slower one'). Round-1's bare-C host "
             "confirmed it: 7/7 parse, 7/7 run, 7/7 attested parity. Every "
             "corrected statement in this audit is this sentence's shape "
             "applied to a different surface."),
        fix=None,
    ),
    dict(
        id="CLI-dsl-run-toml-chain",
        path="python/srmech/cli/main.py",
        pattern=r"run \(execute a TOML chain spec\), ops \(list",
        verdict="TRUE",
        surface="B",
        wheel=True,
        why=("The CLI's run route is the TOML/`[[stage]]` grammar (Surface B) "
             "and its Surface-A touch is `ops`, which only ENUMERATES. So the "
             "CLI half of README:16's 'run cascades' is Surface-B-only as "
             "well — there is no CLI route that runs a `[[cascade.chain]]` "
             "descriptor, in C or otherwise."),
        fix=None,
    ),
    dict(
        id="W-compose-run-bounded-table",
        path="c/src/srmech_compose_run.c",
        # The comment wraps across a C block-comment continuation, so the
        # pattern has to tolerate "\n * " between the words.
        pattern=r"BOUNDED set of\s*\n?\s*\*?\s*shipped-chain ops",
        verdict="TRUE",
        surface="A",
        wheel=True,
        why=("THE most honest statement in the tree about the #1653 gap — the "
             "C run peer says outright that its op set is bounded and "
             "all-Class-N. Round-1 confirmed the table holds 10 entries and "
             "that all 47 ops named by the 18 executable descriptors fall "
             "outside it. Do not weaken this comment; the README should be "
             "corrected TOWARD it."),
        fix=None,
    ),
]

# The claim-shaped regexes for the OPEN SWEEP (pass 2).
SWEEP_PATTERNS = [
    ("coequal", re.compile(r"co-?equal", re.I)),
    ("one_capability_set", re.compile(r"one capability set|same capability", re.I)),
    ("no_python_present", re.compile(r"no Python present|without Python|python-free|"
                                     r"no Python required|C-only host|bare-C host", re.I)),
    ("run_cascades", re.compile(r"run cascades|runs? (the )?cascades?\b", re.I)),
    ("full_parity", re.compile(r"full (C )?parity|complete parity|1:1 C-parity", re.I)),
]

# Only these trees ship to a user (wheel payload + compiled binary + the
# PyPI long_description). A hit outside them is documentation, not a shipped
# claim, and the sweep says which.
WHEEL_PREFIXES = ("python/srmech/", "c/src/", "c/include/", "python/README.md")

SWEEP_DIRS = [
    ("python/srmech", (".py",)),
    ("c/src", (".c", ".h")),
    ("c/include", (".h",)),
]
SWEEP_FILES = ["python/README.md", "CLAUDE.md", "c/README.md"]

# Directories that are neither shipped nor authored prose.
SWEEP_SKIP = ("__pycache__", ".pytest_cache", "/notes/", "/build/")


def ships_in_wheel(relpath):
    return any(relpath.startswith(p) for p in WHEEL_PREFIXES)


def find_anchor(relpath, pattern):
    """Locate a claim by regex. Returns (line_no, verbatim) or (None, None).

    Matches over the whole file text so a pattern may span a wrapped line;
    the reported line number is the line the match STARTS on (1-indexed).

    ``verbatim`` is the MATCHED SPAN plus a little trailing context, not the
    whole physical line — README.md line 16 is a single ~1.5 KB paragraph
    carrying five separate claims, so returning the line would make all five
    anchors print identically and hide which one is being graded.
    """
    full = os.path.join(SRMECH_ROOT, relpath)
    if not os.path.exists(full):
        return None, None
    with open(full, "r", encoding="utf-8") as fh:
        text = fh.read()
    m = re.search(pattern, text)
    if m is None:
        return None, None
    line_no = text.count("\n", 0, m.start()) + 1
    span = text[m.start():m.end()]
    tail = text[m.end():m.end() + 90]
    tail = tail.split("\n")[0]
    return line_no, (span + tail).replace("\n", " ")


def clip(s, n=150):
    s = s.strip()
    if len(s) <= n:
        return s
    return s[:n - 1] + "…"


# ══════════════════════════════════════════════════════════════════════════
# PASS 3 helpers — the LIVE reads, and the measurement describe() lacks.
# ══════════════════════════════════════════════════════════════════════════

LIB = _native.LIB


def c_spec_parse(chain_dict):
    """srmech_chain_spec_parse — arena exactly as compose.py's own caller."""
    payload = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(LIB.srmech_chain_spec_parse_arena_bytes(len(payload)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = 2 * len(payload) + 8192
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = LIB.srmech_chain_spec_parse(
        payload, len(payload), ws, ws_bytes, out, out_cap,
        ctypes.byref(out_len))
    return int(rc)


def c_chain_run(chain_dict, ctx):
    """srmech_chain_run — arena exactly as compose.py's own caller."""
    chain_json = json.dumps(chain_dict, ensure_ascii=False).encode("utf-8")
    ctx_json = json.dumps(ctx, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(LIB.srmech_chain_run_arena_bytes(
        len(chain_json), len(ctx_json)))
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = max(ws_bytes // 2, 16384)
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    rc = LIB.srmech_chain_run(
        chain_json, len(chain_json), ctx_json, len(ctx_json),
        ws, ws_bytes, out, out_cap, ctypes.byref(out_len))
    return int(rc)


def main():
    # ── environment ───────────────────────────────────────────────────────
    ns = srmech.native_status()
    d = srmech.describe()
    cat = d["cascade_catalog"]
    tools = d["tools"]
    cclaims = d["c_claims"]

    hr("ENVIRONMENT (live)")
    print("srmech_version .............. %s" % d["srmech_version"])
    print("has_native / dispatching .... %s / %s"
          % (ns["has_native"], ns["dispatching"]))
    print("abi_version / expected ...... %s / %s"
          % (ns["abi_version"], ns["expected_abi"]))
    rec(record="environment", **{k: ns[k] for k in ns},
        srmech_version=d["srmech_version"])

    # ── PASS 1 ────────────────────────────────────────────────────────────
    hr("PASS 1 — ANCHORED CLAIM ROSTER (%d claims)" % len(CLAIMS))
    tally = {"TRUE": 0, "FALSE": 0, "MISLEADING": 0, "TRUE-BUT-LITERAL": 0,
             "ANCHOR_MISSING": 0}
    wheel_bad = []
    for c in CLAIMS:
        line_no, verbatim = find_anchor(c["path"], c["pattern"])
        if line_no is None:
            verdict = "ANCHOR_MISSING"
            tally["ANCHOR_MISSING"] += 1
        else:
            verdict = c["verdict"]
            tally[verdict] = tally.get(verdict, 0) + 1
        in_wheel = ships_in_wheel(c["path"])
        if verdict in ("FALSE", "MISLEADING") and in_wheel:
            wheel_bad.append(c["id"])
        print()
        print("[%-11s] %-28s %s:%s%s"
              % (verdict, c["id"], c["path"],
                 line_no if line_no else "??",
                 "   *** SHIPS IN WHEEL ***" if in_wheel else ""))
        print("    surface : %s" % c["surface"])
        if verbatim:
            print("    verbatim: %s" % clip(verbatim))
        else:
            print("    verbatim: <anchor regex found nothing — edited or "
                  "deleted; re-audit by hand>")
        if verdict not in ("TRUE",):
            print("    why     : %s" % clip(c["why"], 300))
            if c.get("fix"):
                print("    FIX     : %s" % clip(c["fix"], 400))
        rec(record="anchored_claim", id=c["id"], path=c["path"],
            line=line_no, verbatim=verbatim, verdict=verdict,
            surface=c["surface"], ships_in_wheel=in_wheel,
            why=c["why"], fix=c.get("fix"))

    print()
    print("-" * 78)
    print("PASS 1 tally: " + "  ".join("%s=%d" % (k, v)
                                       for k, v in sorted(tally.items())))
    print("FALSE-or-MISLEADING statements that SHIP IN THE WHEEL: %d %s"
          % (len(wheel_bad), wheel_bad if wheel_bad else ""))
    rec(record="pass1_tally", tally=tally, wheel_bad=wheel_bad)

    # ── PASS 2 ────────────────────────────────────────────────────────────
    hr("PASS 2 — OPEN SWEEP for UNAUDITED claim-shaped statements")
    anchored_files = set(c["path"] for c in CLAIMS)
    anchored_lines = set()
    for c in CLAIMS:
        ln, _v = find_anchor(c["path"], c["pattern"])
        if ln is not None:
            anchored_lines.add((c["path"], ln))

    targets = []
    for relroot, exts in SWEEP_DIRS:
        base = os.path.join(SRMECH_ROOT, relroot)
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [dn for dn in dirnames
                           if dn not in ("__pycache__", ".pytest_cache")]
            for fn in filenames:
                if not fn.endswith(exts):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, SRMECH_ROOT)
                if any(sk in "/" + rel for sk in SWEEP_SKIP):
                    continue
                targets.append(rel)
    for rel in SWEEP_FILES:
        if os.path.exists(os.path.join(SRMECH_ROOT, rel)):
            targets.append(rel)

    sweep_hits = {}
    unaudited = []
    for rel in sorted(set(targets)):
        full = os.path.join(SRMECH_ROOT, rel)
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        for i, line in enumerate(lines, start=1):
            kinds = [name for name, pat in SWEEP_PATTERNS if pat.search(line)]
            if not kinds:
                continue
            sweep_hits.setdefault(rel, []).append((i, kinds, line.rstrip()))
            if (rel, i) not in anchored_lines:
                unaudited.append((rel, i, kinds, line.rstrip()))

    total_hits = sum(len(v) for v in sweep_hits.values())
    print("claim-shaped lines found ....... %d across %d files"
          % (total_hits, len(sweep_hits)))
    print("on the anchored roster ......... %d" % len(anchored_lines))
    print("UNAUDITED ...................... %d" % len(unaudited))
    print()
    print("The unaudited hits are dominated by per-op scoped statements "
          "('a bare-C host reaches THIS op'), which are individually correct "
          "and out of #1653's scope. Reported by FILE so a reviewer can see "
          "where claim density lives, with the SHIPPED files called out.")
    print()
    print("%-58s %5s %6s" % ("file", "hits", "wheel?"))
    print("-" * 74)
    for rel in sorted(sweep_hits, key=lambda r: -len(sweep_hits[r]))[:22]:
        print("%-58s %5d %6s"
              % (clip(rel, 58), len(sweep_hits[rel]),
                 "YES" if ships_in_wheel(rel) else "no"))
    rec(record="pass2_sweep", total_hits=total_hits,
        files=len(sweep_hits), unaudited=len(unaudited),
        by_file=dict((k, len(v)) for k, v in sweep_hits.items()))

    # The narrow, high-risk sweep: the exact phrase README:16 uses.
    print()
    print("NARROW SWEEP — the 'run cascades' phrasing specifically:")
    narrow = [(rel, i, ln) for rel, hits in sweep_hits.items()
              for (i, kinds, ln) in hits if "run_cascades" in kinds]
    if not narrow:
        print("    (none — the phrase was corrected or removed)")
    for rel, i, ln in sorted(narrow):
        print("    %s:%d  %s%s" % (rel, i, clip(ln, 96),
                                   "   [WHEEL]" if ships_in_wheel(rel) else ""))
    rec(record="pass2_narrow_run_cascades",
        hits=[dict(path=r, line=i, text=ln) for r, i, ln in sorted(narrow)])

    # ── PASS 3 ────────────────────────────────────────────────────────────
    hr("PASS 3 — LIVE VALUES the corrected sentences must key to")
    print("describe()[\"cascade_catalog\"][\"total\"] ......... %d" % cat["total"])
    print("describe()[\"cascade_catalog\"][\"executable\"] .... %d" % cat["executable"])
    print("describe()[\"cascade_catalog\"][\"leaf\"] .......... %d" % cat["leaf"])
    print("describe()[\"tools\"][\"total\"] .................. %d" % tools["total"])
    print("describe()[\"tools\"][\"mcp_callable\"] ........... %d" % tools["mcp_callable"])
    print("describe()[\"c_claims\"][\"checked_ops\"] ......... %d" % cclaims["checked_ops"])
    print("describe()[\"c_claims\"][\"checked_symbols\"] ..... %d" % cclaims["checked_symbols"])
    print("describe()[\"c_claims\"][\"consistent\"] .......... %s" % cclaims["consistent"])
    rec(record="live_values", cascade_catalog=cat, tools=tools,
        c_claims=cclaims)

    # The 663 literal, checked against the live read.
    ln, verbatim = find_anchor("python/README.md",
                               r"in-C tool dispatch over the (\d+)-entry tool registry")
    lit = None
    if verbatim:
        m = re.search(r"the (\d+)-entry tool registry", verbatim)
        if m:
            lit = int(m.group(1))
    print()
    print("README literal tool-registry count ... %s" % lit)
    print("live describe()[tools][total] ........ %d" % tools["total"])
    agree = (lit == tools["total"])
    print("AGREE ................................ %s%s"
          % (agree, "" if agree else "   <== the #T992 rot, now live"))
    rec(record="literal_vs_live", which="tool_registry_count",
        literal=lit, live=tools["total"], agree=agree)

    # The SAME check on the ToolEntry prose — read from the LIVE ToolEntry, so
    # this is what an MCP consumer actually receives, not what a file says.
    from srmech.introspect.tool_schema import get_tool_schema
    entry = None
    for t in get_tool_schema().tools:
        if t.name == "srmech.dsl.run_cascade_chain":
            entry = t
            break
    tool_lits = []
    if entry is not None:
        blob = str(getattr(entry, "explanation", "")) + " " + str(
            getattr(entry, "example", ""))
        for m in re.finditer(r"(\d+) executable", blob):
            tool_lits.append(int(m.group(1)))
    print()
    print("LIVE ToolEntry `srmech.dsl.run_cascade_chain` — the surface an MCP")
    print("consumer actually reads:")
    print("  transcribed 'N executable' literals ... %s" % (tool_lits or "-"))
    print("  live cascade_catalog.executable ....... %d" % cat["executable"])
    bad = [n for n in tool_lits if n != cat["executable"]]
    print("  WRONG literals shipping to users ...... %s%s"
          % (bad or "none",
             "   <== FALSE prose in the wheel" if bad else ""))
    rec(record="literal_vs_live", which="tool_entry_executable_count",
        literals=tool_lits, live=cat["executable"], wrong=bad,
        surface_reached="describe() + MCP tools/list",
        fix_path=("edit python/srmech/introspect/_tool_docs_curated.py then "
                  "regenerate _tool_docs.py (tools/regen_all.py)"))

    # ── PASS 3b — the read describe() does NOT have ───────────────────────
    hr("PASS 3b — MEASURING what describe() cannot tell you (the GAP)")
    print("`describe()[\"cascade_catalog\"]` keys: %s"
          % sorted(cat.keys()))
    missing = [k for k in ("c_runnable", "c_parse_accepted", "c_run_accepted")
               if k not in cat]
    print()
    print("MISSING live-read fields ..... %s" % missing)
    print()
    print("This is the hard blocker on the issue's own requirement. README:16")
    print("claims a no-Python host 'can run cascades'; there is NO live value")
    print("in the package that a corrected sentence could be keyed to. The rcN")
    print("must ADD one (a `c_runnable` count on describe()['cascade_catalog'])")
    print("or the correction is just a different literal.")
    rec(record="describe_gap", cascade_catalog_keys=sorted(cat.keys()),
        missing_fields=missing,
        consequence=("no live read exists for Surface-A C-runnability; the "
                     "rcN must add describe()['cascade_catalog']['c_runnable'] "
                     "before README:16 can be keyed to a live value"))

    # Measure it here, so the audit supplies the number until the field exists.
    print()
    print("Measuring it directly instead (the number the field should carry):")
    executable = sorted(n for n, s in cat["status"].items()
                        if s == "executable")
    n_variants = 0
    parse_ok = 0
    run_ok = 0
    per_desc = []
    for name in executable:
        try:
            specs = _cc.cascade_chain_specs(name)
        except Exception as exc:                      # noqa: BLE001
            per_desc.append(dict(name=name, error="%s: %s"
                                 % (type(exc).__name__, exc)))
            continue
        entries = []
        for item in specs:
            # (variant, spec, entry) per the shipped helper's contract.
            entries.append(item)
        for variant, _spec, entry in entries:
            n_variants += 1
            cd = {"name": "%s.%s" % (name, variant),
                  "summary": str(entry.get("summary", "")),
                  "returns": str(entry.get("returns", "")),
                  "on_error": "raise",
                  "steps": entry.get("steps", [])}
            prc = c_spec_parse(cd)
            rrc = c_chain_run(cd, {"row": None, "inputs": {}})
            if prc == 0:
                parse_ok += 1
            if rrc == 0:
                run_ok += 1
            per_desc.append(dict(name=name, variant=variant,
                                 c_parse_rc=prc, c_run_rc=rrc))
    print()
    print("  SURFACE A — the %d executable `[[cascade.chain]]` descriptors,"
          % len(executable))
    print("  %d declared chain variants:" % n_variants)
    print("     srmech_chain_spec_parse ACCEPT ... %d / %d"
          % (parse_ok, n_variants))
    print("     srmech_chain_run        ACCEPT ... %d / %d"
          % (run_ok, n_variants))
    print()
    print("  So the honest corrected README number is: a no-Python host runs")
    print("  %d of %d declared `[[cascade.chain]]` variants." % (run_ok, n_variants))
    rec(record="surface_a_measured", executable=len(executable),
        variants=n_variants, c_parse_accept=parse_ok, c_run_accept=run_ok,
        per_variant=per_desc)

    # ── PASS 4 — generic LITERAL-ROT scan ─────────────────────────────────
    # The issue's requirement is about literals in general, not only the two
    # the anchored roster caught. Any transcribed count of a quantity that has
    # a live read is a rot candidate; this pass finds them and grades the ones
    # whose live value is known.
    hr("PASS 4 — LITERAL-ROT scan (transcribed counts of live quantities)")
    ROT = [
        ("cascade_catalog.executable",
         re.compile(r"(\d+)\s*[\"'\n\s]*executable\s*[\"'\n\s]*/"
                    r"\s*[\"'\n\s]*(\d+)\s*[\"'\n\s]*leaf"),
         cat["executable"], 1),
        ("tools.total (N-entry registry)",
         re.compile(r"the (\d+)-entry tool registry"), tools["total"], 1),
        ("tools.total (describe() stays N)",
         re.compile(r"describe\(\) (?:total )?stays (\d+)"),
         tools["total"], 1),
        ("tools.total (tools.total stays N)",
         re.compile(r"tools\.total\s+stays\s+(\d+)"), tools["total"], 1),
        ("native abi_version",
         re.compile(r"ABI\s+stays\s+(\d+)\b"), ns["abi_version"], 1),
    ]
    rot_rows = []
    for rel in sorted(set(targets)):
        full = os.path.join(SRMECH_ROOT, rel)
        try:
            with open(full, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        for label, pat, live, grp in ROT:
            for m in pat.finditer(text):
                got = int(m.group(grp))
                line_no = text.count("\n", 0, m.start()) + 1
                rot_rows.append(dict(path=rel, line=line_no, quantity=label,
                                     literal=got, live=live,
                                     agree=(got == live),
                                     wheel=ships_in_wheel(rel)))
    # The 'ABI stays N' family is a HISTORICAL rc-log idiom ("at rc14, ABI
    # stays 3"). A past-tense record of a past value is provenance, NOT rot,
    # and it must keep its literal. Only PRESENT-TENSE claims about the
    # current surface are required to be live reads, so the two families are
    # tallied apart rather than lumped into one misleading total.
    HISTORICAL = ("native abi_version", "tools.total (describe() stays N)",
                  "tools.total (tools.total stays N)")
    print("%-34s %6s %6s %7s %s" % ("quantity", "found", "agree", "differ",
                                    "reading"))
    print("-" * 78)
    for label, _pat, live, _g in ROT:
        rows = [r for r in rot_rows if r["quantity"] == label]
        diff = [r for r in rows if not r["agree"]]
        kind = ("historical rc-log — KEEP the literal"
                if label in HISTORICAL else "PRESENT-TENSE — must be a live read")
        print("%-34s %6d %6d %7d %s"
              % (label[:34], len(rows), len(rows) - len(diff), len(diff), kind))
    print()
    print("live values used above: cascade_catalog.executable=%d  "
          "tools.total=%d  abi_version=%d"
          % (cat["executable"], tools["total"], ns["abi_version"]))
    rec(record="pass4_literal_rot", found=len(rot_rows),
        historical_families=list(HISTORICAL), rows=rot_rows)

    # The rows that matter for #1653: PRESENT-TENSE, shipped, and wrong.
    fix_list = [r for r in rot_rows
                if r["quantity"] not in HISTORICAL and not r["agree"]]
    print()
    print("PRESENT-TENSE + SHIPPED + WRONG — the #1653 literal fix list: %d"
          % len(fix_list))
    for r in sorted(fix_list, key=lambda x: x["path"]):
        print("    %-52s says %d, live is %d   %s"
              % (clip("%s:%d" % (r["path"], r["line"]), 52),
                 r["literal"], r["live"], "[WHEEL]" if r["wheel"] else ""))
    print()
    print("  All three are the SAME sentence in three projections: the")
    print("  hand-edit source (_tool_docs_curated.py), its generated Python")
    print("  peer (_tool_docs.py), and the GENERATED CONST C TABLE")
    print("  (srmech_tool_registry.c). The C one is compiled into libsrmech,")
    print("  so the bare-C MCP server hands the wrong count to its clients")
    print("  until the library is regenerated AND rebuilt. One edit, one")
    print("  regen (tools/regen_all.py), one rebuild — not three edits.")
    rec(record="pass4_fix_list", rows=fix_list,
        remediation=("edit _tool_docs_curated.py, then tools/regen_all.py to "
                     "refresh _tool_docs.py AND srmech_tool_registry.c, then "
                     "rebuild + restage libsrmech"))

    # ── the wheel-vs-text split, stated plainly ───────────────────────────
    hr("SHIPS-IN-WHEEL SPLIT — which fixes need a rebuild, not an edit")
    txt_only, wheel_py, wheel_c = [], [], []
    for c in CLAIMS:
        if c["verdict"] == "TRUE" or not c.get("fix"):
            continue
        p = c["path"]
        if p.startswith("c/"):
            wheel_c.append(c["id"])
        elif p.startswith("python/srmech/") or p == "python/README.md":
            wheel_py.append(c["id"])
        else:
            txt_only.append(c["id"])
    print("plain text edit only ................ %s" % (txt_only or "-"))
    print("SHIPS IN WHEEL (py / long_desc) ..... %s" % (wheel_py or "-"))
    print("  -> reaches users via PyPI page, describe(), the MCP tool list;")
    print("     needs the regen path (tools/regen_all.py) when the text is a")
    print("     ToolEntry summary or a generated manifest, not a free docstring.")
    print("COMPILED INTO libsrmech (c/) ........ %s" % (wheel_c or "-"))
    print("  -> a text change here is inert until the library is REBUILT and")
    print("     restaged; the in-C tool registry carries its own literals.")
    rec(record="wheel_split", text_only=txt_only, wheel_python=wheel_py,
        wheel_c=wheel_c)

    with open(OUT, "w", encoding="utf-8") as fh:
        for r in RECS:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
    print()
    print("wrote %d records -> %s" % (len(RECS), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
