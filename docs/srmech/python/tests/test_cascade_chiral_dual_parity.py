"""Parity tests for ``srmech.amsc.cascade.chiral_dual``.

v0.4.5rc8 — the LAST cascade op in the C-parity + TOML retrofit arc
and the ONLY higher-order one.

numpy-free (#564): numpy has been removed entirely from srmech. The old
native ``srmech_cascade_chiral_dual_f64`` fast-path marshalled C buffers
through numpy views for the Python callback, so it is GONE with numpy. The
public ``chiral_dual`` is now the pure-Python composition
``chiral_flip(op(chiral_flip(x)))`` — the cascade IS the composition
(Class C ∘ op ∘ Class C). Consequences these tests now encode:

- there is no ndarray input/output path (feed lists / tuples / strings);
- type preservation flows through ``op`` (the final ``chiral_flip`` is
  type-preserving, so the result type matches whatever ``op`` returns);
- there is no native callback trampoline, so the old wrong-length-output
  ValueError guard no longer exists (pure composition does not length-check);
- Python exceptions raised by ``op`` propagate directly (no trampoline).
"""

from __future__ import annotations

import random

from srmech.amsc.cascade import chiral_dual, chiral_flip


# ---------------------------------------------------------------------
# Basic semantic correctness
# ---------------------------------------------------------------------


def test_chiral_dual_identity_op_list():
    """Identity op: chiral_flip applied twice cancels."""
    result = chiral_dual(lambda v: v, [1.0, 2.0, 3.0])
    assert list(result) == [1.0, 2.0, 3.0]


def test_chiral_dual_negation_op_list():
    """Negation op: result is the element-wise negation (order unchanged
    because the two chiral_flips cancel around the order-preserving op)."""
    result = chiral_dual(lambda v: [-x for x in v], [1.0, 2.0, 3.0])
    assert list(result) == [-1.0, -2.0, -3.0]


def test_chiral_dual_non_trivial_op_agrees_with_python():
    """A non-order-preserving op (shift-by-one): the chiral-dual must
    agree with the pure-Python composition chiral_flip(op(chiral_flip(x)))."""
    def op(v):
        # Cycle-shift by one; not order-preserving so chiral_flip matters.
        out = list(v)
        if len(out) > 1:
            out = [out[-1]] + out[:-1]
        return out
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    py_ref = chiral_flip(op(chiral_flip(x)))
    result = chiral_dual(op, x)
    assert list(result) == list(py_ref)


def test_chiral_dual_tuple_input_op_returns_list():
    """A tuple input with an op that RETURNS A LIST yields a list — the
    result type follows op's output type (the final chiral_flip preserves
    op's list output), not the input container type. This is the numpy-free
    pure-composition contract (#564): there is no native callback to
    reimpose the input container type."""
    result = chiral_dual(lambda v: [x * 2.0 for x in v], (1.0, 2.0, 3.0))
    assert isinstance(result, list)
    assert result == [2.0, 4.0, 6.0]


def test_chiral_dual_tuple_preserved_when_op_preserves_type():
    """When op preserves the container type, chiral_dual returns a tuple
    for a tuple input — type flows through op + the type-preserving
    chiral_flip composition."""
    result = chiral_dual(lambda v: type(v)(x * 2.0 for x in v), (1.0, 2.0, 3.0))
    assert isinstance(result, tuple)
    assert result == (2.0, 4.0, 6.0)


# ---------------------------------------------------------------------
# Boundary cases
# ---------------------------------------------------------------------


def test_chiral_dual_empty_list():
    """Empty list: returns empty list."""
    result = chiral_dual(lambda v: v, [])
    assert result == [] or list(result) == []


def test_chiral_dual_singleton_list():
    """Singleton: a sequence of length 1 reverses to itself, so the
    chiral_dual reduces to op."""
    result = chiral_dual(lambda v: [v[0] * 2.0], [5.0])
    assert list(result) == [10.0]


# ---------------------------------------------------------------------
# Random sweep — pure composition self-consistency
# ---------------------------------------------------------------------


def test_chiral_dual_random_sweep_matches_composition():
    """50-sample random sweep with a fixed op: chiral_dual agrees exactly
    with the pure-Python composition chiral_flip(op(chiral_flip(x))) — they
    are now the same code path, so equality is exact (no machine-precision
    slack needed)."""
    rng = random.Random(0xC0FFEE)
    for _ in range(50):
        n = rng.randint(0, 20)
        x = [rng.uniform(-100.0, 100.0) for _ in range(n)]
        op = lambda v: [val + 1.0 for val in v]
        py_ref = chiral_flip(op(chiral_flip(x)))
        result = chiral_dual(op, x)
        assert list(result) == list(py_ref), (
            f"composition divergence at n={n}: result={result} ref={py_ref}"
        )


# ---------------------------------------------------------------------
# Exception propagation (now direct — no trampoline)
# ---------------------------------------------------------------------


def test_chiral_dual_op_exception_propagates():
    """A Python exception raised inside the op surfaces as the same
    exception — the pure composition simply evaluates op(...) so the error
    propagates directly (no native callback to swallow it)."""
    def bad_op(v):
        return 1 / 0  # intentional ZeroDivisionError
    try:
        chiral_dual(bad_op, [1.0, 2.0])
    except ZeroDivisionError:
        pass
    else:  # pragma: no cover
        raise AssertionError("ZeroDivisionError did not propagate")


# ---------------------------------------------------------------------
# String + mixed-type paths (always pure composition)
# ---------------------------------------------------------------------


def test_chiral_dual_mixed_type_list():
    """A mixed-int+float list: chiral_flip(op(chiral_flip([1, 2.0, 3]))) with
    an identity op is an identity round-trip."""
    result = chiral_dual(lambda v: v, [1, 2.0, 3])
    assert list(result) == [1, 2.0, 3]


def test_chiral_dual_string_identity():
    """A string with an identity op: str[::-1] in / out round-trips."""
    result = chiral_dual(lambda s: s, "abc")
    assert result == "abc"


def test_chiral_dual_string_uppercase_op():
    """A string with a transforming op: chiral_flip("abc") = "cba";
    op.upper() = "CBA"; chiral_flip("CBA") = "ABC"."""
    result = chiral_dual(lambda s: s.upper(), "abc")
    assert result == "ABC"


def test_chiral_dual_non_callable_op_raises():
    """Passing a non-callable op raises TypeError when the composition
    tries to invoke it."""
    try:
        chiral_dual(None, [1.0, 2.0, 3.0])
    except TypeError:
        pass
    else:  # pragma: no cover
        raise AssertionError("TypeError not raised for non-callable op")
