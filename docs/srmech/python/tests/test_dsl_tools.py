"""Tests for the v0.5.0rc12 declarative DSL ToolEntry surface.

The rc8 cascade DSL (``srmech.dsl.*``) is a fluent builder
(``chain().then(...).loop(...)``) — not LLM-tool-ergonomic, since a
single tool call can't chain methods. rc12 exposes the *declarative*
surface as two MCP / Anthropic ToolEntries so an LLM composes AND runs a
cascade in one call:

* ``srmech.dsl.run_toml_chain(spec, input_value)`` — author an inline
  TOML chain spec + run it atomically.
* ``srmech.dsl.list_catalog_ops()`` — enumerate the 8 cascade-catalog
  ops + their A–N class + purpose.

Coverage:

* Both tools register after ``warmup_all()`` (regardless of entry-path).
* ``run_toml_chain`` is one-shot callable THROUGH
  ``srmech.mcp._tools.invoke_tool`` (the end-to-end proof) with real
  1-op + 2-op specs, returning the correct result (NOT an error).
* ``list_catalog_ops`` returns the 8 catalog ops with class + purpose.
* The rc10 property-key validity ratchet + rc11 describe guards continue
  to hold for the new dsl entries (no leaked varargs sigil; clean keys).
"""

from __future__ import annotations

import re

import pytest

import srmech  # noqa: F401
from srmech.amsc.tool_schema import get_tool_schema, warmup_all
from srmech.mcp._tools import invoke_tool, tool_entry_to_mcp_def

#: Anthropic / MCP property-key grammar (anchored) — same as test_mcp.py.
_ANTHROPIC_PROPERTY_KEY_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,64}$")

#: The two declarative DSL ToolEntry names registered in rc12.
_DSL_TOOL_NAMES = (
    "srmech.dsl.run_toml_chain",
    "srmech.dsl.list_catalog_ops",
)

#: The 11 cascade-catalog ops a chain spec may reference (rc12 catalog
#: of 8 lean-ISA atoms/composites + the v0.6.0rc10 pair
#: parallel_sector_dispatch + kuramoto_step + the v0.7.0rc8
#: autocorrelation Class-L primitive).
_EXPECTED_CATALOG_OPS = {
    "autocorrelation",
    "best_rational_signed",
    "chiral_dual",
    "chiral_flip",
    "cyclic_gcd",
    "kuramoto_step",
    "magnitude",
    "net_chirality",
    "octonion_dft",
    "parallel_sector_dispatch",
    "pin_slot_at_zero",
    "quaternion_dft",
    "reorient",
}


# ──────────────────────────────────────────────────────────────────────
# Registration
# ──────────────────────────────────────────────────────────────────────


def test_dsl_tools_registered() -> None:
    """After ``warmup_all()``, both declarative DSL tools appear in the
    tool schema (so MCP / Anthropic consumers can discover them)."""
    warmup_all()  # idempotent; guarantees registration regardless of path
    names = {e.name for e in get_tool_schema().tools}
    for tool_name in _DSL_TOOL_NAMES:
        assert tool_name in names, (
            f"{tool_name} missing from tool schema after warmup_all() "
            f"(v0.5.0rc12 DSL surface voxel)"
        )


def test_dsl_tools_owner_and_category() -> None:
    """The DSL tools are srmech-owned, category 'dsl'."""
    warmup_all()
    schema = get_tool_schema()
    for tool_name in _DSL_TOOL_NAMES:
        entry = schema.lookup(tool_name)
        assert entry is not None, f"{tool_name} not registered"
        assert entry.owner == "srmech"
        assert entry.category == "dsl"
        # rc12 must be cited in the summary so the catalog is honest
        # about which voxel shipped each tool.
        assert "rc12" in entry.summary


# ──────────────────────────────────────────────────────────────────────
# End-to-end one-shot invocation (the load-bearing proof)
# ──────────────────────────────────────────────────────────────────────


