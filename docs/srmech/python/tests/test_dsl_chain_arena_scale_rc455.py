"""The ``srmech_dsl_chain_run`` arena, measured AT SCALE — v0.9.0rc455.

⚠️ WHAT WAS WRONG, AND WHY NOTHING COULD SEE IT.

MEASURED at rc454: ``chain().then('chiral_flip').run(xs)`` — a form shipped
since rc181 — silently stopped running in C above **165 int / 198 float
elements**. The C peer returned ``SRMECH_ERR_OVERFLOW``; ``Chain._run_native``
collapses any non-OK status to a native miss; the pure path then returned the
right answer. So the library gave correct results the whole time and the C
projection had quietly switched itself off, on ordinary inputs, for 273 rcs.

No gate could see it for one reason: **the entire pre-rc455 C-parity proof
corpus for this runner ran at <= 18 elements** (the largest literal sequence in
``test_dsl_chain_c_rc181.py``). A parity corpus that lives entirely below a
cliff cannot see the cliff, and a defect whose only symptom is "the fast path
stopped being taken" produces no red anywhere.

THE CAUSE was a writer reserve of ``16384 + 8*(chain_len + input_len)``, split
in half between the JSON builder and the write scratch — 4 bytes of builder per
byte of INPUT, against ~137 bytes of builder per ~21.5-byte int element. The
16384 constant paid the difference for ~165 elements and then ran out.

THE FIX derives the emit-scratch and builder reserves from the OUTPUT VALUE
(``dsl_out_reserve``), and the write scratch from the BUILT tree. Nothing in the
sizing reads ``input_len`` any more.

WHY THE TABLE BELOW IS SHAPED THE WAY IT IS. A single-size check is satisfied by
any large enough constant, and a constant rots the instant a form's output grows.
So the gate measures the arena a run ACTUALLY REQUIRES, by bisection, across
three orders of magnitude (16 / 256 / 4096 / 65536 elements) crossed with
``n_sectors`` in {1, 4} and ``combine`` in {concat, none} — and asserts:

  (1) the per-output-element ratio stays FLAT (a fixed pad cannot do that);
  (2) the MARGINAL cost of the extra output elements a 4-sector fan-out
      produces is a CONSTANT ~371 bytes each at every size — the decisive
      anti-constant measurement, because an input-derived reserve tuned on the
      ``n_sectors=1`` rows under-provisions the ``n_sectors=4`` rows by 4x, and
      a fixed pad makes this marginal rate decay as 1/n;
  (3) each measured requirement is BRACKETED — the arena one byte-band below it
      genuinely FAILS — so "it fits" is a measurement and not a tautology;
  (4) the requirement is under what ``srmech_dsl_chain_run_arena_bytes`` hands
      the caller, which is what makes the SHIPPED path take C.

COST NOTE: the 65536-element rows allocate a few hundred MiB transiently. That
is the size of the thing being measured; a scale gate that only runs at sizes
which are cheap is the gate that was missing.

numpy-free (stdlib ctypes/json only).
"""
from __future__ import annotations

import ctypes
import json

import pytest

from srmech import _native
from srmech.dsl import chain
from srmech.dsl._chain import _NATIVE_MISS, _value_to_desc

_HAS = (
    _native.HAS_NATIVE
    and _native.LIB is not None
    and hasattr(_native.LIB, "srmech_dsl_chain_run")
    and hasattr(_native.LIB, "srmech_dsl_chain_run_arena_bytes")
)
_needs_native = pytest.mark.skipif(
    not _HAS, reason="native srmech_dsl_chain_run not present (pure-only build)"
)

#: The affine upper bound on the measured requirement, in bytes:
#: ``_BOUND_FIXED + _BOUND_PER_IN*in_elems + _BOUND_PER_OUT*out_elems``.
#: MEASURED at rc455 with 13-34% headroom on every row of the table below; it is
#: a CEIL, so it may be tightened but never loosened without a stated reason.
_BOUND_FIXED = 300_000
_BOUND_PER_IN = 3_400
_BOUND_PER_OUT = 450

#: The marginal bytes each EXTRA output element costs, measured as
#: ``(required(n_sectors=4) - required(n_sectors=1)) / (3 * n)``.
#:
#: ⚠️ THESE READINGS ARE HOST-DEPENDENT AND THE BAND IS WHAT SHIPS, not the
#: readings. ``required`` is a BISECTED bracket, not an exact figure: the search
#: stops within ~1.5% (``_TOL_DEN``), and the true boundary itself moves with
#: the pointer alignment ``ctypes.create_string_buffer`` happens to hand each
#: probe, which ``dcr_align`` then pads against. So a marginal quoted to four
#: significant figures asserts a precision the instrument does not have.
#: rc455 first recorded ``382.7 / 371.4 / 370.7 / 371.0`` with no predicate and
#: no caveat; an independent re-measurement got 370.66 at n=65536 (0.1% off,
#: immaterial to the band), and THIS host measures a different set again:
#:
#:   combine='concat'  399.44 (n=16)  365.16 (256)  365.96 (4096)  373.67 (65536)
#:   combine=None      399.44 (n=16)  365.16 (256)  362.44 (4096)  360.12 (65536)
#:
#: measured on WSL2 Linux gcc, ``libsrmech.so`` at ABI 24, 0.9.0rc454 tree.
#: Spread across all eight: 1.109x, against the 1.25x the flatness assertion
#: allows. The point the file makes survives any of these readings — a rate
#: that is FLAT is the property a padding constant cannot fake, and the exact
#: value is not load-bearing. Quote the band; re-measure before quoting a digit.
_MARGINAL_LO = 300
_MARGINAL_HI = 460

