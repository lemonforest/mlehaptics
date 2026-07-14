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

# Monotone floor: the count of tools whose EXAMPLE is a real executed
# input->output (vs an honest signature snippet). Curation grows this over
# subsequent rcs — it may rise, never fall.
_MIN_EXECUTED_EXAMPLES = 90


def _srmech_tools():
    return [t for t in get_tool_schema().tools if t.owner == "srmech"]


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
    """An example is either a real executed {input, output} OR an honest
    {call} usage snippet — never a fabricated output without an input."""
    bad = []
    for t in _srmech_tools():
        ex = t.example
        if not ex:
            continue
        keys = set(ex)
        if keys == {"input", "output"} or keys == {"call"}:
            continue
        # sha256_bytes-style hand examples are {input, output}; snippet is {call}.
        if "output" in keys and "input" not in keys:
            bad.append(t.name)
    assert not bad, f"examples with an output but no input (fabricated?): {bad[:5]}"


def test_executed_example_floor_is_monotone() -> None:
    n = sum(1 for t in _srmech_tools()
            if isinstance(t.example, dict) and "output" in t.example
            and "input" in t.example)
    assert n >= _MIN_EXECUTED_EXAMPLES, (
        f"only {n} tools have a real executed input->output example; the rc240 "
        f"floor is {_MIN_EXECUTED_EXAMPLES} (curation grows this — never lower it)"
    )


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