def test_dsl_run_toml_chain_via_invoke_tool() -> None:
    """``srmech.dsl.run_toml_chain`` is one-shot callable THROUGH
    ``invoke_tool`` with a real TOML chain spec + input, returning the
    correct result (NOT an error).

    This is the end-to-end proof the tool is one-shot callable — the
    exact path an MCP / Anthropic client takes. A 1-op ``chiral_flip``
    chain reverses the input sequence.
    """
    spec = (
        "[chain]\n"
        'name = "rc12-demo"\n'
        "\n"
        "[[stage]]\n"
        'op = "chiral_flip"\n'
    )
    result = invoke_tool(
        "srmech.dsl.run_toml_chain",
        {"spec": spec, "input_value": [1, 2, 3, 4]},
    )
    # chiral_flip is Class C orientation reversal: seq[::-1].
    assert result == [4, 3, 2, 1], (
        f"run_toml_chain returned {result!r}; expected [4, 3, 2, 1] "
        f"(a 1-op chiral_flip chain). A wrong / error result means the "
        f"tool is not one-shot callable."
    )


def test_dsl_run_toml_chain_two_op_reduce_via_invoke_tool() -> None:
    """A 2nd real spec through ``invoke_tool``: a ``reduce`` over
    ``cyclic_gcd`` (Class I) collapses a sequence to its gcd."""
    spec = (
        "[chain]\n"
        'name = "rc12-gcd"\n'
        "\n"
        "[[stage]]\n"
        'reduce_op = "cyclic_gcd"\n'
    )
    result = invoke_tool(
        "srmech.dsl.run_toml_chain",
        {"spec": spec, "input_value": [12, 8, 4]},
    )
    assert result == 4, (
        f"run_toml_chain reduce(cyclic_gcd, [12, 8, 4]) returned "
        f"{result!r}; expected 4 (gcd)."
    )


def test_dsl_run_toml_chain_scalar_input_via_invoke_tool() -> None:
    """A scalar input through ``invoke_tool``: ``magnitude`` (Class K
    pin-slot magnitude) of a negative float — cascade-honest |x|."""
    spec = (
        "[chain]\n"
        'name = "rc12-mag"\n'
        "\n"
        "[[stage]]\n"
        'op = "magnitude"\n'
    )
    result = invoke_tool(
        "srmech.dsl.run_toml_chain",
        {"spec": spec, "input_value": -3.14},
    )
    assert result == pytest.approx(3.14), (
        f"run_toml_chain magnitude(-3.14) returned {result!r}; "
        f"expected 3.14."
    )


def test_dsl_run_toml_chain_unknown_op_raises() -> None:
    """An unknown cascade op name surfaces as an error (the catalog is
    the SSoT — ``then('nope')`` is rejected). The dispatcher propagates
    the ValueError so the MCP / Anthropic layer can render it."""
    spec = (
        "[chain]\n"
        'name = "rc12-bad"\n'
        "\n"
        "[[stage]]\n"
        'op = "no_such_cascade_op"\n'
    )
    with pytest.raises(Exception):
        invoke_tool(
            "srmech.dsl.run_toml_chain",
            {"spec": spec, "input_value": [1, 2, 3]},
        )


# ──────────────────────────────────────────────────────────────────────
# list_catalog_ops
# ──────────────────────────────────────────────────────────────────────


def test_dsl_list_catalog_ops() -> None:
    """``srmech.dsl.list_catalog_ops`` returns the 11 catalog ops, each
    with a name + A–N class + purpose, sourced from the on-disk
    descriptors."""
    result = invoke_tool("srmech.dsl.list_catalog_ops", {})
    assert isinstance(result, list)
    names = {rec["name"] for rec in result}
    assert names == _EXPECTED_CATALOG_OPS, (
        f"list_catalog_ops returned {sorted(names)}; expected the 11 "
        f"cascade-catalog ops {sorted(_EXPECTED_CATALOG_OPS)}"
    )
    # Each record carries class + purpose + kind + provenance, and
    # class/purpose are non-empty for the real catalog descriptors. The
    # shipped ops are all A-tier (provenance="srmech"); a bring-your-own
    # registered op would be "user" (F289 D2 / v0.7.0rc6).
    for rec in result:
        assert set(rec.keys()) == {"name", "class", "purpose", "kind", "provenance"}
        assert rec["class"], f"{rec['name']} has empty class composition"
        assert rec["purpose"], f"{rec['name']} has empty purpose"
        assert rec["kind"] in ("stage", "combinator"), (
            f"{rec['name']} has unexpected kind {rec['kind']!r}"
        )
        assert rec["provenance"] == "srmech", (
            f"{rec['name']} is a shipped op; expected provenance 'srmech', "
            f"got {rec['provenance']!r}"
        )
    # Sorted ascending by name (so an LLM gets a stable enumeration).
    assert [r["name"] for r in result] == sorted(names)
    # The DSL role is surfaced honestly: the higher-order fan-out is a
    # 'combinator' (not a plain `op=` stage); everything else is a 'stage'.
    by_kind = {rec["name"]: rec["kind"] for rec in result}
    assert by_kind["parallel_sector_dispatch"] == "combinator", (
        "parallel_sector_dispatch must be advertised as a combinator so a "
        "CLI/LLM user knows to drive it via the `parallel` discriminator, "
        "not as a plain `op=` chain stage"
    )
    assert by_kind["kuramoto_step"] == "stage"
    assert by_kind["chiral_flip"] == "stage"


