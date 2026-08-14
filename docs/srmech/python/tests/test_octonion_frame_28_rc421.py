"""rc421 (`#T1122`) — the 𝕆 frame-committed read is 28-valued, and the count
was MEASURED.

Through rc420 ``srmech.cascade.octonion_frame_read`` accepted only ``frame=4``.
The validator's argument was that ``e₁/e₂/e₃`` lie inside the ℍ base and
``e₅/e₆/e₇`` "are not independent seam generators, so no other single basis unit
splits 𝕆 = ℍ ⊕ ℍℓ cleanly". The first clause is true; **the conclusion is
false**, and this file pins the measurement that shows it.

What is actually the case, derived from ``cd_mult`` / ``cd_basis_product``
rather than from any tabulated Fano convention:

  1. 𝕆 has **7** Fano lines; each ``span{e₀} ∪ line`` is closed and has all
     ``64`` ordered base-triple associators zero (a genuine ℍ subalgebra).
  2. Each line admits **4** valid splitting units — including the standard base,
     whose four are ``{e₄,e₅,e₆,e₇}``, not ``{e₄}``.
  3. All ``7 × 4 = 28`` reads of one generic octonion are **DISTINCT**, so the
     frame is the ``(line, ℓ)`` **PAIR** and the parameter is 28-valued. This
     is the leg the rc421 research did NOT guess in advance: leg 2 held ``ℓ`` at
     ``seam[0]`` and so measured only seven.
  4. Within a line the four ``ℓ`` differ by an exactly predictable **right
     action**: ``base_H' = base_H·u`` and ``canonical_affine' =
     canonical_affine·u`` for the signed base unit ``u`` with ``e_ℓ' = u·e_ℓ``,
     while ``q0`` / ``base_R`` / ``norm_sq`` are ``ℓ``-invariant.
  5. ``frame=4`` is **byte-identical** to its pre-rc421 behaviour — pinned here
     against values captured from the rc420 op, not against the new one.

The NEGATIVE CONTROL is the point of §3: a reader that silently ignored ``ℓ``
would return **7** distinct reads over the 28 pairs, not 28. That is measured
here as an explicit collapsing control, so the ``== 28`` assertion is a gate
that CAN fail rather than a decorative count.

⚠️ HONESTY NOTE carried from the generating scripts, so it cannot drift. Leg 1
(``docs/srmech/notes/octonion_frame_seven_frames_rc421.py``) pre-registered four
conditions, and its condition (iv) ("no nonzero associator lies entirely inside
the base") is **implied by** condition (ii) ("all 64 ordered base-triple
associators vanish"), because the line is a subset of the base. (iv) could not
have returned otherwise once (ii) passed: it is DERIVED, not independent
evidence, and is not re-asserted as a separate finding here. Conditions (i),
(ii) and (iii) are genuine — each could have failed against srmech's own table.

Generating scripts: ``docs/srmech/notes/octonion_frame_seven_frames_rc421.py``
(leg 1), ``…_generalised_read_rc421.py`` (leg 2), ``…_ell_within_line_rc421.py``
(leg 3, the 28-vs-7 decision). numpy-free; srmech + stdlib only. No ``abs()``.
"""
from __future__ import annotations

import itertools

import pytest

from srmech.cascade import octonion_frame_read
from srmech.cascade.cayley_dickson import (
    OCTONION_FRAME_COUNT,
    OCTONION_FRAME_LINE,
    OCTONION_FRAME_SEAM,
    _octonion_fano_lines,
    associator,
    cd_basis,
    cd_basis_product,
)
from srmech.math.q import Q

# A deliberately generic octonion: no zero coordinate, no repeated value, so a
# read that collapses across frames cannot do so by accident.
_X = (1, 2, 3, 5, 7, 11, 13, 17)


def _e(i):
    return cd_basis(8, i)


def _valid_splitting_units(line):
    """Which ℓ carry this line's ℍ base ONTO its seam — derived, not tabulated."""
    base = (0,) + tuple(line)
    seam = [k for k in range(1, 8) if k not in line]
    good = []
    for ell in seam:
        hit, ok = set(), True
        for b in base:
            index, _sign = cd_basis_product(8, b, ell)
            if index in base:
                ok = False
                break
            hit.add(index)
        if ok and hit == set(seam):
            good.append(ell)
    return good


