#!/usr/bin/env python3
"""The DECLARED codegen dependency graph (rc346, `#T975`).

Every generated file in this tree is produced by a script under
``python/tools/`` or ``c/tools/``. Several of those scripts read what
another one WRITES, so the order they run in is load-bearing — and until
rc346 that order lived only in changelog prose and in whoever happened to
remember it. It was remembered wrong three times in a row: the filed task
said three generators, rc345 found a fourth the hard way (it shipped red),
and the survey for this rc found **eight producers**, four of which emit
the C registry tables.

So the order is no longer written down. It is DERIVED, here, from what each
generator declares it consumes and produces. Adding a ninth generator means
adding a row to :data:`GENERATORS` with its ``consumes`` / ``produces``; the
topological sort places it. Nobody has to remember anything, and
:func:`discover_generator_scripts` makes forgetting to declare it a test
failure rather than a silent gap.

The resource model
------------------
Generators do not consume each other's FILES directly — they consume live
Python objects (``get_tool_schema()``, ``_pure_carrier_schema()``) which are
themselves built from generated files. Declaring only file paths would miss
that, which is exactly how rc345 shipped red: it asked the SEMANTIC question
("did a carrier move?"), answered it correctly, and still regenerated
nothing, because the carrier registry's real input is the *sorted tool-name
list*, not the carrier metadata.

:data:`DERIVES` closes that gap. It records which logical resource is built
from which, so a generator that declares ``consumes=(R_CARRIER_SCHEMA,)``
transitively depends on ``R_TOOL_DOCS`` without anyone re-deriving the chain
by hand. The rule that results is MECHANICAL, not semantic:

    the tool surface changed  =>  every generator downstream of
    ``R_TOOL_SCHEMA`` regenerates, whether or not its own subject moved.

Measured, not assumed
---------------------
The edges below were established by perturbation, not by reading imports.
Each input was changed one at a time and every generator re-run to see whose
output moved (``mode`` / ``gen`` / ``sha`` triples, rc346 bring-up):

  * **a new public callable** (``tools.total`` +1) moved ``_tool_docs.py``
    (149084 -> 149183 bytes), ``srmech_tool_registry.c`` and
    ``srmech_carrier_registry.c`` (180889 -> 181113). It did NOT move the
    responsion or class tables.
  * **an edited tool summary** (count-neutral) moved
    ``srmech_tool_registry.c`` alone.
  * **an edited ``_tool_docs.py``** moved ``srmech_tool_registry.c`` alone,
    and by EXACTLY the 14 bytes injected (827380 -> 827394). That is trap 1
    measured at the mechanism: the tool registry embeds the docs prose, so
    running it before ``gen_tool_docs`` leaves it stale against the very
    text it contains.
  * **renaming a registered op** made ``_pure_responsion_schema()`` raise
    ``RuntimeError: ... references unregistered operator ...``. The
    responsion table's dependency on the tool surface is real but is a
    VALIDATION edge: additions do not move its bytes, removals and renames
    break it outright. It belongs in the pass for that reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Tuple

# ``python/tools/codegen_manifest.py`` -> ``docs/srmech``
_TOOLS_DIR = Path(__file__).resolve().parent
PY_ROOT = _TOOLS_DIR.parent
SR_ROOT = PY_ROOT.parent


# ── logical resources ─────────────────────────────────────────────────
#
# A resource is an artifact a generator reads or writes. Some are files on
# disk; some are live Python objects assembled FROM those files. Both kinds
# are named here so an edge can be declared against whichever one the
# generator actually touches.

R_TOOL_DOCS = "tool_docs"                  # srmech/amsc/_tool_docs.py
R_TOOL_DOCS_CURATED = "tool_docs_curated"  # srmech/amsc/_tool_docs_curated.py
R_CARRIER_EXAMPLES = "carrier_examples"    # srmech/amsc/_carrier_examples.py
R_TOOL_SCHEMA = "tool_schema"              # live get_tool_schema()
R_CARRIER_SCHEMA = "carrier_schema"        # live _pure_carrier_schema()
R_RESPONSION_SCHEMA = "responsion_schema"  # live _pure_responsion_schema()
R_C_CLAIMS = "c_claims"                    # srmech/amsc/_c_claims.py
R_ROSETTA_LEDGER = "rosetta_ledger"        # tests/rosetta_classification.ndjson
R_C_HEADER = "c_header"                    # c/include/srmech.h
R_CLASS_TOML = "class_catalog_toml"        # cascade/catalogs/class_catalog/*.toml
R_TOOL_REGISTRY_C = "tool_registry_c"
R_CARRIER_REGISTRY_C = "carrier_registry_c"
R_RESPONSION_REGISTRY_C = "responsion_registry_c"
R_CLASS_REGISTRY_C = "class_registry_c"

#: Which resource is BUILT FROM which — the live-object data flow that file
#: paths alone cannot express. Read as "key is derived from values".
#:
#: ``tool_schema`` reads ``_tool_docs.py`` at import (``tool_schema.py``
#: merges ``TOOL_DOCS`` into every ``ToolEntry.explanation`` / ``.example``),
#: so everything downstream of the schema is downstream of the docs.
DERIVES: Dict[str, Tuple[str, ...]] = {
    R_TOOL_SCHEMA: (R_TOOL_DOCS,),
    R_CARRIER_SCHEMA: (R_TOOL_SCHEMA, R_CARRIER_EXAMPLES),
    R_RESPONSION_SCHEMA: (R_TOOL_SCHEMA, R_CARRIER_SCHEMA),
}


def closure(resources: Tuple[str, ...]) -> frozenset:
    """``resources`` plus everything they are transitively derived from."""
    out: set = set()
    stack = list(resources)
    while stack:
        r = stack.pop()
        if r in out:
            continue
        out.add(r)
        stack.extend(DERIVES.get(r, ()))
    return frozenset(out)


# ── generator rows ────────────────────────────────────────────────────


@dataclass(frozen=True)
class Generator:
    """One code generator and the edges that place it in the order."""

    name: str
    #: Path to the script, relative to ``docs/srmech``.
    script: str
    #: Path to the file it writes, relative to ``docs/srmech``.
    output: str
    #: Logical resources it reads.
    consumes: Tuple[str, ...]
    #: Logical resources it writes.
    produces: Tuple[str, ...]
    #: Name of the module-level callable returning the full output TEXT.
    #: Every generator is driven through this rather than through its
    #: ``__main__`` block, so the runner owns the write — which is how the
    #: stdout trap (trap 2) stops being reachable at all.
    render: str
    #: Human note carried into ``--list`` output.
    note: str = ""

    @property
    def script_path(self) -> Path:
        return SR_ROOT / self.script

    @property
    def output_path(self) -> Path:
        return SR_ROOT / self.output


#: The generators ``regen-all`` runs, in DECLARATION order (which is NOT
#: necessarily run order — :func:`resolve_order` derives that).
GENERATORS: Tuple[Generator, ...] = (
    Generator(
        name="gen_tool_docs",
        script="python/tools/gen_tool_docs.py",
        output="python/srmech/amsc/_tool_docs.py",
        consumes=(R_TOOL_DOCS_CURATED, R_TOOL_SCHEMA),
        produces=(R_TOOL_DOCS,),
        render="_render_tool_docs",
        note="docstring seed + curation merge; FEEDS the tool schema",
    ),
    Generator(
        name="gen_c_claims",
        script="python/tools/gen_c_claims.py",
        output="python/srmech/amsc/_c_claims.py",
        consumes=(R_ROSETTA_LEDGER, R_C_HEADER),
        produces=(R_C_CLAIMS,),
        render="_render_c_claims",
        note="op -> C-symbol manifest; independent of the tool docs",
    ),
    Generator(
        name="gen_tool_registry",
        script="c/tools/gen_tool_registry.py",
        output="c/src/srmech_tool_registry.c",
        consumes=(R_TOOL_SCHEMA,),
        produces=(R_TOOL_REGISTRY_C,),
        render="generate",
        note="EMBEDS the docs prose — measured 14-byte propagation",
    ),
    Generator(
        name="gen_carrier_registry",
        script="c/tools/gen_carrier_registry.py",
        output="c/src/srmech_carrier_registry.c",
        consumes=(R_CARRIER_SCHEMA,),
        produces=(R_CARRIER_REGISTRY_C,),
        render="generate",
        note="bakes the sorted tool-name back-index; moves on tools.total",
    ),
    Generator(
        name="gen_responsion_registry",
        script="c/tools/gen_responsion_registry.py",
        output="c/src/srmech_responsion_registry.c",
        consumes=(R_RESPONSION_SCHEMA,),
        produces=(R_RESPONSION_REGISTRY_C,),
        render="generate",
        note="validates operator refs against the schema; raises on a rename",
    ),
    Generator(
        name="gen_class_registry",
        script="c/tools/gen_class_registry.py",
        output="c/src/srmech_class_registry.c",
        consumes=(R_CLASS_TOML,),
        produces=(R_CLASS_REGISTRY_C,),
        render="generate",
        note="bakes the [class] TOML bytes; no srmech import at all",
    ),
)


#: Generator scripts deliberately NOT in the automatic pass, each with the
#: reason. This is not a to-do list — every entry is a decision, and the
#: completeness test forces a new script to land in one list or the other.
EXCLUDED: Dict[str, str] = {
    "c/tools/gen_unicode_fold_tables.py": (
        "VENDORED UPSTREAM DATA, NON-HERMETIC. Fetches the Unicode character "
        "database over the network (urllib.request.urlopen) and emits both "
        "c/src/srmech_unicode_fold_tables.h and "
        "python/srmech/amsc/_unicode_fold_tables.py from that one source. It "
        "imports no srmech module and reads nothing this graph produces, so "
        "no tool-surface change can stale it. Running it in a dev loop or in "
        "CI would make both non-deterministic and network-dependent for zero "
        "benefit; tests/test_unicode_fold_tables_attested.py re-verifies the "
        "vendored bytes instead. Refresh it deliberately, on its own."
    ),
    "c/tools/gen_unicode_gb_tables.py": (
        "VENDORED UPSTREAM DATA, NON-HERMETIC. The UAX #29 grapheme-break "
        "peer of gen_unicode_fold_tables.py — same reasoning, same network "
        "fetch, same dual C-header + Python-module emission, same attested "
        "re-verification test. Not tool-surface dependent."
    ),
    "python/tools/gen_curated_probe.py": (
        "HUMAN-IN-THE-LOOP CURATION, NOT A SSoT REBUILD. Its own docstring "
        "says 'NOT the SSoT — the human reviews/edits the emitted file'. It "
        "executes central ops and refreshes _tool_docs_curated.py, which is "
        "the CURATION floor that gen_tool_docs merges OVER the auto-seed. "
        "Running it unattended would let a probe result overwrite reviewed "
        "prose — the rc274->rc290 defect (`#T916`) with the blast radius "
        "moved onto the file that exists to survive regeneration. Run it by "
        "hand when curation is the intent, then review the diff."
    ),
    "python/tools/gen_carrier_examples_probe.py": (
        "HUMAN-IN-THE-LOOP CURATION, NOT A SSoT REBUILD. Emits a SKELETON of "
        "per-carrier construction examples for a human to fold into "
        "carrier_schema._CARRIERS ('NOT the SSoT — the human reviews the "
        "emitted skeleton'). Same reasoning as gen_curated_probe.py."
    ),
}
# NB ``python/tools/run_worked_examples.py`` (rc354, gh #1530 §K) is NOT listed
# above, and must not be: :func:`discover_generator_scripts` matches ``gen_*.py``
# only, so a non-``gen_`` tool is never in ``found`` and listing it makes it a
# PHANTOM (``test_every_generator_is_classified`` fails on that half of the
# guard). It is also not a generator by nature — it produces a MEASUREMENT
# (``tests/worked_examples_result.ndjson``), nothing in the wheel derives from
# it, and its result legitimately differs between the native and pure cells.


# ── render adapters ───────────────────────────────────────────────────
#
# Four generators expose ``generate() -> str`` already. The two Python-side
# ones write in place from ``main()``, so they get a thin adapter that
# returns the same TEXT their main() would have written — letting the runner
# own every write uniformly.


def _render_tool_docs(mod, *, accept_seed_drift: bool = False) -> str:
    """``gen_tool_docs`` output text, with its un-rederivable-prose guard
    (rc291, `#T916`) preserved.

    The guard is the reason this adapter exists rather than a call to
    ``main()``: it must still refuse to destroy curation that lives neither
    in ``CURATED`` nor in a current docstring, and it must refuse BEFORE the
    runner writes anything.
    """
    docs, seed, curated = mod.build_docs()
    lost = mod.unrederivable_fields(
        mod.load_committed(SR_ROOT / "python/srmech/amsc/_tool_docs.py"),
        seed, curated)
    if lost and not accept_seed_drift:
        n = sum(len(v) for v in lost.values())
        detail = "; ".join(f"{k}: {', '.join(v)}" for k, v in sorted(lost.items()))
        raise RuntimeError(
            f"gen_tool_docs refuses to write — {n} field(s) across "
            f"{len(lost)} tool(s) would be DESTROYED (neither in "
            f"_tool_docs_curated.py nor re-derivable from a docstring): "
            f"{detail}. Move the text into _tool_docs_curated.py, or re-run "
            f"with --accept-seed-drift if a docstring legitimately changed.")
    return mod.render(docs)


def _render_c_claims(mod, **_kw) -> str:
    """``gen_c_claims`` output text (its ``main()`` writes the same string)."""
    import importlib
    claims, unverifiable, _off_header = mod.extract()
    native_mod = importlib.import_module("srmech.amsc._native")
    abi = getattr(native_mod, "EXPECTED_ABI_VERSION", 0)
    return mod.render(claims, unverifiable, abi)


#: Adapters that live here rather than in the generator scripts.
_LOCAL_RENDERERS: Dict[str, Callable] = {
    "_render_tool_docs": _render_tool_docs,
    "_render_c_claims": _render_c_claims,
}


def get_renderer(gen: Generator, mod) -> Callable:
    """The zero-arg-ish callable returning ``gen``'s full output text."""
    if gen.render in _LOCAL_RENDERERS:
        fn = _LOCAL_RENDERERS[gen.render]
        return lambda **kw: fn(mod, **kw)
    fn = getattr(mod, gen.render, None)
    if fn is None:
        raise RuntimeError(
            f"{gen.name}: {gen.script} has no `{gen.render}` callable")
    return lambda **_kw: fn()


