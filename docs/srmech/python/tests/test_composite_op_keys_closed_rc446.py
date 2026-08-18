"""`#T1142` / gh #1653 — ``_COMPOSITE_OP_KEYS`` must be CLOSED against the grammar.

THE DEFECT (live rc? → rc445, confirmed by planted failure with controls).
``srmech/dsl/_catalog.py`` declared::

    _COMPOSITE_OP_KEYS = ("op", "fold_op", "reduce_op", "parallel_body")

``map_op`` was missing. That is not one missing check — it silently lapsed BOTH
composite load-time guarantees at once, because :func:`_catalog._composite_op_refs`
feeds *both* unknown-op validation *and* cycle detection from that one tuple. So a
composite whose ``map_op`` named a non-existent op loaded clean, and a cycle routed
through a ``map_op`` was undetectable.

WHY A "add map_op" TEST WOULD BE THE WRONG FIX
----------------------------------------------
Asserting ``"map_op" in _COMPOSITE_OP_KEYS`` gates the bug we already found and
nothing else. The NEXT op-naming discriminator would lapse exactly the same way.
So the gate here is a CLOSURE invariant against the grammar's own single source of
truth, ``_toml_chain._RESERVED_STAGE_KEYS``:

    _RESERVED_STAGE_KEYS  ==  _COMPOSITE_OP_KEYS  ∪  _NON_OP_RESERVED

Adding a reserved key to the grammar without classifying it as op-naming or not
FAILS this file. That is the property that could not rot; a membership test is.

⚠️ WHAT THIS CANNOT DETECT. It is closed against the *reserved-key* SSoT, so a
discriminator introduced WITHOUT being added to ``_RESERVED_STAGE_KEYS`` is
invisible here — the closure is only as good as that tuple's completeness. The
planted-failure tests below are the independent check: they exercise the actual
guarantees rather than the bookkeeping.
"""
from __future__ import annotations

import pytest

from srmech.dsl import _catalog as _cat
from srmech.dsl import _toml_chain as _tc

#: Reserved stage keys that do NOT name a cascade op. Every reserved key must be
#: here or in ``_COMPOSITE_OP_KEYS`` — that partition is the whole gate.
_NON_OP_RESERVED = frozenset({
    "loop_n",      # an iteration count
    "sub_chain",   # a nested stage list, walked separately by _composite_op_refs
    "fold_init",   # a seed value
    "fold_args",   # kwarg names for a kw-named fold
    "n_sectors",   # a sector count
    "combine",     # a recombine MODE name, not an op name
})


def test_composite_op_keys_partition_the_reserved_keys():
    """THE CLOSURE INVARIANT. A new reserved key must be classified, not ignored."""
    op_keys = frozenset(_cat._COMPOSITE_OP_KEYS)
    reserved = frozenset(_tc._RESERVED_STAGE_KEYS)

    phantom = sorted(op_keys - reserved)
    assert not phantom, (
        "_COMPOSITE_OP_KEYS names %s, which the grammar does not reserve. Either "
        "the grammar dropped a discriminator or this tuple has a typo — a phantom "
        "key validates nothing and hides the fact that nothing is validated."
        % phantom)

    unclassified = sorted(reserved - op_keys - _NON_OP_RESERVED)
    assert not unclassified, (
        "the grammar reserves %s but this file classifies them neither as "
        "op-naming (_COMPOSITE_OP_KEYS) nor as non-op (_NON_OP_RESERVED).\n"
        "If a key NAMES A CASCADE OP it MUST go in _COMPOSITE_OP_KEYS, or "
        "unknown-op validation AND cycle detection both lapse for it silently — "
        "that is exactly `#T1142`." % unclassified)

    overlap = sorted(op_keys & _NON_OP_RESERVED)
    assert not overlap, "%s is classified both ways" % overlap


def test_map_op_is_gated():
    """The specific `#T1142` regression, kept alongside the closure invariant."""
    assert "map_op" in _cat._COMPOSITE_OP_KEYS, (
        "map_op is absent again — both composite load-time guarantees have "
        "lapsed for it. See `#T1142`.")


# ── planted failures: exercise the GUARANTEES, not the bookkeeping ───────────
#
# Each defective composite is planted twice: once under ``map_op`` (the key that
# was missing) and once under ``fold_op`` (a key that was always covered). The
# COVERED-KEY row is the control — without it, "map_op raises" would not show
# that the guarantee is what fires, only that something did.

def _catalog_with(stage_key, ref, extra=None):
    """A minimal two-op catalog whose composite references ``ref`` via ``stage_key``."""
    stage = {stage_key: ref}
    if extra:
        stage.update(extra)
    return {
        "probe": {"_source": "<planted>", "composite": {"stage": [stage]}},
        "magnitude": {"_source": "<planted>"},
    }


@pytest.mark.parametrize("stage_key", ["map_op", "fold_op"])
def test_unknown_op_is_caught_under_every_op_naming_key(stage_key):
    """Guarantee 1 — unknown-op validation. Fires for map_op AND the control."""
    catalog = _catalog_with(stage_key, "no_such_op_anywhere")
    with pytest.raises(ValueError, match="unknown op"):
        _cat._validate_composite("probe", catalog, ())


@pytest.mark.parametrize("stage_key", ["map_op", "fold_op"])
def test_cycle_is_caught_under_every_op_naming_key(stage_key):
    """Guarantee 2 — cycle detection. Fires for map_op AND the control."""
    catalog = {
        "a": {"_source": "<planted>", "composite": {"stage": [{stage_key: "b"}]}},
        "b": {"_source": "<planted>", "composite": {"stage": [{"op": "a"}]}},
    }
    with pytest.raises(ValueError, match="cycle"):
        _cat._validate_composite("a", catalog, ())


@pytest.mark.parametrize("stage_key", ["map_op", "fold_op"])
def test_a_VALID_reference_still_loads(stage_key):
    """The positive control. A validator that rejects everything is not a fix."""
    _cat._validate_composite("probe", _catalog_with(stage_key, "magnitude"), ())


def test_the_shipped_catalog_still_loads():
    """Widening the tuple must not reject anything srmech actually ships."""
    catalog = _cat.load_catalog()
    assert catalog, "catalog is empty — the loader broke"
    for name in sorted(catalog):
        _cat._validate_composite(name, catalog, ())