#: Bisection stops once the bracket is within ~1.5%, which keeps the 65536 rows
#: to ~7 probes instead of ~28 without weakening either side of the bracket.
_TOL_DEN = 64


def _payload(n_sectors, combine, values):
    stage = [{"parallel_body": "chiral_flip", "n_sectors": n_sectors,
              "combine": combine}]
    cj = json.dumps({"chain": {"name": "s"}, "stage": stage}).encode("utf-8")
    ij = json.dumps(_value_to_desc(values)).encode("utf-8")
    return cj, ij


def _run_ws(cj, ij, ws_bytes):
    """One C run into an arena of EXACTLY ``ws_bytes``. Returns the status."""
    lib = _native.LIB
    ws = (ctypes.c_char * ws_bytes)()
    out_cap = 64 * len(ij) + 65536
    out = (ctypes.c_char * out_cap)()
    out_len = ctypes.c_size_t()
    return lib.srmech_dsl_chain_run(cj, len(cj), ij, len(ij), ws, ws_bytes,
                                    out, out_cap, ctypes.byref(out_len))


def _bracket(cj, ij, hi):
    """Bisect for the smallest workable arena. Returns ``(fails_at, works_at)``.

    ``fails_at`` is a REAL failing probe, not an inferred one — it is what makes
    ``works_at`` a measurement of a boundary rather than of an upper bound.
    """
    assert _run_ws(cj, ij, hi) == _native.SRMECH_OK, (
        "the declared bound must itself work, or nothing below is measured"
    )
    lo = 1024
    assert _run_ws(cj, ij, lo) != _native.SRMECH_OK, "1 KiB must not suffice"
    while hi - lo > max(lo // _TOL_DEN, 1024):
        mid = (lo + hi) // 2
        if _run_ws(cj, ij, mid) == _native.SRMECH_OK:
            hi = mid
        else:
            lo = mid
    return lo, hi


def _bound(in_elems, out_elems):
    return (_BOUND_FIXED + _BOUND_PER_IN * in_elems
            + _BOUND_PER_OUT * out_elems)


def _rows(table):
    """The table in a deterministic order. ``sorted`` cannot be used directly:
    ``combine`` is ``None`` on half the rows and ``None < 'concat'`` raises."""
    return sorted(table.items(), key=lambda kv: (kv[0][0], kv[0][1],
                                                 str(kv[0][2])))


def _required(n, n_sectors, combine):
    """The measured minimum arena (within ~1.5%) for one table row."""
    values = list(range(n))
    cj, ij = _payload(n_sectors, combine, values)
    out_elems = n * n_sectors
    fails_at, works_at = _bracket(cj, ij, _bound(n, out_elems))
    return {"required": works_at, "fails_at": fails_at, "out_elems": out_elems,
            "arena_bytes": int(
                _native.LIB.srmech_dsl_chain_run_arena_bytes(len(cj), len(ij)))}


# ─────────────────────────────────────────────────────────────────────
# The direct cliff regression — the cheapest, most decisive row
# ─────────────────────────────────────────────────────────────────────


@_needs_native
@pytest.mark.parametrize("n", [16, 128, 165, 166, 167, 199, 256, 1024, 4096])
def test_shipped_path_still_runs_in_c_past_the_old_cliff(n):
    """With the arena Python actually ships, the C path RUNS — at every size.

    ⚠️ 165 / 166 and 198 / 199 are IN THIS LIST BY MEASUREMENT: they are the
    exact int and float boundaries rc454 fell off. Sizes on both sides of a
    measured boundary are what make the row a regression gate rather than a
    smoke test.
    """
    for values in (list(range(n)), [float(i) + 0.5 for i in range(n)]):
        ch = chain("c").then("chiral_flip")
        native = ch._run_native(values)
        assert native is not _NATIVE_MISS, (
            "srmech_dsl_chain_run declined at n=%d — the rc454 arena cliff" % n
        )
        assert native == values[::-1]


@_needs_native
@pytest.mark.parametrize("n_sectors,combine", [(1, "concat"), (4, "concat"),
                                               (1, None), (4, None)])
@pytest.mark.parametrize("n", [16, 256, 4096])
def test_shipped_arena_covers_the_fan_out(n_sectors, combine, n):
    """The <=4x fan-out also fits the arena the caller is told to allocate."""
    ch = chain("c").parallel_sectors("chiral_flip", n_sectors=n_sectors,
                                     combine=combine)
    assert ch._run_native(list(range(n))) is not _NATIVE_MISS


# ─────────────────────────────────────────────────────────────────────
# The bisection table
# ─────────────────────────────────────────────────────────────────────

_SIZES = (16, 256, 4096, 65536)
_SHAPES = ((1, "concat"), (4, "concat"), (1, None), (4, None))


@pytest.fixture(scope="module")
def table():
    """One bisection per (size, shape) cell. Module-scoped — the 65536 rows are
    the expensive part and are measured once for all the assertions below."""
    if not _HAS:
        pytest.skip("native srmech_dsl_chain_run not present")
    return {(n, ns, cb): _required(n, ns, cb)
            for n in _SIZES for (ns, cb) in _SHAPES}


@_needs_native
def test_every_row_is_bracketed(table):
    """Each requirement is a real boundary: one band lower genuinely FAILS.

    Without this the whole table degenerates into "a big number worked", which
    any padding constant satisfies.
    """
    for key, row in _rows(table):
        assert row["fails_at"] < row["required"], key
        assert row["required"] <= row["fails_at"] * 1.02 + 1024, (
            "bracket too loose to call a boundary at %r" % (key,))


@_needs_native
def test_requirement_is_under_the_declared_bound(table):
    """required <= _BOUND_FIXED + PER_IN*in + PER_OUT*out, on every row."""
    for (n, ns, cb), row in _rows(table):
        assert row["required"] <= _bound(n, row["out_elems"]), (
            "row (n=%d, ns=%d, combine=%r) needs %d bytes, past the declared "
            "bound %d" % (n, ns, cb, row["required"], _bound(n, row["out_elems"]))
        )


@_needs_native
def test_requirement_is_under_the_shipped_arena(table):
    """...and under what ``srmech_dsl_chain_run_arena_bytes`` hands the caller.

    This is the link between the measurement and the shipped behaviour: it is
    why the public path takes C rather than silently falling back.
    """
    for key, row in _rows(table):
        assert row["required"] <= row["arena_bytes"], key


@_needs_native
def test_per_output_element_ratio_stays_flat(table):
    """The ratio required/out_elems must not GROW from 256 to 65536.

    Bytes per output element, ``combine='concat'``, measured on WSL2 Linux gcc
    against ``libsrmech.so`` at ABI 24:

    ======  ==============  ==============
    n       n_sectors=1     n_sectors=4
    ======  ==============  ==============
    16      6050            1812
    256     3336            1108
    4096    3310            1102
    65536   3433            1139
    ======  ==============  ==============

    The n=16 column is higher because the ~100 KiB of fixed parse constants has
    not amortised yet; from 256 up the per-element cost is flat to within 4%
    (worst case 3310 -> 3433, +3.7%).

    ⚠️ THE DIGITS ARE HOST-DEPENDENT; THE ASSERTION IS NOT. ``required`` comes
    from a bisection that stops within ~1.5%, and the boundary moves with probe
    alignment — see the ``_MARGINAL_LO`` note. rc455 first tabulated
    ``6039 / 3313 / 3281 / 3411`` here without stating either the shape or the
    point of measurement, and that table does not reproduce on this host. The
    assertion below reads the LIVE table, so it is unaffected; only the
    illustration was wrong. Re-measure before quoting a digit.
    """
    for ns, cb in _SHAPES:
        base = table[(256, ns, cb)]
        ref = base["required"] / base["out_elems"]
        for n in (4096, 65536):
            row = table[(n, ns, cb)]
            ratio = row["required"] / row["out_elems"]
            assert ratio <= 1.25 * ref, (
                "per-output-element cost grew from %.0f (n=256) to %.0f "
                "(n=%d) for ns=%d combine=%r — that is what a fixed padding "
                "constant looks like" % (ref, ratio, n, ns, cb))


@_needs_native
@pytest.mark.parametrize("combine", ["concat", None])
def test_marginal_cost_per_extra_output_element_is_constant(table, combine):
    """THE ANTI-CONSTANT MEASUREMENT.

    A 4-sector fan-out emits ``3*n`` more elements than a 1-sector one from the
    SAME input. If the reserve were derived from the input, that difference
    would cost nothing and the two rows would need the same arena; if it were a
    fixed pad, the marginal rate would decay as 1/n. Measured, it is FLAT from
    n=16 to n=65536 — ~360-400 bytes per extra output element on this host,
    1.109x end to end. The flatness is the claim; the digit is not (see the
    ``_MARGINAL_LO`` note for why a four-figure reading over-states what a
    ~1.5% bisection can resolve).
    """
    seen = []
    for n in _SIZES:
        one = table[(n, 1, combine)]["required"]
        four = table[(n, 4, combine)]["required"]
        marginal = (four - one) / (3.0 * n)
        seen.append((n, marginal))
        assert _MARGINAL_LO <= marginal <= _MARGINAL_HI, (
            "marginal bytes per extra OUTPUT element is %.1f at n=%d "
            "(combine=%r); the reserve has stopped tracking output length: %r"
            % (marginal, n, combine, seen))
    spread = max(m for _, m in seen) / min(m for _, m in seen)
    assert spread <= 1.25, (
        "the marginal rate must be flat across three orders of magnitude, "
        "got a %.2fx spread: %r" % (spread, seen))