# ── order derivation ──────────────────────────────────────────────────


def edges() -> Tuple[Tuple[str, str], ...]:
    """``(before, after)`` pairs implied by the declared consumes/produces.

    ``a`` precedes ``b`` when something ``a`` produces is in the transitive
    closure of what ``b`` consumes.
    """
    out = []
    for b in GENERATORS:
        needs = closure(b.consumes)
        for a in GENERATORS:
            if a.name == b.name:
                continue
            if needs & frozenset(a.produces):
                out.append((a.name, b.name))
    return tuple(out)


def resolve_order() -> Tuple[Generator, ...]:
    """The generators in a valid run order, derived from the declarations.

    Kahn's algorithm with a declaration-order tiebreak, so the result is
    deterministic — two runs on the same manifest always agree, which the
    idempotence proof depends on.
    """
    by_name = {g.name: g for g in GENERATORS}
    rank = {g.name: i for i, g in enumerate(GENERATORS)}
    incoming: Dict[str, set] = {g.name: set() for g in GENERATORS}
    outgoing: Dict[str, set] = {g.name: set() for g in GENERATORS}
    for a, b in edges():
        incoming[b].add(a)
        outgoing[a].add(b)

    ready = sorted((n for n, deps in incoming.items() if not deps),
                   key=rank.__getitem__)
    order: list = []
    while ready:
        n = ready.pop(0)
        order.append(by_name[n])
        for m in sorted(outgoing[n], key=rank.__getitem__):
            incoming[m].discard(n)
            if not incoming[m]:
                ready.append(m)
        ready.sort(key=rank.__getitem__)

    if len(order) != len(GENERATORS):
        stuck = sorted(set(by_name) - {g.name for g in order})
        raise RuntimeError(
            f"codegen dependency graph has a CYCLE — cannot order {stuck}")
    return tuple(order)


