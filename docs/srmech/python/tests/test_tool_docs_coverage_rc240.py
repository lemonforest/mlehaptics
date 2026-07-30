"""rc240 (#838) — the introspection docs coverage RATCHET.

Every srmech-owned tool must expose BOTH an EXPLANATION (what it does / when to
use, beyond the one-line summary) and an EXAMPLE (executed input->output where
safe, else an honest signature usage-snippet). This pins the rc240 floor as a
hard invariant that can only be maintained or improved — a new tool that ships
without docs fails here.

Also guards the silent-drop footgun: every CURATED key must be a REAL registered
tool name (a curation entry keyed on a non-existent name would be silently
ignored by the generator).

numpy-free (imports only srmech + stdlib), per the numpy-absent CI cell.
"""

from __future__ import annotations

from srmech.amsc.tool_schema import get_tool_schema, warmup_all

warmup_all()

# Monotone floor: the count of tools whose EXAMPLE is a real executed one (vs
# an honest signature snippet). Curation grows this over subsequent rcs — it
# may rise, never fall.
_MIN_EXECUTED_EXAMPLES = 90

# What counts as a record of a REAL execution: an ``output`` PLUS a record of
# what produced it. Two forms are in the tree and both are honest:
#
#   {input, output}   the rc240 single-call form — the kwargs that were passed.
#   ``worked``        the rc353 (`#T1006`) WORKED form — the executable source
#                     of a few coherent calls that produced ``output``.
#
# Membership is deliberately tested by KEY PRESENCE, not by an exact key set:
# the worked form is being adopted family-by-family and different families pair
# it with different companions (``why``, and some also keep the original
# ``input``). Pinning exact sets would silently drop those from the floor below
# and let the executed-example count erode while looking green.
_EXECUTED_SOURCE_KEYS = ("input", "worked")


def _srmech_tools():
    return [t for t in get_tool_schema().tools if t.owner == "srmech"]


def _is_executed(ex) -> bool:
    """True iff ``ex`` has an ``output`` AND a record of what produced it."""
    return (isinstance(ex, dict) and "output" in ex
            and any(k in ex for k in _EXECUTED_SOURCE_KEYS))


def test_every_srmech_tool_has_explanation() -> None:
    missing = [t.name for t in _srmech_tools()
               if not (t.explanation and t.explanation.strip())]
    assert not missing, (
        f"{len(missing)} srmech tools have no explanation (rc240 #838 floor is "
        f"100%); regenerate srmech/amsc/_tool_docs.py via tools/gen_tool_docs.py: "
        f"{missing[:5]}"
    )


def test_every_srmech_tool_has_example() -> None:
    missing = [t.name for t in _srmech_tools() if not t.example]
    assert not missing, (
        f"{len(missing)} srmech tools have no example (rc240 #838 floor is 100%): "
        f"{missing[:5]}"
    )


def test_every_example_is_well_formed() -> None:
    """An example is a real execution (:func:`_is_executed`) OR an honest
    {call} usage snippet — never an output with no record of what produced it."""
    bad = []
    for t in _srmech_tools():
        ex = t.example
        if not ex:
            continue
        keys = set(ex)
        if _is_executed(ex) or keys == {"call"}:
            continue
        # An ``output`` with neither an ``input`` nor a ``worked`` source is a
        # claim nobody can re-check — exactly the fabricated-output shape.
        if "output" in keys and not ({"input", "worked"} & keys):
            bad.append(t.name)
    assert not bad, (
        f"examples with an output but no input/worked source (fabricated?): "
        f"{bad[:5]}"
    )


def test_executed_example_floor_is_monotone() -> None:
    n = sum(1 for t in _srmech_tools() if _is_executed(t.example))
    assert n >= _MIN_EXECUTED_EXAMPLES, (
        f"only {n} tools have a real executed example; the rc240 "
        f"floor is {_MIN_EXECUTED_EXAMPLES} (curation grows this — never lower it)"
    )


# NOT SHIPPED YET — the TRUTH guard on the worked form (rc353, `#T1006`).
#
# ``_is_executed`` above is a SHAPE check, and a shape check cannot tell a real
# capture from a typed one. The guard that closes that gap is: re-execute each
# ``worked`` source and diff its stdout against the committed ``output``. It was
# written, run, and deliberately NOT shipped in this rc, because the arc
# currently carries TWO incompatible worked conventions:
#
#   * print-driven capture  — ``worked`` is a script whose stdout IS ``output``
#     (the Class-L laplacian family; all 56 re-execute byte-identically in 7.7 s,
#     which is what makes the guard cheap enough to want);
#   * REPL transcript       — ``worked`` is a list of bare expressions and
#     ``output`` is a hand-aligned annotated table of their return values, some
#     of which deliberately RAISE to document a ceiling (the Class-N rational
#     family, e.g. ``continued_fraction``'s uint64 wall).
#
# Re-execution verifies the first and misfires on all 160 of the second. A guard
# that fires on correct work gets suppressed, and a suppressed guard is worse
# than none — so the truth check waits on ONE convention being chosen for the
# arc. Whoever settles it should land this, not re-derive it:
#
#     for t in _srmech_tools():
#         ex = t.example
#         if not (isinstance(ex, dict) and "worked" in ex):
#             continue
#         buf = io.StringIO()
#         with redirect_stdout(buf), redirect_stderr(buf):
#             exec(compile(ex["worked"], f"<{t.name}>", "exec"), {})
#         assert buf.getvalue().rstrip("\n") == ex["output"]
#
# Until then "executed" is asserted per family by the authoring probe, not by
# this suite — which is exactly the gap being recorded here rather than hidden.


