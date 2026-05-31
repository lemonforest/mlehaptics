"""v0.6.0rc11/rc12 — the DSL ``parallel`` discriminator + composability.

``parallel_sector_dispatch`` is a 1→N fan-out combinator, NOT a plain
``value → value`` ``op=`` stage. rc11 gave it a first-class chain
discriminator (``chain.parallel_sectors`` / ``parallel_body=`` in a TOML
spec) — the same way loop/fold/reduce are special forms — and rejects it
as an ``op=`` stage with a guided error. rc12 makes the stage COMPOSABLE:
a ``combine=`` recombine (default ``"bundle"``) folds the ≤4 sector
results into ONE value, so the stage is ``stream → stream`` and chains /
nests like any other; ``combine=None`` keeps the terminal per-sector list
(guarded against chaining-past). These tests pin:

1. ``chain.parallel_sectors(body)`` recombines by default → a single
   composable stream, and CHAINS (parallel → then, parallel → parallel);
2. ``combine=None`` yields the ordered per-sector list (the fan-out),
   and is a TERMINAL stage (chaining past it raises a guided error);
3. the TOML ``parallel_body=`` discriminator + ``combine=`` do the same;
4. ``n_sectors`` is honoured + range-checked at build time;
5. using the combinator as a plain ``op=`` stage raises a guided error
   (both the fluent ``.then()`` and the TOML ``op=`` paths);
6. ``cascade_op_kind`` classifies stage vs combinator;
7. ``sectorize`` nests a sector-dispatch inside another (rc12 §11.3).
"""

from __future__ import annotations

import pytest

from srmech.amsc.cascade import (
    chiral_flip,
    parallel_sector_dispatch,
    sectorize,
)
from srmech.dsl import chain, run_toml_chain
from srmech.dsl._catalog import cascade_op_kind

# A small even-length real input (chiral_flip = reverse).
_X = [0.1, 0.2, 0.3, 0.4]


# ── kind classification ────────────────────────────────────────────────

def test_cascade_op_kind_combinator_vs_stage() -> None:
    assert cascade_op_kind("parallel_sector_dispatch") == "combinator"
    assert cascade_op_kind("kuramoto_step") == "stage"
    assert cascade_op_kind("chiral_flip") == "stage"
    # Unknown name defers to "stage" (lookup_cascade_op owns the real gate).
    assert cascade_op_kind("does_not_exist") == "stage"


# ── rc12 default: recombine → single composable stream ──────────────────

def test_parallel_sectors_default_combine_is_single_stream() -> None:
    """The default (combine='bundle') recombines the ≤4 sectors into ONE
    length-preserving stream — NOT the per-sector list."""
    out = chain("p").parallel_sectors("chiral_flip").run(_X)
    # A single flat stream the length of the input (the bundle), not a
    # list-of-4 sequences.
    assert len(list(out)) == len(_X)
    assert not isinstance(out[0], (list, tuple))


def test_parallel_sectors_default_chains_then() -> None:
    """A default parallel stage is stream→stream, so a following .then()
    consumes it (rc11 crashed here)."""
    out = chain("p").parallel_sectors("chiral_flip").then("chiral_flip").run(_X)
    assert len(list(out)) == len(_X)


def test_parallel_sectors_chains_parallel_after_parallel() -> None:
    """rc11 regression: chain a parallel stage AFTER a parallel stage. This
    raised ``TypeError: bad operand type for unary -: 'list'`` in rc11
    (the 4-way splay did not carry through a chained cascade). rc12: it
    runs — each stage recombines, so the next sees a flat stream."""
    out = (
        chain("settle")
        .parallel_sectors("chiral_flip")
        .parallel_sectors("chiral_flip")
        .run(_X)
    )
    assert len(list(out)) == len(_X)


def test_parallel_sectors_combine_variants() -> None:
    """Each named reducer yields a single composable value of the right
    shape; 'sector0' is value-transparent (== body(x))."""
    s0 = chain("p").parallel_sectors("chiral_flip", combine="sector0").run(_X)
    assert list(s0) == chiral_flip(_X)
    mean = chain("p").parallel_sectors("chiral_flip", combine="mean").run(_X)
    assert len(list(mean)) == len(_X)
    concat = chain("p").parallel_sectors("chiral_flip", combine="concat").run(_X)
    assert len(list(concat)) == 4 * len(_X)


# ── combine=None: the terminal per-sector fan-out ───────────────────────