def _all_frames():
    return [(line, ell) for line in _octonion_fano_lines()
            for ell in _valid_splitting_units(line)]


def _read_key(r):
    """An exact, comparable rendering of a read (no float anywhere)."""
    return tuple(
        (k, tuple(str(c) for c in v) if isinstance(v, tuple) else str(v))
        for k, v in sorted(r.items())
        if k in ("q0", "q1", "base_H", "base_R", "norm_sq", "canonical_affine"))


# ── 1. the seven ℍ subalgebras, derived from cd_mult ─────────────────────
def test_seven_fano_lines_derived_from_the_table():
    lines = _octonion_fano_lines()
    assert len(lines) == 7, f"𝕆 has 7 Fano lines; derived {len(lines)}"
    # every triple really is closed: e_i·e_j = ±e_k for the third member
    for i, j, k in lines:
        index, _sign = cd_basis_product(8, i, j)
        assert index == k, f"line {(i, j, k)} not closed: e{i}·e{j} = ±e{index}"


def test_every_line_is_a_coherent_H_subalgebra():
    """Condition (ii): all 64 ordered base-triple associators vanish, per line.

    This is the genuine one — it could have failed against srmech's own table
    for any of the seven. Condition (iv) of the leg-1 pre-registration is
    IMPLIED by this and is deliberately not restated as separate evidence.
    """
    for line in _octonion_fano_lines():
        base = (0,) + tuple(line)
        nz = sum(1 for t in itertools.product(base, repeat=3)
                 if any(v != 0 for v in associator(_e(t[0]), _e(t[1]), _e(t[2]))))
        assert nz == 0, f"base {base} must be coherent (0/64); got {nz}"


def test_every_line_admits_exactly_four_splitting_units():
    """The clause rc420's error message got wrong: the STANDARD base admits
    four valid ℓ (e₄,e₅,e₆,e₇), not one."""
    for line in _octonion_fano_lines():
        ells = _valid_splitting_units(line)
        assert len(ells) == 4, f"line {line}: expected 4 splitting units, got {ells}"
    assert _valid_splitting_units(OCTONION_FRAME_LINE) == [4, 5, 6, 7]


# ── 2. the frame is the (line, ℓ) PAIR — 28, not 7 ───────────────────────
def test_there_are_exactly_28_well_posed_frames():
    frames = _all_frames()
    assert len(frames) == OCTONION_FRAME_COUNT == 28, (
        f"expected 7 lines × 4 units = 28 frames; got {len(frames)}")


def test_all_28_reads_are_distinct_the_frame_is_the_pair():
    """THE MEASUREMENT THAT PICKED THE API SHAPE. If the four ℓ of a line had
    agreed, the frame would be the LINE and `frame=` would be 7-valued."""
    reads = {}
    for line, ell in _all_frames():
        reads[(line, ell)] = _read_key(
            octonion_frame_read(_X, frame=(line[0], line[1], line[2], ell)))
    assert len(set(reads.values())) == 28, (
        f"the 28 frames must give 28 DISTINCT reads; got "
        f"{len(set(reads.values()))} — the frames collapsed")


def test_negative_control_a_collapsing_reader_would_give_seven():
    """NEGATIVE CONTROL — the gate above must be able to FAIL.

    A reader that ignored ℓ (always using its line's first valid unit) returns
    SEVEN distinct reads over the same 28 pairs. Measuring that separation here
    is what makes `== 28` evidence rather than decoration.
    """
    collapsed = set()
    for line, _ell in _all_frames():
        first = _valid_splitting_units(line)[0]
        collapsed.add(_read_key(octonion_frame_read(
            _X, frame=(line[0], line[1], line[2], first))))
    assert len(collapsed) == 7, (
        f"a ℓ-ignoring reader must give 7 distinct reads; got {len(collapsed)}")
    honest = {_read_key(octonion_frame_read(
        _X, frame=(l[0], l[1], l[2], e))) for l, e in _all_frames()}
    assert len(honest) == 28 and len(honest) != len(collapsed)