def test_curated_keys_are_all_registered() -> None:
    """Every hand-curated entry must key on a REAL registered tool name — a
    typo'd key would be silently dropped by the generator (the merge is keyed
    on the registered tool name, not the callable path)."""
    try:
        from srmech.amsc._tool_docs_curated import CURATED
    except Exception:  # noqa: BLE001
        CURATED = {}
    names = {t.name for t in get_tool_schema().tools}
    orphans = [k for k in CURATED if k not in names]
    assert not orphans, (
        f"CURATED keys not in the registry (silently dropped): {orphans}"
    )


def test_every_carrier_has_construction_example() -> None:
    """rc241 (#839): every registered CARRIER exposes a construction example
    (how to build/obtain it) — the operand-side peer of the tool floor. A new
    carrier that ships without one fails here."""
    from srmech.amsc.carrier_schema import carrier_schema

    sch = carrier_schema()
    missing = [name for name, c in sch.items() if not c.get("example")]
    assert not missing, (
        f"{len(missing)} carriers have no construction example (rc241 floor is "
        f"100%); regenerate srmech/amsc/_carrier_examples.py: {missing[:5]}"
    )


# ── rc363: the curated-row PRESERVATION gate ─────────────────────────────────
#
# The gate above is a COVERAGE floor: it fails when a registered carrier has no
# example at all. That is not the same property as PRESERVATION, and rc363
# measured the difference the hard way.
#
# `tools/gen_carrier_examples_probe.py` has claimed since rc241 that
# "hand-curated construction examples may be added here and are preserved".
# They were not: `main()` rebuilt the whole file from its derived dicts, so a
# row added by hand to `_carrier_examples.py` vanished on the next run. At rc363
# regenerating for two new carriers silently dropped the rc362 `Qalg` row, whose
# `yields` carries the zero-divisor / irrationality witness a bare `repr` cannot
# show. The coverage floor would eventually have caught the ROW disappearing
# (Qalg is a registered carrier) — but only after a commit, and it can never
# catch the richer `yields` CONTENT being replaced by a thinner derived one, nor
# a curated row for a key that is not a registered carrier.
#
# So the mechanism (`_CURATED`, applied last) gets its own gate. ADR-0012 §3.2:
# a clause without an instrument that can return otherwise is not a clause.


def _probe_module():
    """Load the dev-time probe by path (it lives in tools/, not in the wheel) —
    the same pattern tests/test_carrier_schema_rc205.py uses for the C codegen."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "tools" / "gen_carrier_examples_probe.py"
    assert path.exists(), f"missing carrier-example probe {path}"
    spec = importlib.util.spec_from_file_location("gen_carrier_examples_probe_rc363", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_curated_carrier_examples_are_preserved_by_regeneration() -> None:
    """Every hand-authored `_CURATED` row survives a regeneration BYTE-IDENTICAL,
    and the shipped file agrees with a fresh build (the idempotence half)."""
    from srmech.amsc._carrier_examples import CARRIER_EXAMPLES

    probe = _probe_module()
    assert probe._CURATED, (
        "gen_carrier_examples_probe._CURATED is empty — the mechanism that makes "
        "the module's 'hand-curated examples are preserved' claim TRUE has been "
        "removed. Either restore it or delete the claim.")

    built = probe.build_examples(quiet=True)
    assert built == CARRIER_EXAMPLES, (
        "srmech/amsc/_carrier_examples.py is out of date — re-run "
        "`python3 tools/gen_carrier_examples_probe.py`")

    for name, row in probe._CURATED.items():
        assert CARRIER_EXAMPLES.get(name) == row, (
            f"the curated example for {name!r} did not survive regeneration. "
            f"This is the rc363 defect reopening: main() rebuilds the file from "
            f"its dicts, so a curated row must live in _CURATED (applied LAST) "
            f"and nowhere else.")


def test_the_curated_layer_actually_overrides() -> None:
    """NON-VACUITY for the test above. Build the payload with the curated layer
    SUPPRESSED and require the result to differ on exactly the curated keys.

    Without this, `test_curated_carrier_examples_are_preserved_by_regeneration`
    would still pass if `_CURATED` were quietly reduced to rows the derived
    layers happen to reproduce — a preservation test that cannot observe the
    un-preserved state is not a measurement of preservation."""
    probe = _probe_module()
    with_curated = probe.build_examples(quiet=True)
    without = probe.build_examples(apply_curated=False, quiet=True)

    differing = {k for k in with_curated
                 if without.get(k) != with_curated[k]}
    assert differing == set(probe._CURATED), (
        f"suppressing the curated layer changed {sorted(differing)}, expected "
        f"exactly {sorted(probe._CURATED)} — a curated row that the derived "
        f"layers already reproduce is not curating anything, and one that "
        f"changes MORE than its own key means the layers are not last-wins.")


def test_the_curated_qalg_row_still_carries_its_witness() -> None:
    """The reason the Qalg row is curated rather than derived: its `yields` is a
    MEASUREMENT (an exact-arithmetic witness), not a repr. A derived row would
    print `Qalg(degree=2, ...)` and lose both facts."""
    from srmech.amsc._carrier_examples import CARRIER_EXAMPLES

    yields = CARRIER_EXAMPLES["Qalg"]["yields"]
    assert "as_rational() == Q(2, 1)" in yields, (
        "the Qalg example lost its exactness witness (α·α is exactly 2)")
    assert "is_rational() is False" in yields, (
        "the Qalg example lost its irrationality witness — the Tier-1/Tier-2 "
        "distinction srmech.music exists to make")
