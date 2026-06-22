"""rc30 CLEANUP + BUGFIX pinning tests (numpy-free).

Three tracks, all asserted here:

(A) BUGFIX — ``rbs_lm.substrate.sim_k4_batch`` returns plain Python ``float``
    (not the exact ``Q`` of ``hdc.klein4_similarity``), and the vocab-ranking
    order is unchanged (``klein4_similarity == match_count / D`` exactly, so the
    integer-count → one-float-division path ranks identically).

(B + C) CLEANUP — every dead Python symbol + Phase-8 profiling stub deleted in
    rc30 is GONE (``not hasattr(module, name)``), and the profiling stubs +
    ``ProfilingNotImplementedError`` are no longer importable from
    ``srmech.signal_processing``.

The file is numpy-free per
``[[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]`` — it
imports srmech surfaces + uses stdlib only.
"""
from __future__ import annotations

import importlib

import pytest

from srmech.amsc import hdc
from srmech.rbs_lm import encode_word_k4, sim_k4_batch

_D = 256
_HEX_CHARS = 12


# ──────────────────────────────────────────────────────────────────────
# (A) sim_k4_batch float hot-path
# ──────────────────────────────────────────────────────────────────────


def test_sim_k4_batch_returns_plain_float_not_q():
    """Every element is a built-in ``float`` — NOT the exact ``Q`` rational
    that ``hdc.klein4_similarity`` returns (the rc30 hot-path fix)."""
    q = encode_word_k4("cat", D=_D, sector=0, hex_chars=_HEX_CHARS)
    cands = [
        encode_word_k4("cat", D=_D, sector=0, hex_chars=_HEX_CHARS),
        encode_word_k4("dog", D=_D, sector=0, hex_chars=_HEX_CHARS),
        encode_word_k4("sat", D=_D, sector=0, hex_chars=_HEX_CHARS),
    ]
    sims = sim_k4_batch(q, cands)
    assert len(sims) == 3
    for s in sims:
        assert type(s) is float, f"expected plain float, got {type(s).__name__}"
    # Self-similarity is exactly 1.0; others lie in [0, 1).
    assert sims[0] == 1.0
    assert all(0.0 <= s <= 1.0 for s in sims)


def test_sim_k4_batch_ranking_matches_exact_similarity():
    """The float ranking order is IDENTICAL to the exact-``Q`` similarity order
    (``klein4_similarity == match_count / D`` exactly), so the argmax/sort the
    inference path runs is unchanged."""
    q = encode_word_k4("cat", D=_D, sector=0, hex_chars=_HEX_CHARS)
    words = ["cat", "dog", "sat", "the", "mat"]
    cands = [encode_word_k4(w, D=_D, sector=0, hex_chars=_HEX_CHARS) for w in words]

    floats = sim_k4_batch(q, cands)
    exact = [hdc.klein4_similarity(q, c) for c in cands]  # exact Q

    # Same value (float == float(Q)) and same argsort.
    assert floats == [float(e) for e in exact]
    order_float = sorted(range(len(cands)), key=lambda i: floats[i], reverse=True)
    order_exact = sorted(range(len(cands)), key=lambda i: exact[i], reverse=True)
    assert order_float == order_exact
    # The self-match ("cat") ranks first.
    assert words[order_float[0]] == "cat"


# ──────────────────────────────────────────────────────────────────────
# (B) deleted private helpers are gone from their modules
# ──────────────────────────────────────────────────────────────────────

_DELETED = {
    "srmech.amsc.hdc": (
        "_as_klein4",
        "_klein4_chirality_duals",
        "_klein4_similarity_native",
    ),
    "srmech.amsc.mat": ("_flat_index",),  # Mat method (checked on the class below)
    "srmech.qm.so8": ("_mat_rows",),
    "srmech.amsc.rational": (
        "_principal_angle_anchor",
        "_q_scale2",
        "_q_pow2",
        "_rational_sqrt_midpoint",
        "_TRIG_FLOAT_ANCHOR_DEN",
    ),
    "srmech.amsc.laplacian": (
        "_vec_to_interleaved_cbuf",
        "_vec_from_interleaved_cbuf",
    ),
    "srmech.signal_processing.profiling": (
        "_time_one_call",
        "profile_op",
        "update_dispatch_table",
        "ProfilingNotImplementedError",
    ),
}


@pytest.mark.parametrize(
    "mod_name,sym",
    [(m, s) for m, syms in _DELETED.items() for s in syms],
)
def test_deleted_symbol_is_gone(mod_name, sym):
    mod = importlib.import_module(mod_name)
    assert not hasattr(mod, sym), (
        f"{mod_name}.{sym} should have been deleted in rc30 but is still present"
    )


def test_mat_flat_index_method_gone():
    """``Mat._flat_index`` was a dead method — gone from the class."""
    from srmech.amsc.mat import Mat
    assert not hasattr(Mat, "_flat_index")


def test_live_siblings_survive():
    """The live siblings the deletions sit next to are untouched."""
    assert hasattr(hdc, "_as_klein4_buf")          # live (the alias's target)
    assert hasattr(hdc, "_klein4_match_count_native")
    from srmech.amsc import laplacian
    assert hasattr(laplacian, "_mat_to_interleaved_cbuf")    # live Mat twins
    assert hasattr(laplacian, "_mat_from_interleaved_cbuf")
    from srmech.amsc import rational
    assert hasattr(rational, "_TRIG_FLOAT_TERMS")            # live sibling consts
    assert hasattr(rational, "_ATAN_FLOAT_TERMS")
    assert hasattr(rational, "pi_cascade_digits")            # live (stale ref fixed)


# ──────────────────────────────────────────────────────────────────────
# (C) the Phase-8 profiling stubs are no longer importable
# ──────────────────────────────────────────────────────────────────────


def test_profiling_stubs_not_importable_from_signal_processing():
    import srmech.signal_processing as sp
    for name in ("profile_op", "update_dispatch_table", "ProfilingNotImplementedError"):
        assert not hasattr(sp, name), (
            f"srmech.signal_processing.{name} should be deleted (no-stubs rule)"
        )
    # The surviving profiling surface still imports fine.
    from srmech.signal_processing import (  # noqa: F401
        ProfileCellKey,
        ProfileRecord,
        cell_grid,
        clear_records,
        iter_records,
        record_profile,
    )


def test_profiling_stubs_not_importable_directly():
    prof = importlib.import_module("srmech.signal_processing.profiling")
    for name in ("profile_op", "update_dispatch_table",
                 "ProfilingNotImplementedError", "_time_one_call"):
        assert not hasattr(prof, name)
    # __all__ no longer advertises any of them.
    advertised = set(getattr(prof, "__all__", ()))
    assert advertised.isdisjoint(
        {"profile_op", "update_dispatch_table", "ProfilingNotImplementedError"}
    )