# ── discovery (the anti-miscount guard) ───────────────────────────────


def discover_generator_scripts() -> Tuple[str, ...]:
    """Every ``gen_*.py`` under a ``tools/`` directory in this tree.

    The set this graph must account for. Compared against
    ``GENERATORS`` + ``EXCLUDED`` by
    ``tests/test_regen_all_rc346.py::test_every_generator_is_classified`` —
    the guard that makes a NEW generator a test failure until somebody
    declares its edges or states why it is out of the pass. That test is the
    structural answer to this set having been miscounted three times.
    """
    found = []
    for tools_dir in sorted(SR_ROOT.glob("*/tools")):
        for script in sorted(tools_dir.glob("gen_*.py")):
            found.append(script.relative_to(SR_ROOT).as_posix())
    return tuple(found)


# ── the standalone-invocation guard ───────────────────────────────────

#: Set by ``regen_all.py`` while it drives a generator, so the guard below
#: can tell "the runner called me" from "a human typed the old command".
#: One SSoT — both sides read it from here.
RUNNING_ENV = "SRMECH_REGEN_ALL"


def require_regen_all(gen_name: str) -> None:
    """Refuse a bare ``python3 tools/gen_x.py`` invocation.

    Called from a generator's ``__main__`` block ONLY, so importing the
    module (which is how every codegen test drives it) is unaffected.

    The point is that the DEFAULT path is the correct one. Running a single
    generator by hand is how rc345 shipped a carrier registry stale against
    a tool list it never re-read, and how the four stdout generators could
    be "run" with no redirect and change nothing at all. Both are still
    reachable — behind a flag that names what is being accepted.
    """
    import os
    import sys

    if os.environ.get(RUNNING_ENV) == "1":
        return
    if "--standalone" in sys.argv[1:]:
        return
    after = sorted({b for a, b in edges() if a == gen_name})
    print(
        f"REFUSING to run {gen_name} standalone.\n\n"
        f"Generated files in this tree feed each other, and this script is "
        f"only correct as part of the ordered pass.\n"
        + (f"{gen_name} feeds: {', '.join(after)} — running it alone leaves "
           f"those stale against it.\n" if after else "")
        + f"\nRun the full ordered pass:\n"
        f"    python3 tools/regen_all.py          (from docs/srmech/python)\n"
        f"\nIf you genuinely want just this one:\n"
        f"    python3 tools/regen_all.py --only {gen_name} --force-partial\n"
        f"    python3 {gen_name}.py --standalone   (raw; you own the "
        f"redirect and the line endings)\n",
        file=sys.stderr)
    raise SystemExit(2)


