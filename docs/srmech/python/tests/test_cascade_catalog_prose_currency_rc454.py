"""rc454 (`#T1159`, gh #1653 item 11) — a cascade-catalog CARDINAL may not be
written as a literal in emitted ``ToolEntry`` prose.

THE DEFECT, MEASURED
====================
``srmech.dsl.run_cascade_chain``'s ``explanation`` shipped this sentence from
rc438 to rc453, in every wheel:

    ``describe()['cascade_catalog']`` counts the catalog (17 executable / 3
    leaf), ``srmech.dsl.list_catalog_ops`` carries per-descriptor ``status``

Live at rc454: ``executable`` is **18** — ``klein4_from_one`` joined the catalog
at rc438 and the prose did not follow. The clause's own point is to send the
reader to the live read, and it transcribed the value anyway. Adjudicated
**FALSE** by ``notes/_1653_readme_truth_audit.md``
(``TD-run-cascade-chain-17-explanation``), corrected form: *name the live keys
and stop transcribing their values*.

WHY THIS IS A SHAPE GATE AND NOT A VALUE GATE
=============================================
rc447 already hunted this exact literal. Its commit message says *"THE STALE
LITERALS WERE TWO, NOT ONE"* — and it fixed ONE of them. The ``example`` field
of the SAME entry, in the SAME regeneration, got ``17`` -> ``18``; the
``explanation`` field two hundred lines away kept ``17`` and shipped for six
more releases. Bumping a literal re-arms at descriptor 19.

So this gate is **strict-zero on the SHAPE**: no integer literal qualifying a
catalog-partition word may appear in emitted ToolEntry prose at all. A
currently-TRUE cardinal is still a violation — ``any of the 18 executable
descriptors`` was *correct* at rc453 and is banned here, because "correct
today" is precisely the state the stale one was in at rc437.

WHY GREP COULD NOT HAVE FOUND IT (the line-split trap)
======================================================
The curated SSoT is Black-formatted, so the claim spans two source lines::

    "``describe()['cascade_catalog']`` counts the catalog (17 "
    'executable / 3 leaf), ``srmech.dsl.list_catalog_ops`` '

Measured: ``grep -c '17 executable' _tool_docs_curated.py`` returns **0** while
the identical joined string is present in both generated artifacts and in the
compiled library. ``git log -S '17 executable / 3 leaf'`` returns 0 hits too —
git's own pickaxe is defeated by the same split. **This file therefore never
reads the curated module as TEXT.** It imports ``CURATED`` and reads it as a
loaded dict, which is what resolves the implicit concatenation.

THE FOUR LAYERS
===============
Each is a different way for the same sentence to reach a user, and the defect
was live in all four simultaneously:

  **L0 — the curated SSoT.** ``srmech.introspect._tool_docs_curated.CURATED``,
  read as a dict. This is the only hand-edited surface; fixing anywhere else is
  destroyed by the next generator run. Gating here is what makes a fix durable.

  **L1 — the live ToolEntry surface.** ``warmup_all()`` +
  ``get_tool_schema().tools`` — what ``describe()`` and the MCP tool list
  actually serve. ``tool_schema`` imports ``TOOL_DOCS`` from the GENERATED
  ``_tool_docs``, so this layer transitively pins that file's content too.

  **L2 — the checked-in generated artifacts.** Derived by iterating
  ``tools/codegen_manifest.GENERATORS`` rather than naming files, so a seventh
  generator cannot ship unguarded (the rc348 pattern). Two predicates per
  artifact: the raw text, AND ``c_byte_arrays.decoded_blobs`` for the embedded
  decimal byte arrays — rc359 measured a text-only scan reporting a true-but-
  meaningless ``0`` while five bare refs shipped inside the payload.

  **L3 — the compiled library.** The primary compiled-tier guarantee is NOT
  here: ``test_tool_registry_c_rc184.py`` pins the C registry byte-identical to
  the live Python SSoT, so prose the ``.so`` carries that L1 does not is a hash
  mismatch there. This file adds a direct byte scan as belt-and-braces, guarded
  on ``HAS_NATIVE`` and on the file existing, because the library is gitignored
  and absent on pure / numpy-absent / Pyodide cells.

THE ENCODING TRAP
=================
The C registry stores the same prose TWO ways, and a pattern that spans a
non-ASCII character matches one form and misses the other:

  * ``explanation`` is a plain ``const char *`` with octal escapes — its
    em-dash is ``\\342\\200\\224``;
  * ``example`` is JSON encoded INSIDE a C string — its em-dash is ``\\\\u2014``.

Every pattern here is anchored on **ASCII digits and ASCII words only**, which
matches both. The octal channel also cuts the other way: an octal escape ENDS
in digits, so a naive ``(\\d+)\\s+word`` predicate reads ``\\342\\206\\222 chain``
as "222 chain". Measured — that false positive is real in the tree today. The
shared lookbehind excludes it.

THE DATED-CLAUSE CARVE-OUT (load-bearing, not polish)
=====================================================
A naive ``(\\d+) executable`` predicate also matches ``README.md``'s

    At v0.9.0rc447: **21 descriptors — 18 executable, 3 leaf**

and the rc447 ``CHANGELOG.md`` lines. Those are Type-A DATED LEDGER entries:
they date themselves, and keying them live would demand they be BUMPED the
moment the catalog grows — fabricating history, which this tree treats as worse
than the staleness. Without the carve-out this gate is not merely noisy, it is
actively harmful, so :func:`catalog_cardinal_hits` excuses any match on a line
that OPENS with an explicit dated-ledger stamp. The carve-out has its own test;
``test_readme_currency_rc419`` documents its narrative-rc-citation carve-out the
same way.

The carve-out is deliberately TIGHT on two axes, and both are load-bearing:

  1. the stamp must carry a FULL version token (``v0.9.0rc447``), never a bare
     ``rc419``; and
  2. it must open the line.

That is what encodes the project's ruling on the genuinely ambiguous case. The
stale clause contains ``measured as unenumerable through rc419`` MID-SENTENCE.
Read loosely, that rc-reference would "date" the clause and excuse the very
defect this file exists to catch. The audit ruled otherwise — the rc-reference
attaches to the ADR-0012 C6 *unenumerability* measurement, not to the cardinal —
and there is a test below asserting that string is NOT excused.

ANTI-VACUITY
============
A strict-zero over a corpus that has stopped being scanned is a green light for
nothing. Every layer therefore asserts it can still SEE:

  * both prose corpora are non-empty, at a floor well under their measured size;
  * the byte-array decoder still returns blobs (rc348's
    ``test_the_decoder_can_still_see_something``);
  * the generator roster is non-empty and every declared output exists;
  * the SENTENCE ITSELF still exists and still names both live keys, in all
    four artifacts — deleting the clause would otherwise pass strict-zero;
  * the live mapping exposes its partition keys by MEMBERSHIP, never
    ``.get(..., 0)``. ``c_runnable`` in particular has exactly one existence
    guard tree-wide, so a silent default here would make the retro-check
    vacuous the day the key is removed;
  * a SEEDED DETECTOR plants the rc453 prose — in all three encodings, and into
    a copy of the real curated corpus — and asserts the predicate FIRES.

numpy-free (imports only srmech + stdlib + two in-tree test helpers), per the
numpy-absent CI cell.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from srmech import _native
from srmech.introspect import describe
from srmech.introspect._tool_docs_curated import CURATED
from srmech.introspect.tool_schema import get_tool_schema, warmup_all

_HERE = Path(__file__).resolve().parent          # docs/srmech/python/tests
_PKG_ROOT = _HERE.parent                          # docs/srmech/python
_SR_ROOT = _HERE.parents[1]                       # docs/srmech  <- DECLARED reach
_TOOLS = _PKG_ROOT / "tools"

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import codegen_manifest  # noqa: E402  (tools/ on sys.path above)
from c_byte_arrays import decoded_blobs  # noqa: E402  (tests/ on sys.path above)

warmup_all()


# ══════════════════════════════════════════════════════════════════════
# THE PREDICATE
# ══════════════════════════════════════════════════════════════════════

#: What may NOT sit immediately before a cardinal's first digit. Each exclusion
#: is here because of a MEASURED false positive in this tree:
#:
#:   ``-``   ``Klein-4 leaf`` — a hyphenated algebra term, not a count.
#:   ``\``   ``\342\206\222 chain`` — the tail of a C OCTAL ESCAPE. An escape
#:           ends in digits, so an em-dash written before a partition word
#:           mints a phantom cardinal out of thin air.
#:   word    the tail of a longer number or identifier.
#:
#: The second lookbehind is narrower than it looks, and deliberately so. It
#: rejects ``2**8 leaf`` (an exponent) WITHOUT rejecting ``**21 descriptors``
#: (markdown bold around a real cardinal). Excluding a bare ``*`` would do
#: both, and the carve-out test caught exactly that: a bold-wrapped ledger
#: cardinal went silently unseen, which is how a shape gate acquires a blind
#: spot in the one prose style ledger entries are written in.
_NOT_A_CARDINAL_START = r"(?<![-\w\\])(?<!\d\*\*)"

#: The catalog-cardinal shapes. Names, not indices, so a failure says which
#: claim moved. All three measure ZERO across L0/L1/L2/L3 at rc454 head.
CARDINAL_PATTERNS = {
    # "counts the catalog (17 executable / 3 leaf)" and
    # "any of the 18 executable descriptors" — both halves rc447 split.
    "executable": re.compile(_NOT_A_CARDINAL_START + r"(\d+)\s+executable\b"),
    # the other half of the same partition.
    "leaf": re.compile(_NOT_A_CARDINAL_START + r"(\d+)\s+leaf\b"),
    # the TOTAL, in the spelling the README ledger uses.
    "descriptors": re.compile(
        _NOT_A_CARDINAL_START
        + r"(\d+)\s+(?:cascade[- ])?(?:catalog\s+)?descriptors?\b"),
}

#: A DATED LEDGER LINE — a line that opens with an explicit "this was true at
#: version X" stamp. Every match on such a line is excused. Requires a FULL
#: version token: a bare `rc419` mid-sentence must never date a clause (see
#: the carve-out section of the module docstring, and
#: ``test_the_carve_out_does_not_excuse_an_in_sentence_rc_reference``).
DATED_LEDGER_LINE = re.compile(
    r"^[\s>*\-#|]*(?:\*\*)?(?:at|as\s+of|measured\s+at)\s+"
    r"v?\d+\.\d+\.\d+(?:rc\d+)?",
    re.IGNORECASE)

#: rc453's shipped prose, VERBATIM — the seeded detector's payload and the
#: retro-check's subject. The first is the stale half; the second was TRUE and
#: is banned anyway, which is the whole point of a shape gate.
RC453_EXPLANATION_CLAUSE = (
    "``describe()['cascade_catalog']`` counts the catalog (17 executable / 3 "
    "leaf), ``srmech.dsl.list_catalog_ops`` carries per-descriptor ``status``")
RC453_EXAMPLE_CLAUSE = "'cyclic_gcd' — any of the 18 executable descriptors"

#: The stale explanation as the C registry carries a plain ``const char *``:
#: em-dash octal-escaped.
RC453_C_OCTAL_FORM = (
    "\"WHAT \\342\\200\\224 run a cascade-catalog descriptor's DECLARED chain: "
    "``describe()['cascade_catalog']`` counts the catalog (17 executable / 3 "
    "leaf) \\342\\200\\224 done.\"")

#: The example as the C registry carries it: JSON encoded INSIDE a C string,
#: so the em-dash is double-escaped.
RC453_C_JSON_FORM = (
    "\"{\\\"input\\\":{\\\"op_name\\\":\\\"'cyclic_gcd' \\\\u2014 any of the "
    "18 executable descriptors\\\"}}\"")

#: A Type-A dated ledger line, shaped exactly like the one in ``README.md``
#: that this predicate must NEVER touch.
DATED_LEDGER_SAMPLE = (
    "At v0.9.0rc447: **21 descriptors — 18 executable, 3 leaf** "
    "(`chiral_flip`, `pin_slot_at_zero`, `reorient`)")

#: The prose fields of a ToolEntry. The census named ``explanation`` and
#: ``example``; ``summary`` and ``smoke_test_hint`` are the same curated file
#: and the same emitted surface, so they are scanned too. The non-prose fields
#: (``composes`` / ``preserves`` / ``returns`` / ``category``) are covered by
#: L2, which scans the whole emitted artifact rather than a field list.
PROSE_FIELDS = ("summary", "explanation", "example", "smoke_test_hint")


def _strings(obj) -> "list[str]":
    """Every string reachable inside ``obj``, keys included.

    ``example`` is a nested mapping (``input`` / ``output`` / ``why`` /
    ``worked``), and the cardinal lived inside ``input['op_name']`` — a value
    two levels down. Walking the structure is what reaches it. Serialising to
    JSON would work too, but would drag a stdlib codec across the self-hosting
    boundary for no gain.
    """
    out: "list[str]" = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            out.extend(_strings(key))
            out.extend(_strings(value))
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            out.extend(_strings(value))
    return out


def catalog_cardinal_hits(text: str, where: str = "") -> "list[tuple]":
    """Every catalog-cardinal literal in ``text``, minus dated-ledger lines.

    Returns ``(where, line_no, pattern_name, value, context)`` per hit. Scans
    EVERY match of EVERY pattern — never the first only. One ToolEntry held a
    right ``18`` and a wrong ``17`` at the same time, and a first-match gate
    reads that entry as green.
    """
    hits: "list[tuple]" = []
    for line_no, line in enumerate(text.splitlines() or [""], 1):
        if DATED_LEDGER_LINE.match(line):
            continue
        for name, pattern in CARDINAL_PATTERNS.items():
            for match in pattern.finditer(line):
                context = line[max(0, match.start() - 70):match.end() + 30]
                hits.append((where, line_no, name, match.group(1), context))
    return hits


def _scan_prose_mapping(mapping: dict) -> "tuple[list[tuple], int]":
    """Scan ``{entry_name: {field: value}}``. Returns (hits, strings scanned).

    The string count is returned so the caller can assert the corpus has not
    quietly emptied — a strict-zero over nothing is not a measurement.
    """
    hits: "list[tuple]" = []
    scanned = 0
    for name in sorted(mapping):
        fields = mapping[name]
        for field in PROSE_FIELDS:
            for text in _strings(fields.get(field)):
                scanned += 1
                hits.extend(catalog_cardinal_hits(text, f"{name}.{field}"))
    return hits, scanned


def _curated_mapping() -> dict:
    return {name: dict(entry) for name, entry in CURATED.items()}


def _live_mapping() -> dict:
    return {
        entry.name: {f: getattr(entry, f, None) for f in PROSE_FIELDS}
        for entry in get_tool_schema().tools
    }


def _report(hits: "list[tuple]", layer: str) -> str:
    lines = [
        f"{len(hits)} cascade-catalog cardinal literal(s) in {layer}:",
    ]
    for where, line_no, name, value, context in hits[:25]:
        lines.append(f"  {where}:{line_no}  [{name}={value}]  ...{context}...")
    lines.append("")
    lines.append(
        "A catalog cardinal written as a literal has no tie to the value it "
        "describes, so it rots — measured: '17 executable' shipped in every "
        "wheel from rc438 to rc453 while the live read said 18. Do NOT bump "
        "the number: rc447 bumped one of two literals in this same entry and "
        "the sibling shipped stale for six more releases. Name the live keys "
        "instead ('counts the catalog (its ``executable`` / ``leaf`` split)'). "
        "Edit srmech/introspect/_tool_docs_curated.py — the hand-curated SSoT "
        "— then `python3 tools/regen_all.py` (add --accept-seed-drift for a "
        "deliberate curated edit) and rebuild the C library. Never hand-edit "
        "a generated artifact; the next generator run destroys it. If the "
        "cardinal is genuinely HISTORICAL, open its line with a dated stamp "
        "('At v0.9.0rcNNN: ...') and the carve-out will excuse it.")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
# L0 — the curated SSoT, read as a LOADED DICT (never as file text)
# ══════════════════════════════════════════════════════════════════════

def test_the_curated_corpus_is_not_empty() -> None:
    """The curated SSoT must still present as a populated mapping of prose.

    Measured at rc454: 666 entries, 6k+ prose strings. The floors are far
    below that — they exist to catch a format change that makes the scan below
    pass by scanning nothing, not to pin a population.
    """
    mapping = _curated_mapping()
    assert len(mapping) >= 400, (
        f"CURATED holds {len(mapping)} entries — the curated SSoT was reshaped "
        "and this gate has stopped observing. Re-point the reader; do not "
        "delete the assertion.")
    _, scanned = _scan_prose_mapping(mapping)
    assert scanned >= 1000, (
        f"only {scanned} prose strings reachable under {PROSE_FIELDS} — the "
        "curated field names changed and this gate has stopped observing.")


def test_the_curated_ssot_carries_no_catalog_cardinal() -> None:
    """L0 — strict zero, at the one surface a fix can durably live on."""
    hits, _ = _scan_prose_mapping(_curated_mapping())
    assert not hits, _report(hits, "the CURATED tool-doc SSoT")


# ══════════════════════════════════════════════════════════════════════
# L1 — the live ToolEntry surface describe() and MCP actually serve
# ══════════════════════════════════════════════════════════════════════

def test_the_live_corpus_is_not_empty() -> None:
    """The live registry must still present ToolEntry prose to scan."""
    mapping = _live_mapping()
    assert len(mapping) >= 400, (
        f"get_tool_schema().tools yielded {len(mapping)} entries — the registry "
        "was reshaped and this gate has stopped observing.")
    _, scanned = _scan_prose_mapping(mapping)
    assert scanned >= 1000, (
        f"only {scanned} prose strings reachable on live ToolEntry objects — "
        "the field names changed and this gate has stopped observing.")


def test_the_live_toolentry_surface_carries_no_catalog_cardinal() -> None:
    """L1 — strict zero on what describe() and the MCP tool list serve."""
    hits, _ = _scan_prose_mapping(_live_mapping())
    assert not hits, _report(hits, "the LIVE ToolEntry registry")


# ══════════════════════════════════════════════════════════════════════
# L2 — the checked-in generated artifacts, roster DERIVED not listed
# ══════════════════════════════════════════════════════════════════════

def _generated_outputs() -> "list[tuple[str, Path]]":
    return [(g.output, g.output_path) for g in codegen_manifest.GENERATORS]


def test_the_generator_roster_is_derived_and_present() -> None:
    """The roster comes from ``codegen_manifest.GENERATORS``, so a seventh
    generator is scanned the day it lands — the rc348 pattern. A hard-coded
    file list is how a new emitted artifact ships unguarded."""
    outputs = _generated_outputs()
    assert len(outputs) >= 6, (
        f"codegen_manifest.GENERATORS declares {len(outputs)} outputs — the "
        "manifest was reshaped and this gate has stopped observing.")
    missing = [rel for rel, path in outputs if not path.is_file()]
    assert not missing, (
        "declared generator output(s) absent from the tree: " + ", ".join(missing))
    # The reach out of python/ is a PROPERTY, not an accident of layout: the C
    # registry is the surface that carried the most copies of the rc453 defect,
    # and it is the one a bare-C host reads. This is what the SCAN_ROOTS entry
    # in test_ref_notation_emitted_rc348.py is declaring; if it ever becomes
    # false, narrow the declared root rather than leaving it over-broad.
    py_root = _SR_ROOT / "python"
    outside = [rel for rel, path in outputs if py_root not in path.parents]
    assert outside, (
        "every declared generator output now lives under docs/srmech/python — "
        "this gate no longer reaches into docs/srmech/c, so its SCAN_ROOTS "
        "declaration is over-broad. Narrow it rather than leaving a root "
        "declared that nothing reads.")


def test_generated_artifacts_carry_no_catalog_cardinal_as_text() -> None:
    """L2a — the raw text of every declared generated artifact.

    Wider than L0/L1 by construction: this reads the WHOLE emitted file, so it
    also covers summaries, categories and anything else the generator writes.
    """
    hits: "list[tuple]" = []
    for rel, path in _generated_outputs():
        text = path.read_text(encoding="utf-8", errors="replace")
        hits.extend(catalog_cardinal_hits(text, rel))
    assert not hits, _report(hits, "the GENERATED artifacts (as text)")


def test_the_byte_array_decoder_can_still_see_something() -> None:
    """rc348's non-vacuity assert, restated. Three of the generated registries
    bake prose as DECIMAL BYTE ARRAYS; if the decoder returns nothing, the
    scan below is a true-but-meaningless zero — which is exactly what rc359
    measured while five bare refs shipped inside the payload."""
    total = sum(len(decoded_blobs(path)) for _, path in _generated_outputs())
    assert total >= 5, (
        f"the embedded-byte-array decoder found {total} blobs across the "
        "generated registries — the generators changed their literal form and "
        "this channel has stopped being observed. Re-point c_byte_arrays; do "
        "not delete the assertion.")


def test_generated_byte_arrays_carry_no_catalog_cardinal() -> None:
    """L2b — the SECOND encoding channel inside the same files."""
    hits: "list[tuple]" = []
    for rel, path in _generated_outputs():
        for array_name, text in decoded_blobs(path):
            hits.extend(catalog_cardinal_hits(text, f"{rel}:{array_name}"))
    assert not hits, _report(hits, "the GENERATED byte-array payloads")


# ══════════════════════════════════════════════════════════════════════
# L3 — the compiled library (belt-and-braces; rc184 owns the primary pin)
# ══════════════════════════════════════════════════════════════════════

_LIB_PATH = getattr(_native, "_LIB_PATH", None)
_needs_native = pytest.mark.skipif(
    not getattr(_native, "HAS_NATIVE", False)
    or _LIB_PATH is None
    or not Path(_LIB_PATH).is_file(),
    reason="compiled srmech library absent (pure / numpy-absent / Pyodide cell)",
)


@_needs_native
def test_the_compiled_library_carries_no_catalog_cardinal() -> None:
    """L3 — the prose is compiled INTO the library, so it reaches a bare-C
    host that never sees Python. The primary compiled-tier guarantee is
    ``test_tool_registry_c_rc184.py``'s hash ratchet (the C registry pinned
    byte-identical to the live Python SSoT); this is the direct read.
    """
    text = Path(_LIB_PATH).read_bytes().decode("utf-8", errors="replace")
    hits = catalog_cardinal_hits(text, Path(_LIB_PATH).name)
    assert not hits, (
        _report(hits, "the COMPILED library")
        + "\n\nIf this is red on a LOCAL tree, rebuild first: the C Makefile "
          "carries no header-dependency edge, so the library does not rebuild "
          "on a registry-source change by itself — `cd docs/srmech/c && make`. "
          "Red on a CI cell, which always builds from the checked-in source, "
          "is a genuine defect.")


# ══════════════════════════════════════════════════════════════════════
# THE CLAUSE MUST STILL EXIST — strict-zero's own anti-vacuity
# ══════════════════════════════════════════════════════════════════════

#: The de-literalized clause, in the form the audit adjudicated. Held as three
#: SEPARATE tokens rather than one sentence so ordinary rewording does not red
#: the gate, while DELETING the clause does.
_POINTER_TOKENS = ("counts the catalog", "executable", "leaf")

_SUBJECT = "srmech.dsl.run_cascade_chain"


def _pointer_clause_present(text: str) -> bool:
    head = text.find(_POINTER_TOKENS[0])
    if head < 0:
        return False
    window = text[head:head + 200]
    return all(token in window for token in _POINTER_TOKENS[1:])


def test_the_pointer_clause_survives_in_the_curated_ssot() -> None:
    """Strict zero is satisfied by deleting the sentence, so the sentence is
    pinned separately: it must still be there and must still name BOTH live
    keys. Without this, the fix and the vandalism are indistinguishable."""
    entry = CURATED.get(_SUBJECT)
    assert entry is not None, (
        f"{_SUBJECT} is absent from CURATED — the entry was renamed and this "
        "gate has stopped observing. Re-point ``_SUBJECT``; do not delete it.")
    assert "explanation" in entry, (
        f"{_SUBJECT} carries no 'explanation' field (has: {sorted(entry)}) — "
        "the curated schema changed and this gate has stopped observing.")
    assert _pointer_clause_present(entry["explanation"]), (
        f"{_SUBJECT}'s explanation no longer points at the LIVE catalog split. "
        "The clause must name the ``executable`` and ``leaf`` keys rather than "
        "transcribing their values — deleting it passes the strict-zero scan "
        "and leaves the reader with nothing.")


def test_the_pointer_clause_survives_on_the_live_surface() -> None:
    """The same clause, on what describe() and MCP actually serve."""
    live = [e for e in get_tool_schema().tools if e.name == _SUBJECT]
    assert len(live) == 1, (
        f"expected exactly one live ToolEntry named {_SUBJECT}, found "
        f"{len(live)} — the registry was reshaped and this gate has stopped "
        "observing.")
    assert _pointer_clause_present(live[0].explanation), (
        f"the live {_SUBJECT} explanation no longer points at the live catalog "
        "split — the generated artifacts are stale against the curated SSoT, "
        "or the clause was deleted. Run `python3 tools/regen_all.py`.")


def test_the_pointer_clause_survives_in_the_generated_artifacts() -> None:
    """It shipped in ``_tool_docs.py`` AND ``srmech_tool_registry.c``. Both
    must still carry it, or a regeneration dropped the prose on the floor."""
    carriers = [
        rel for rel, path in _generated_outputs()
        if _pointer_clause_present(
            path.read_text(encoding="utf-8", errors="replace"))
    ]
    assert len(carriers) >= 2, (
        "the de-literalized catalog clause survives in "
        f"{len(carriers)} generated artifact(s), expected at least 2 "
        "(_tool_docs.py and srmech_tool_registry.c both embed ToolEntry "
        "prose). Either the clause was deleted or the artifacts are stale — "
        "run `python3 tools/regen_all.py`.")


# ══════════════════════════════════════════════════════════════════════
# THE LIVE MAPPING — membership, never .get(..., default)
# ══════════════════════════════════════════════════════════════════════

def test_the_live_cascade_catalog_exposes_its_partition_keys() -> None:
    """``c_runnable`` has exactly ONE existence guard tree-wide. A default
    here would make the retro-check below vacuous the day the key is dropped,
    so every key this file reads is asserted by MEMBERSHIP."""
    live = describe()["cascade_catalog"]
    for key in ("total", "executable", "leaf", "c_runnable"):
        assert key in live, (
            f"describe()['cascade_catalog'] has no {key!r} key — the mapping "
            f"was reshaped (keys: {sorted(live)}) and this gate has stopped "
            "observing. Re-point it; do not switch to a defaulted lookup.")
    assert live["executable"] + live["leaf"] == live["total"], (
        "the catalog partition no longer sums: "
        f"{live['executable']} + {live['leaf']} != {live['total']}. The "
        "two-state contract (executable | leaf) grew a third state.")


# ══════════════════════════════════════════════════════════════════════
# THE SEEDED DETECTOR — a gate that cannot return otherwise is not a
# measurement
# ══════════════════════════════════════════════════════════════════════

def test_the_detector_fires_on_the_rc453_prose_in_every_encoding() -> None:
    """Plant rc453's shipped text in each of the three encodings it really
    shipped in, and prove the predicate FIRES on all three.

    The C forms are the point: the same sentence lives there octal-escaped
    (``explanation``) and JSON-escaped-inside-C (``example``, with an em-dash).
    A pattern that spanned the em-dash would match one and silently miss the
    other.
    """
    cases = {
        "python prose": RC453_EXPLANATION_CLAUSE,
        "python example": RC453_EXAMPLE_CLAUSE,
        "C octal-escaped": RC453_C_OCTAL_FORM,
        "C json-inside-C": RC453_C_JSON_FORM,
    }
    silent = []
    for label, text in cases.items():
        hits = catalog_cardinal_hits(text, label)
        if not hits:
            silent.append(label)
    assert not silent, (
        "the catalog-cardinal detector did NOT fire on rc453's own shipped "
        "prose in these encodings: " + ", ".join(silent)
        + "\n\nThe predicate has stopped observing. Re-point it; a gate that "
          "cannot return otherwise is not a measurement.")
    # And the values it reports must be the ones that actually shipped.
    reported = {
        (name, value)
        for text in cases.values()
        for _, _, name, value, _ in catalog_cardinal_hits(text)
    }
    assert ("executable", "17") in reported, (
        f"the detector fired but never reported the stale 17: {sorted(reported)}")
    assert ("executable", "18") in reported, (
        "the detector fired but never reported the TRUE-but-banned 18 — a "
        "shape gate must reject a correct cardinal too, which is the whole "
        f"lesson of rc447: {sorted(reported)}")


def test_the_detector_fires_through_the_real_curated_scan_path() -> None:
    """Plant the rc453 explanation into a COPY of the live curated corpus and
    scan it through the SAME function the L0 test uses.

    This exercises the path, not just the regex: the L0 reader, the nested
    ``example`` walk and the carve-out all run. A regex proven in isolation
    while the reader looks at the wrong field is the classic false green.
    """
    seeded = _curated_mapping()
    assert _SUBJECT in seeded
    seeded[_SUBJECT]["explanation"] = RC453_EXPLANATION_CLAUSE
    seeded[_SUBJECT]["example"] = {
        "input": {"op_name": RC453_EXAMPLE_CLAUSE},
        "output": "6",
    }
    hits, scanned = _scan_prose_mapping(seeded)
    assert scanned >= 1000, "the seeded corpus lost its prose"
    names = {(name, value) for _, _, name, value, _ in hits}
    assert ("executable", "17") in names and ("leaf", "3") in names, (
        "the L0 scan path did not report rc453's planted explanation "
        f"cardinals: {sorted(names)}")
    assert ("executable", "18") in names, (
        "the L0 scan path did not reach the planted cardinal nested inside "
        f"example['input']['op_name']: {sorted(names)}")
    # ...and the unseeded corpus is still clean, so the fixture is what fired.
    assert not _scan_prose_mapping(_curated_mapping())[0]


def test_the_detector_fires_through_the_real_generated_file_read_path(tmp_path) -> None:
    """Plant rc453's clause into a COPY of a real generated C artifact — in
    BOTH of that file's channels — and scan the copy from disk.

    This red-demonstrates L2 end to end rather than the regex alone: the file
    read, the text channel and the byte-array channel all run. rc359 measured a
    text-only scan reporting a true-but-meaningless zero while five bare refs
    shipped inside the byte-array payload, so both channels are planted.
    """
    c_artifacts = [(rel, path) for rel, path in _generated_outputs()
                   if rel.endswith(".c")]
    assert c_artifacts, (
        "no generated C artifact is declared — the codegen manifest was "
        "reshaped and this red-demonstration has stopped observing.")
    rel, source = c_artifacts[0]
    original = source.read_text(encoding="utf-8", errors="replace")
    assert not catalog_cardinal_hits(original, rel), (
        "the unplanted artifact is already dirty; the plant below would prove "
        "nothing")

    payload = ", ".join(str(b) for b in RC453_EXPLANATION_CLAUSE.encode("utf-8"))
    planted = tmp_path / source.name
    planted.write_text(
        original
        + "\nstatic const char *seed_explanation = " + RC453_C_OCTAL_FORM + ";\n"
        + "static const char *seed_example = " + RC453_C_JSON_FORM + ";\n"
        + "static const unsigned char seed_blob[] = { " + payload + " };\n",
        encoding="utf-8")

    text_hits = catalog_cardinal_hits(
        planted.read_text(encoding="utf-8", errors="replace"), planted.name)
    assert text_hits, (
        "the L2 TEXT channel did not fire on a planted rc453 clause — the "
        "file-reading path has stopped observing.")

    blobs = decoded_blobs(planted)
    assert any(RC453_EXPLANATION_CLAUSE in text for _, text in blobs), (
        f"the byte-array decoder did not recover the planted payload from "
        f"{len(blobs)} blob(s) — re-point c_byte_arrays; do not delete this.")
    blob_hits = [
        hit
        for name, text in blobs
        for hit in catalog_cardinal_hits(text, f"{planted.name}:{name}")
    ]
    assert blob_hits, (
        "the L2 BYTE-ARRAY channel did not fire on a planted rc453 clause — "
        "this is exactly the rc359 blind spot, restored.")


# ══════════════════════════════════════════════════════════════════════
# THE DATED-CLAUSE CARVE-OUT
# ══════════════════════════════════════════════════════════════════════

def test_a_dated_ledger_line_is_carved_out() -> None:
    """A Type-A dated ledger line PASSES, and the same line without its stamp
    FIRES. Both halves are asserted: a carve-out that excused everything would
    also pass the first half."""
    assert not catalog_cardinal_hits(DATED_LEDGER_SAMPLE, "dated"), (
        "the dated-clause carve-out has stopped working. Without it this gate "
        "would demand that 'At v0.9.0rc447: 21 descriptors — 18 executable, 3 "
        "leaf' be BUMPED the moment the catalog grows, which fabricates "
        "history — a worse defect than the staleness it guards.")
    undated = DATED_LEDGER_SAMPLE.split(":", 1)[1].strip()
    hits = catalog_cardinal_hits(undated, "undated")
    assert len(hits) >= 3, (
        "strip the dated stamp and the SAME line must fire — it did not, so "
        f"the carve-out is excusing on the wrong axis: {hits}")


def test_the_carve_out_does_not_excuse_an_in_sentence_rc_reference() -> None:
    """The genuinely ambiguous case, ruled on by the project.

    rc453's clause carries ``measured as unenumerable through rc419``
    mid-sentence. A loose carve-out would read that as dating the clause and
    would excuse the exact defect this file exists to catch. The audit
    (``notes/_1653_readme_truth_audit.md``,
    ``TD-run-cascade-chain-17-explanation``) graded it **FALSE**: the
    rc-reference attaches to the ADR-0012 C6 unenumerability measurement, not
    to the cardinal. The carve-out therefore requires a FULL version token AND
    line-start, and this asserts that ruling holds.
    """
    ambiguous = (
        "the op → chain half of the word-problem bridge ADR-0012 C6 "
        "measured as unenumerable through rc419: " + RC453_EXPLANATION_CLAUSE)
    hits = catalog_cardinal_hits(ambiguous, "ambiguous")
    assert hits, (
        "the carve-out excused a clause dated only by a BARE `rc419` "
        "reference mid-sentence. That re-opens the adjudicated case: the "
        "rc-reference dates the C6 measurement, not the cardinal. Tighten the "
        "stamp back to a full version token at line start.")
    assert not DATED_LEDGER_LINE.match(ambiguous), (
        "DATED_LEDGER_LINE matched a sentence whose rc-reference is neither at "
        "line start nor a full version token.")


def test_the_carve_out_requires_the_stamp_to_open_the_line() -> None:
    """A version token buried mid-line does not date the line either."""
    buried = (
        "the engine has been stable since v0.9.0rc420 and the catalog now "
        "holds 18 executable descriptors")
    assert catalog_cardinal_hits(buried, "buried"), (
        "a mid-line version token excused a live cardinal — the carve-out is "
        "too loose and will hide the next stale literal.")


# ══════════════════════════════════════════════════════════════════════
# THE RETRO-CHECK — replay rc453 against live
# ══════════════════════════════════════════════════════════════════════

def test_the_rc453_prose_is_gone_from_every_layer() -> None:
    """Neither shipped clause survives anywhere the gate can see.

    Asserted as VERBATIM absence rather than by the pattern, because the two
    are different questions: the pattern says "no cardinal of this shape", this
    says "not THIS sentence". The second is what a botched half-regeneration
    would leave behind.
    """
    survivors = []
    for name, fields in _curated_mapping().items():
        blob = "\n".join(
            text for field in PROSE_FIELDS for text in _strings(fields.get(field)))
        if RC453_EXPLANATION_CLAUSE in blob or RC453_EXAMPLE_CLAUSE in blob:
            survivors.append(f"CURATED[{name!r}]")
    for name, fields in _live_mapping().items():
        blob = "\n".join(
            text for field in PROSE_FIELDS for text in _strings(fields.get(field)))
        if RC453_EXPLANATION_CLAUSE in blob or RC453_EXAMPLE_CLAUSE in blob:
            survivors.append(f"live[{name!r}]")
    for rel, path in _generated_outputs():
        text = path.read_text(encoding="utf-8", errors="replace")
        if RC453_EXPLANATION_CLAUSE in text:
            survivors.append(rel)
    assert not survivors, (
        "rc453's literal catalog prose survives in: " + ", ".join(survivors)
        + "\n\nA partial regeneration leaves exactly this shape. Re-run "
          "`python3 tools/regen_all.py` and rebuild the C library.")


def test_the_rc453_cardinal_no_longer_equals_live() -> None:
    """The stale half, replayed: 17 against the live ``executable``.

    If this ever compares EQUAL, re-base the retro-check onto the next stale
    literal rather than deleting it — an equality here means the catalog
    shrank back to 17, not that the defect never happened.
    """
    live = describe()["cascade_catalog"]
    shipped = catalog_cardinal_hits(RC453_EXPLANATION_CLAUSE)
    executable_values = [
        int(value) for _, _, name, value, _ in shipped if name == "executable"]
    assert executable_values == [17], (
        f"the rc453 clause no longer parses to its shipped cardinal: "
        f"{executable_values} — the constant was edited and this retro-check "
        "has stopped observing.")
    assert executable_values[0] != live["executable"], (
        f"rc453's literal 17 now EQUALS the live executable count "
        f"({live['executable']}). The catalog shrank back rather than the "
        "defect un-happening — re-base this retro-check onto the current "
        "stale literal rather than deleting it.")