def test_dsl_list_catalog_ops_classes_match_known() -> None:
    """Spot-check a few op -> A–N class mappings against the known
    cascade vocabulary (chiral_flip = C; cyclic_gcd = I; magnitude =
    K)."""
    result = invoke_tool("srmech.dsl.list_catalog_ops", {})
    by_name = {rec["name"]: rec["class"] for rec in result}
    assert by_name["chiral_flip"] == "C"
    assert by_name["cyclic_gcd"] == "I"
    assert by_name["magnitude"] == "K"


# ──────────────────────────────────────────────────────────────────────
# rc10 property-key ratchet + rc11 clean-conversion guards (now also
# guarding the dsl entries)
# ──────────────────────────────────────────────────────────────────────


def test_dsl_tool_property_keys_match_anthropic_grammar() -> None:
    """Every ``inputSchema.properties`` KEY of the dsl tools matches
    Anthropic's ``^[a-zA-Z0-9_.-]{1,64}$`` grammar (no leaked varargs
    sigil) — the rc10 ratchet applied to the rc12 entries.

    ``run_toml_chain`` uses plain keyword params (``spec`` /
    ``input_value``); ``list_catalog_ops`` has none. Both are picked so
    ``invoke_tool``'s ``fn(**coerced)`` calls them directly (no
    VAR_POSITIONAL unpack)."""
    warmup_all()
    schema = get_tool_schema()
    for tool_name in _DSL_TOOL_NAMES:
        entry = schema.lookup(tool_name)
        assert entry is not None
        mcp_def = tool_entry_to_mcp_def(entry)
        props = mcp_def["inputSchema"]["properties"]
        for key in props:
            assert "*" not in key and _ANTHROPIC_PROPERTY_KEY_RE.match(key), (
                f"{tool_name}: property key {key!r} violates the "
                f"Anthropic grammar (would 400 the whole catalog)"
            )
        # required keys reference real properties (lockstep guard).
        for req in mcp_def["inputSchema"]["required"]:
            assert req in props


def test_dsl_run_toml_chain_param_names_match_callable() -> None:
    """The ToolEntry param names MUST match the resolved callable's
    keyword params, or ``invoke_tool``'s ``fn(**coerced)`` raises a
    TypeError. Guards the rc10 lesson: schema names == call signature."""
    import inspect

    from srmech.dsl import run_toml_chain

    entry = get_tool_schema().lookup("srmech.dsl.run_toml_chain")
    assert entry is not None
    schema_param_names = {p.name for p in entry.parameters}
    sig = inspect.signature(run_toml_chain)
    callable_param_names = set(sig.parameters)
    # No VAR_POSITIONAL / VAR_KEYWORD — purely keyword-callable.
    assert not any(
        p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        for p in sig.parameters.values()
    ), "run_toml_chain should be plain-keyword callable (no *args/**kw)"
    assert schema_param_names == callable_param_names, (
        f"ToolEntry params {sorted(schema_param_names)} != callable "
        f"params {sorted(callable_param_names)}; invoke_tool's "
        f"fn(**coerced) would raise"
    )