# ── line endings (trap 3) ─────────────────────────────────────────────
#
# There is no single on-disk convention to match: measured at rc346 this
# tree carries _tool_docs.py, srmech_responsion_registry.c and
# srmech_class_registry.c as CRLF while _c_claims.py,
# srmech_tool_registry.c and srmech_carrier_registry.c are LF — with no
# .gitattributes and core.autocrlf=true, so git normalises everything to LF
# in the object store and the working-tree difference is invisible to
# `git diff`. A generator writing the other convention therefore rewrites
# every line on disk while showing a clean diff, which is exactly how a
# real one-line change hides inside a whole-file rewrite.
#
# So: PRESERVE whatever each file already uses (zero byte movement when the
# content is unchanged), and COMPARE normalised (never false-fire on the
# convention). Content is the invariant; the convention is not.


def detect_eol(path: Path) -> str:
    """The dominant line terminator of an existing file; ``"\\n"`` if new."""
    if not path.exists():
        return "\n"
    data = path.read_bytes()
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    return "\r\n" if crlf > lf else "\n"


def normalise(text: str) -> str:
    """EOL-insensitive form, for comparison only."""
    return text.replace("\r\n", "\n")


def write_preserving_eol(path: Path, text: str) -> bool:
    """Write ``text`` using ``path``'s existing EOL convention.

    Returns True when the bytes on disk actually changed.
    """
    eol = detect_eol(path)
    payload = normalise(text)
    if eol != "\n":
        payload = payload.replace("\n", eol)
    encoded = payload.encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return False
    path.write_bytes(encoded)
    return True