def test_parallel_sectors_none_returns_per_sector_list() -> None:
    out = chain("p").parallel_sectors("chiral_flip", combine=None).run(_X)
    assert isinstance(out, list) and len(out) == 4
    # Sector 0 is the identity stream-transform, so its dual is just
    # body(x) = chiral_flip(x) = reversed input.
    assert list(out[0]) == chiral_flip(_X)
    for sector in out:
        assert len(list(sector)) == len(_X)


def test_parallel_sectors_none_n_sectors_truncates() -> None:
    out = chain("p").parallel_sectors(
        "chiral_flip", n_sectors=2, combine=None,
    ).run(_X)
    assert isinstance(out, list) and len(out) == 2


def test_parallel_sectors_none_is_terminal() -> None:
    """A non-combining parallel stage is terminal — chaining past it raises
    a guided error pointing at combine= (the rc12 composability guard)."""
    ch = chain("p").parallel_sectors("chiral_flip", combine=None)
    with pytest.raises(ValueError, match="combine|terminal|fan-out"):
        ch.then("chiral_flip")
    # Also guards loop/fold/reduce/parallel after the terminal stage.
    with pytest.raises(ValueError, match="combine|terminal|fan-out"):
        chain("p").parallel_sectors("chiral_flip", combine=None).reduce(
            "cyclic_gcd"
        )


# ── the TOML discriminator ──────────────────────────────────────────────

def test_parallel_sectors_toml_default_combine_is_stream() -> None:
    spec = (
        "[chain]\nname='p'\n\n"
        "[[stage]]\nparallel_body='chiral_flip'\nn_sectors=4\n"
    )
    out = run_toml_chain(spec, _X)
    assert len(list(out)) == len(_X)
    assert not isinstance(out[0], (list, tuple))


def test_parallel_sectors_toml_combine_none_sentinel() -> None:
    """The TOML sentinel ``combine = "none"`` maps to Python None → the
    per-sector list."""
    spec = (
        "[chain]\nname='p'\n\n"
        "[[stage]]\nparallel_body='chiral_flip'\ncombine='none'\n"
    )
    out = run_toml_chain(spec, _X)
    assert isinstance(out, list) and len(out) == 4
    assert list(out[0]) == chiral_flip(_X)


def test_parallel_sectors_toml_chains() -> None:
    """Two combining parallel stages in TOML chain (the rc12 settling-loop
    shape)."""
    spec = (
        "[chain]\nname='settle'\n\n"
        "[[stage]]\nparallel_body='chiral_flip'\n\n"
        "[[stage]]\nparallel_body='chiral_flip'\n"
    )
    out = run_toml_chain(spec, _X)
    assert len(list(out)) == len(_X)


# ── range checks (build-time, fail-fast) ────────────────────────────────

@pytest.mark.parametrize("bad", [0, 5, 8, -1])
def test_parallel_sectors_n_sectors_out_of_range_raises(bad: int) -> None:
    with pytest.raises(ValueError, match="1..4|triality"):
        chain("p").parallel_sectors("chiral_flip", n_sectors=bad)


# ── the combinator-as-op guard (the rc11 Gap-1 fix) ─────────────────────

def test_combinator_rejected_as_fluent_then_stage() -> None:
    with pytest.raises(ValueError, match="combinator|parallel"):
        chain("p").then("parallel_sector_dispatch")


def test_combinator_rejected_as_toml_op_stage() -> None:
    spec = "[chain]\nname='p'\n\n[[stage]]\nop='parallel_sector_dispatch'\n"
    with pytest.raises(ValueError, match="combinator|parallel"):
        run_toml_chain(spec, _X)


# ── rc12 §11.3: sectorize nests a dispatch inside another ───────────────

def test_sectorize_nests_inside_dispatch() -> None:
    """A sectorized body returns a single flat stream, so it composes as the
    body of an OUTER parallel_sector_dispatch — the 4-way splay carries
    through (rc11 raised ``unary -: 'str'``/``'list'`` here)."""
    inner = sectorize(chiral_flip, combine="bundle")
    result = parallel_sector_dispatch(inner, _X, combine="bundle")
    assert result["combined"] is not None
    assert len(list(result["combined"])) == len(_X)


def test_sectorize_rejects_combine_none() -> None:
    with pytest.raises(ValueError, match="single value|combine"):
        sectorize(chiral_flip, combine=None)


# ── a stage op still chains normally (no regression) ────────────────────

def test_plain_stage_op_still_runs() -> None:
    out = chain("p").then("chiral_flip").run(_X)
    assert list(out) == chiral_flip(_X)