def test_norm_sq_is_the_frame_independent_scale():
    norms = {octonion_frame_read(_X, frame=(l[0], l[1], l[2], e))["norm_sq"]
             for l, e in _all_frames()}
    assert len(norms) == 1, f"norm_sq must be shared by all 28 frames; got {norms}"
    assert norms.pop() == Q(sum(c * c for c in _X), 1)


# ── 3. HOW the four ℓ of a line differ — the exact right action ──────────
def _transition_unit(line, ell0, ell):
    """The signed base unit u with e_ℓ = u·e_ℓ₀, read off cd_basis_product."""
    for b in (0,) + tuple(line):
        index, sign = cd_basis_product(8, b, ell0)
        if index == ell:
            return b, sign
    return None


def test_within_a_line_the_four_ell_differ_by_a_signed_permutation():
    """base_H' = base_H·u and canonical_affine' = canonical_affine·u — the
    predictable structure the ℓ-dependence actually has (28/28 in leg 3)."""
    from srmech.cascade.cayley_dickson import _frame_h_mult

    law = affine = total = affine_total = 0
    for line in _octonion_fano_lines():
        ells = _valid_splitting_units(line)
        ell0 = ells[0]
        base = (0,) + tuple(line)
        r0 = octonion_frame_read(_X, frame=(line[0], line[1], line[2], ell0))
        for ell in ells:
            r = octonion_frame_read(_X, frame=(line[0], line[1], line[2], ell))
            got = _transition_unit(line, ell0, ell)
            assert got is not None, (line, ell0, ell)
            b, sign = got
            u = [Q(0, 1)] * 4
            u[base.index(b)] = Q(sign, 1)
            total += 1
            law += 1 if _frame_h_mult(base, r0["base_H"], u) == r["base_H"] else 0
            if r0["canonical_affine"] is not None and r["canonical_affine"] is not None:
                affine_total += 1
                affine += 1 if _frame_h_mult(
                    base, r0["canonical_affine"], u) == r["canonical_affine"] else 0
    assert (law, total) == (28, 28), f"base_H right action: {law}/{total}"
    # denominator reported so a 0-of-0 cannot pass as a pass
    assert affine_total == 28, f"affine law denominator is {affine_total}, not 28"
    assert affine == 28, f"canonical_affine right action: {affine}/{affine_total}"


def test_q0_base_R_and_norm_sq_are_ell_invariant_within_a_line():
    for line in _octonion_fano_lines():
        ells = _valid_splitting_units(line)
        reads = [octonion_frame_read(_X, frame=(line[0], line[1], line[2], e))
                 for e in ells]
        assert len({r["q0"] for r in reads}) == 1
        assert len({r["base_R"] for r in reads}) == 1
        assert len({r["norm_sq"] for r in reads}) == 1
        # ...while the seam half and the Hopf base genuinely MOVE
        assert len({r["q1"] for r in reads}) == 4
        assert len({r["base_H"] for r in reads}) == 4


# ── 4. frame=4 back-compat — pinned against the PRE-rc421 values ─────────
# Captured by RUNNING the rc420 op (not by inspecting the rc421 one), so this
# is a differential gate against the old behaviour rather than a restatement of
# the new. _XB is the rc384 docstring/test probe.
_XB = [1, 2, -3, 1, 2, -1, 1, 4]
_PRE_RC421_FRAME_4 = {
    "frame": 4,
    "dim": 8,
    "q0": (Q(1, 1), Q(2, 1), Q(-3, 1), Q(1, 1)),
    "q1": (Q(2, 1), Q(-1, 1), Q(1, 1), Q(4, 1)),
    "base_H": (Q(2, 1), Q(36, 1), Q(4, 1), Q(-2, 1)),
    "base_R": Q(-7, 1),
    "norm_sq": Q(37, 1),
    "writhe": (Q(2, 1), Q(-1, 1), Q(1, 1), Q(4, 1)),
    "writhe_norm_sq": Q(22, 1),
    "canonical_affine": (Q(1, 22), Q(9, 11), Q(1, 11), Q(-1, 22)),
}


def test_frame_4_is_byte_identical_to_pre_rc421():
    r = octonion_frame_read(_XB)
    for key, want in _PRE_RC421_FRAME_4.items():
        assert r[key] == want, f"frame=4 moved at {key}: {r[key]!r} != {want!r}"


