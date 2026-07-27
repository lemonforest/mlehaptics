"""rc346 (`#T975`) — the codegen dependency graph and the ``regen-all`` gate.

Six generators feed the shipped tree and three of them are downstream of a
fourth, so the order they run in is load-bearing. Before rc346 that order
lived in changelog prose, and it was got wrong repeatedly: the filed task
said three generators, rc345 discovered a fourth by shipping a stale carrier
registry, and the rc346 survey found six in the pass plus two more excluded.

These tests pin the properties that make the order impossible to get wrong:

  1. **Completeness** — every ``gen_*.py`` in the tree is either declared in
     the graph or explicitly excluded with a reason. This is the test that
     answers the miscounting directly: a seventh generator is a FAILURE
     until somebody classifies it.
  2. **Derivation** — the run order satisfies every edge implied by the
     declared ``consumes`` / ``produces``, rather than matching a list
     someone typed.
  3. **Freshness** — no generated file is stale (content equality, the
     robust form; NOT mtime, which is meaningless in a git checkout).
  4. **The guards** — a bare single-generator invocation refuses.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SR_ROOT = _HERE.parent.parent          # docs/srmech
_TOOLS = _SR_ROOT / "python" / "tools"

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import codegen_manifest as cm  # noqa: E402
import regen_all  # noqa: E402


# ── 1. completeness: the anti-miscount guard ──────────────────────────


def test_every_generator_is_classified() -> None:
    """Every generator script on disk is DECLARED or EXPLICITLY EXCLUDED.

    The set was miscounted three times running (three -> four -> six). This
    makes the next miscount a red test instead of a stale shipped table:
    adding ``c/tools/gen_whatever.py`` fails here until its edges are
    declared in ``GENERATORS`` or its absence is justified in ``EXCLUDED``.
    """
    found = set(cm.discover_generator_scripts())
    declared = {g.script for g in cm.GENERATORS}
    excluded = set(cm.EXCLUDED)

    unclassified = found - declared - excluded
    assert not unclassified, (
        "generator script(s) present on disk but neither declared in "
        f"codegen_manifest.GENERATORS nor listed in EXCLUDED: "
        f"{sorted(unclassified)}. Declare its consumes/produces so the "
        "order can be derived, or add it to EXCLUDED with the reason."
    )

    phantom = (declared | excluded) - found
    assert not phantom, (
        f"codegen_manifest references generator(s) that do not exist: "
        f"{sorted(phantom)}"
    )


def test_every_exclusion_states_a_reason() -> None:
    """An exclusion without a reason is a to-do pretending to be a decision."""
    for script, reason in cm.EXCLUDED.items():
        assert len(reason) > 80, f"{script}: exclusion reason is too thin"


def test_declared_outputs_all_exist() -> None:
    for gen in cm.GENERATORS:
        assert gen.script_path.exists(), f"missing generator {gen.script}"
        assert gen.output_path.exists(), f"missing output {gen.output}"


# ── 2. the order is DERIVED ───────────────────────────────────────────


def test_graph_is_acyclic_and_total() -> None:
    order = cm.resolve_order()
    assert len(order) == len(cm.GENERATORS)
    assert {g.name for g in order} == {g.name for g in cm.GENERATORS}


def test_derived_order_satisfies_every_declared_edge() -> None:
    """The run order is a valid topological sort of the DECLARED edges.

    This is the property that replaces "remember to run tool_docs first".
    Nothing here names a generator: if the declarations change, the expected
    order changes with them.
    """
    order = [g.name for g in cm.resolve_order()]
    pos = {name: i for i, name in enumerate(order)}
    for before, after in cm.edges():
        assert pos[before] < pos[after], (
            f"derived order violates the declared edge {before} -> {after}: "
            f"{order}"
        )


def test_tool_docs_precedes_every_schema_consumer() -> None:
    """The specific edge that trap 1 is made of, derived not asserted.

    ``gen_tool_docs`` writes ``_tool_docs.py``; ``tool_schema`` merges it
    into every ``ToolEntry``; the tool / carrier / responsion registries read
    that schema. So all three must follow it — and they must follow it
    because the RESOURCE CLOSURE says so, not because this test says so.
    """
    order = [g.name for g in cm.resolve_order()]
    pos = {name: i for i, name in enumerate(order)}
    for consumer in ("gen_tool_registry", "gen_carrier_registry",
                     "gen_responsion_registry"):
        gen = next(g for g in cm.GENERATORS if g.name == consumer)
        assert cm.R_TOOL_DOCS in cm.closure(gen.consumes), (
            f"{consumer} should transitively depend on {cm.R_TOOL_DOCS}")
        assert pos["gen_tool_docs"] < pos[consumer]


def test_carrier_registry_depends_on_the_tool_surface() -> None:
    """The rc345 defect, encoded as a declaration.

    rc345 asked "did a carrier move?", answered no correctly, skipped
    ``gen_carrier_registry`` and shipped a stale table — because the carrier
    registry bakes the SORTED TOOL-NAME back-index, so it goes stale on any
    change to ``tools.total`` whether or not a carrier moved. The rule is
    mechanical, and here it is as a mechanical fact about the graph.
    """
    gen = next(g for g in cm.GENERATORS if g.name == "gen_carrier_registry")
    reachable = cm.closure(gen.consumes)
    assert cm.R_TOOL_SCHEMA in reachable
    assert cm.R_TOOL_DOCS in reachable


def test_independent_generators_have_no_inbound_edge() -> None:
    """``gen_c_claims`` and ``gen_class_registry`` were MEASURED independent
    of the tool surface (rc346 perturbation runs). Their declarations should
    say so — if someone later gives them a tool-schema edge, this fails and
    forces the measurement to be redone rather than assumed."""
    for name in ("gen_c_claims", "gen_class_registry"):
        gen = next(g for g in cm.GENERATORS if g.name == name)
        assert cm.R_TOOL_SCHEMA not in cm.closure(gen.consumes), (
            f"{name} now declares a tool-schema dependency; re-measure "
            "before trusting it")


# ── 3. freshness: content equality, never mtime ───────────────────────


def test_no_generated_file_is_stale() -> None:
    """Every generated file equals what its generator produces right now.

    Content equality is the robust staleness signal. An mtime comparison
    ("fail if _tool_docs.py is newer than the registry") would false-fire on
    every fresh clone, rebase and ``git checkout``, because those set mtimes
    in arbitrary order — and a guard that false-fires gets suppressed.

    This also closes a real gap: ``_tool_docs.py`` is the ROOT of the
    dependency order and, until rc346, was the one generated file in the
    chain with no staleness check at all. The four C registries and
    ``_c_claims.py`` each had one; the file they all descend from did not.
    """
    texts = regen_all.render_all()
    stale = []
    for gen in cm.resolve_order():
        want = cm.normalise(texts[gen.name])
        have = cm.normalise(gen.output_path.read_text(encoding="utf-8"))
        if want != have:
            stale.append(f"{gen.output} "
                         f"({len(have)} on disk vs {len(want)} regenerated)")
    assert not stale, (
        "generated file(s) are STALE:\n  " + "\n  ".join(stale)
        + "\n\nRegenerate with:  python3 tools/regen_all.py"
    )


# ── 4. the guards ─────────────────────────────────────────────────────


@pytest.mark.parametrize("gen", cm.GENERATORS, ids=lambda g: g.name)
def test_standalone_invocation_refuses(gen: cm.Generator) -> None:
    """A bare ``python3 tools/gen_x.py`` refuses and writes nothing.

    Two defects at once. The four C generators wrote to STDOUT, so a bare
    run with no redirect changed nothing while exiting 0 — success-shaped
    and inert. And running any single generator leaves everything
    downstream of it stale, which is how rc345 shipped red.
    """
    proc = subprocess.run(
        [sys.executable, str(gen.script_path)],
        capture_output=True, cwd=str(_SR_ROOT),
        env={k: v for k, v in __import__("os").environ.items()
             if k != cm.RUNNING_ENV},
    )
    assert proc.returncode == 2, (
        f"{gen.name} did not refuse a standalone run "
        f"(exit {proc.returncode})")
    assert proc.stdout == b"", (
        f"{gen.name} emitted {len(proc.stdout)} bytes despite refusing")
    assert b"REFUSING" in proc.stderr
    assert b"regen_all" in proc.stderr, (
        f"{gen.name}'s refusal should point at the correct command")


def test_only_refuses_without_force_partial() -> None:
    rc = regen_all.main(["--only", "gen_tool_registry"])
    assert rc == 2, "--only should refuse without --force-partial"


def test_only_rejects_an_unknown_generator() -> None:
    rc = regen_all.main(["--only", "gen_nope", "--force-partial"])
    assert rc == 2


# ── 5. line endings (trap 3) ──────────────────────────────────────────


@pytest.mark.parametrize("eol", ["\n", "\r\n"])
def test_write_preserves_existing_eol(tmp_path: Path, eol: str) -> None:
    """A rewrite keeps the file's own convention, so unchanged content moves
    ZERO bytes on disk.

    This tree has no ``.gitattributes`` and ``core.autocrlf=true``, and the
    generated files are genuinely mixed (measured rc346: three CRLF, three
    LF). git normalises both to LF in the object store, so a
    wrong-convention write rewrites every line on disk while ``git diff``
    stays clean — which is exactly how a real one-line change hides inside
    a whole-file rewrite.
    """
    p = tmp_path / "f.txt"
    p.write_bytes(("a" + eol + "b" + eol).encode("utf-8"))
    assert cm.detect_eol(p) == eol

    # Same content, LF-shaped input: must not move a byte.
    moved = cm.write_preserving_eol(p, "a\nb\n")
    assert moved is False
    assert p.read_bytes() == ("a" + eol + "b" + eol).encode("utf-8")

    # Real change: rewritten in the file's own convention.
    moved = cm.write_preserving_eol(p, "a\nc\n")
    assert moved is True
    assert p.read_bytes() == ("a" + eol + "c" + eol).encode("utf-8")


def test_normalise_is_comparison_only() -> None:
    assert cm.normalise("a\r\nb") == "a\nb"
    assert cm.normalise("a\nb") == "a\nb"
