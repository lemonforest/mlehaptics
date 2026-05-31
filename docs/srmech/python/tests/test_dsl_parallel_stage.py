"""v0.6.0rc11 — the DSL ``parallel`` discriminator + combinator classification.

``parallel_sector_dispatch`` is a 1→N fan-out combinator, NOT a plain
``value → value`` ``op=`` stage. rc11 gives it a first-class chain
discriminator (``chain.parallel_sectors`` / ``parallel_body=`` in a TOML
spec) — the same way loop/fold/reduce are special forms — and rejects it
as an ``op=`` stage with a guided error. These tests pin:

1. ``chain.parallel_sectors(body)`` runs the body across the ≤4 Klein-4
   sectors and yields the ordered list of per-sector results;
2. the TOML ``parallel_body=`` discriminator does the same;
3. ``n_sectors`` is honoured + range-checked at build time;
4. using the combinator as a plain ``op=`` stage raises a guided error
   (both the fluent ``.then()`` and the TOML ``op=`` paths);
5. ``cascade_op_kind`` classifies stage vs combinator.
"""

from __future__ import annotations

import pytest

from srmech.amsc.cascade import chiral_flip
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


# ── the parallel discriminator runs ─────────────────────────────────────

def test_parallel_sectors_fluent_returns_per_sector_list() -> None:
    out = chain("p").parallel_sectors("chiral_flip").run(_X)
    assert isinstance(out, list) and len(out) == 4
    # Sector 0 is the identity stream-transform, so its dual is just
    # body(x) = chiral_flip(x) = reversed input.
    assert list(out[0]) == chiral_flip(_X)
    # Every sector result is a length-preserving sequence.
    for sector in out:
        assert len(list(sector)) == len(_X)


def test_parallel_sectors_n_sectors_truncates() -> None:
    out = chain("p").parallel_sectors("chiral_flip", n_sectors=2).run(_X)
    assert isinstance(out, list) and len(out) == 2


def test_parallel_sectors_toml_discriminator() -> None:
    spec = (
        "[chain]\nname='p'\n\n"
        "[[stage]]\nparallel_body='chiral_flip'\nn_sectors=4\n"
    )
    out = run_toml_chain(spec, _X)
    assert isinstance(out, list) and len(out) == 4
    assert list(out[0]) == chiral_flip(_X)


def test_parallel_sectors_toml_default_n_sectors() -> None:
    spec = "[chain]\nname='p'\n\n[[stage]]\nparallel_body='chiral_flip'\n"
    out = run_toml_chain(spec, _X)
    assert isinstance(out, list) and len(out) == 4


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


# ── a stage op still chains normally (no regression) ────────────────────

def test_plain_stage_op_still_runs() -> None:
    out = chain("p").then("chiral_flip").run(_X)
    assert list(out) == chiral_flip(_X)