def test_frame_4_additions_are_purely_additive():
    """The widening may only ADD keys at the default frame."""
    r = octonion_frame_read(_XB)
    assert set(r) - set(_PRE_RC421_FRAME_4) == {"base", "seam", "seam_chart"}
    assert r["base"] == (0, 1, 2, 3)
    assert r["seam"] == (4, 5, 6, 7)
    # the default chart is the identity: q0 = x[:4] and q1 = x[4:] exactly
    assert r["seam_chart"] == ((4, 0, 1), (5, 1, 1), (6, 2, 1), (7, 3, 1))
    assert r["q0"] == tuple(Q(v, 1) for v in _XB[:4])
    assert r["q1"] == tuple(Q(v, 1) for v in _XB[4:])


def test_default_and_both_spellings_agree_at_the_cd_frame():
    assert (octonion_frame_read(_XB)
            == octonion_frame_read(_XB, frame=OCTONION_FRAME_SEAM)
            == octonion_frame_read(_XB, frame=(1, 2, 3, 4)))


def test_bare_int_spelling_is_the_default_line():
    for ell in (4, 5, 6, 7):
        assert (octonion_frame_read(_X, frame=ell)
                == octonion_frame_read(_X, frame=(1, 2, 3, ell)))


# ── 5. the S³ fiber guard survives at EVERY frame (non-tautological) ─────
_LAM = (Q(1, 2), Q(1, 2), Q(1, 2), Q(1, 2))    # |λ|² = 1, a Hurwitz unit


def _rebuild(base, ell, q0, q1):
    """Reassemble an 8-vector from a frame's two halves, via cd_mult."""
    from srmech.cascade.cayley_dickson import _frame_embed
    from srmech.cascade.cayley_dickson import cd_mult as _m
    x = list(_frame_embed(base, q0))
    seam_part = _m(_frame_embed(base, q1), cd_basis(8, ell))
    return [a + b for a, b in zip(x, seam_part)]


@pytest.mark.parametrize("line,ell", _all_frames())
def test_fiber_invariance_and_nonfiber_control_at_every_frame(line, ell):
    """At EVERY one of the 28 frames: the Hopf base is UNCHANGED under the S³
    fiber (both halves right-multiplied by a unit quaternion) and CHANGED under
    a non-fiber move. The docstring's explicit non-tautology guard has to
    survive the generalisation at each frame, not just at e₄."""
    from srmech.cascade.cayley_dickson import _frame_h_mult

    base = (0,) + tuple(line)
    spec = (line[0], line[1], line[2], ell)
    r = octonion_frame_read(_X, frame=spec)
    # FIBER: right-multiply BOTH halves by the unit λ
    rf = octonion_frame_read(
        _rebuild(base, ell, _frame_h_mult(base, r["q0"], _LAM),
                 _frame_h_mult(base, r["q1"], _LAM)), frame=spec)
    assert rf["base_H"] == r["base_H"], f"fiber moved base_H at frame {spec}"
    assert rf["base_R"] == r["base_R"]
    assert rf["norm_sq"] == r["norm_sq"]
    assert rf["writhe"] != r["writhe"], "the writhe must be EQUIVARIANT"
    # NON-FIBER CONTROL: move only q0 — the base MUST change
    rn = octonion_frame_read(
        _rebuild(base, ell, _frame_h_mult(base, r["q0"], _LAM), r["q1"]),
        frame=spec)
    changed = not all(
        rn["base_H"][i] * r["base_R"] == r["base_H"][i] * rn["base_R"]
        for i in range(4))
    assert changed, (
        f"non-fiber move must change the base at frame {spec} — the "
        f"instrument has to be able to return otherwise")


@pytest.mark.parametrize("line,ell", _all_frames())
def test_four_sphere_identity_holds_at_every_frame(line, ell):
    from srmech.cascade.cayley_dickson import cd_norm_sq
    r = octonion_frame_read(_X, frame=(line[0], line[1], line[2], ell))
    assert (cd_norm_sq(r["base_H"]) + r["base_R"] * r["base_R"]
            == r["norm_sq"] * r["norm_sq"])


