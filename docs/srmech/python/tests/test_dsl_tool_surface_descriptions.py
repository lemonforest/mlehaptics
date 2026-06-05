"""v0.7.0rc15 — DSL surface description audit + anti-drift guard.

The LLM-facing tool descriptions for the cascade DSL (the
``srmech.dsl.run_toml_chain`` / ``srmech.dsl.list_catalog_ops`` ToolEntry
summaries) had drifted stale: they enumerated only the original "8 ops" and
referenced a "10-op cascade catalog", omitting the v0.7.0rc8 ``autocorrelation``
and miscounting the v0.6.0 ``parallel_sector_dispatch`` / ``kuramoto_step``. An
LLM reading those tools would believe fewer ops exist than actually ship.

These tests lock the descriptions to the LIVE cascade-catalog op set, so adding
a future op forces the summaries to be updated (or CI fails) rather than letting
the LLM-facing surface silently fall behind the runner.
"""
from srmech.dsl import list_cascade_ops
from srmech.amsc.tool_schema import get_tool_schema


def _dsl_summaries():
    entries = {e.name: e for e in get_tool_schema().tools}
    return (
        entries["srmech.dsl.run_toml_chain"].summary,
        entries["srmech.dsl.list_catalog_ops"].summary,
    )


def test_list_catalog_ops_summary_names_every_live_op():
    """The list_catalog_ops summary enumerates the op names an LLM may use —
    it must name EVERY op the runner can actually resolve, with none stale."""
    ops = list_cascade_ops()
    _run_summ, list_summ = _dsl_summaries()
    missing = [name for name in ops if name not in list_summ]
    assert not missing, (
        "srmech.dsl.list_catalog_ops summary omits live cascade ops "
        f"{missing} — update the op list in "
        "srmech.amsc.tool_schema._register_dsl_tools so the LLM-facing "
        "description stays in lockstep with the runner."
    )


def test_dsl_summaries_reference_live_op_count():
    """Both DSL ToolEntry summaries cite the current op count, not a stale
    one (pre-rc15 they said '8 ops' / '10-op' when 11 ship)."""
    n = len(list_cascade_ops())
    run_summ, list_summ = _dsl_summaries()
    assert f"{n} ops" in list_summ, (
        f"list_catalog_ops summary should cite the live count '{n} ops'"
    )
    assert f"{n}-op" in run_summ, (
        f"run_toml_chain summary should cite the live '{n}-op cascade catalog'"
    )


def test_dsl_summaries_have_no_stale_undercount():
    """Belt-and-braces: the specific stale phrases this rc removed must not
    reappear (the '8 ops:' op-list and the '10-op' / '10 cascade-catalog'
    counts that predate autocorrelation + the parallel/kuramoto ops)."""
    run_summ, list_summ = _dsl_summaries()
    both = run_summ + "\n" + list_summ
    for stale in ("8 ops:", "10-op", "10 cascade-catalog"):
        assert stale not in both, (
            f"stale DSL op-count phrase {stale!r} reappeared in a DSL "
            "ToolEntry summary"
        )