# ── 6. rejection — each defect named separately, not one generic error ───
@pytest.mark.parametrize("bad,needle", [
    (2, "lies INSIDE"),                 # int spelling cannot change the base
    (1, "lies INSIDE"),
    (3, "lies INSIDE"),
    (0, "REAL unit"),
    (8, "not a basis index"),
    (-1, "not a basis index"),
    ((1, 2, 4, 5), "not a Fano line"),
    ((2, 4, 6, 4), "lies INSIDE its own"),
    ((1, 2, 3), "4-sequence"),
    ((1, 2, 3, 4, 5), "4-sequence"),
    ((0, 1, 2, 4), "distinct IMAGINARY"),
    ((1, 1, 3, 4), "distinct IMAGINARY"),
    ("1234", "text value"),
    ((1.5, 2, 3, 4), "non-integral"),
    (None, "not all basis"),
])
def test_invalid_frames_are_rejected_with_a_reason(bad, needle):
    with pytest.raises(ValueError) as exc:
        octonion_frame_read(_X, frame=bad)
    assert needle in str(exc.value), (
        f"frame={bad!r} must be refused with a message naming the DEFECT "
        f"({needle!r}); got: {exc.value}")


def test_rejection_messages_teach_rather_than_merely_refuse():
    """The old message was good pedagogy; its replacement must be at least as
    specific — naming the base, the valid alternatives, and the way out."""
    with pytest.raises(ValueError) as exc:
        octonion_frame_read(_X, frame=2)
    msg = str(exc.value)
    assert "(4, 5, 6, 7)" in msg, "must name this line's valid splitting units"
    assert "frame=(1, 4, 5, 2)" in msg, "must show how to put e2 in the seam"
    assert "28" in msg, "must say how many well-posed frames exist"


def test_non_octonion_input_still_rejected():
    with pytest.raises(ValueError):
        octonion_frame_read([1, 2, 3, 4])


# ── 7. the split is DERIVED from the table, not tabulated ────────────────
def test_seam_chart_reproduces_the_split_through_cd_basis_product():
    """Every returned chart triple (m, σ(m), s) must satisfy
    e_σ(m)·e_ℓ = s·e_m against srmech's own cocycle."""
    for line, ell in _all_frames():
        r = octonion_frame_read(_X, frame=(line[0], line[1], line[2], ell))
        assert len(r["seam_chart"]) == 4
        assert tuple(m for m, _b, _s in r["seam_chart"]) == r["seam"]
        for m, b, s in r["seam_chart"]:
            index, sign = cd_basis_product(8, b, ell)
            assert (index, sign) == (m, s), (
                f"chart triple {(m, b, s)} disagrees with cd_basis_product")
            assert b in r["base"] and s in (1, -1)


def test_q1_is_the_seam_half_pulled_back_along_ell():
    """q₁'s coefficient at slot σ(m) is s·x_m — the defining relation of the
    split x = q₀ + q₁·ℓ, checked against the returned chart."""
    for line, ell in _all_frames():
        r = octonion_frame_read(_X, frame=(line[0], line[1], line[2], ell))
        for m, b, s in r["seam_chart"]:
            want = Q(_X[m], 1) if s == 1 else -Q(_X[m], 1)
            assert r["q1"][r["base"].index(b)] == want


def test_no_abs_in_the_frame_read_source():
    """Cascade-honesty: sign handling is Class K pin-slot + Class C
    re-application, never a bare abs().

    The docstrings SAY "no ``abs()``", so a naive substring scan over the raw
    source passes on the prose and would keep passing if the code grew a real
    one. The docstring is stripped first, so this reads the CODE.
    """
    import ast
    import inspect
    import textwrap

    from srmech.cascade import cayley_dickson as cd
    for fn in (cd.octonion_frame_read, cd._octonion_frame_spec,
               cd._octonion_fano_lines, cd._frame_h_mult, cd._frame_h_conj):
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
        body = tree.body[0]
        if (body.body and isinstance(body.body[0], ast.Expr)
                and isinstance(body.body[0].value, ast.Constant)
                and isinstance(body.body[0].value.value, str)):
            body.body = body.body[1:]           # drop the docstring
        code = ast.unparse(tree)
        assert "abs(" not in code, f"{fn.__name__} uses abs() in its CODE"
        calls = {n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
        assert "abs" not in calls, f"{fn.__name__} calls abs()"
