"""Octonion algebra: the Cayley-Dickson-from-H multiplication table + L/R binders.

The foundational layer of the ``srmech.qm`` so(8)/Spin(8) triality engine
(v0.5.0rc17). Octonions are the 8-dimensional real normed division algebra
``O`` obtained by doubling the quaternions ``H``; their multiplication
fixes a sign convention that, once chosen, IS the provenance of every
downstream object (the 28 so(8) generators, the order-3 triality
automorphism ``tau``, the ``Fix(tau) = g2`` keystone).

Per ``[[feedback_science_is_ssot_not_project]]``: each operation cites the
canonical octonion literature, **not** a project instantiation.

FIXED CONVENTION (Cayley-Dickson doubling ``R -> C -> H -> O``):

- doubling rule:  ``(a, b) * (c, d) = (a*c - conj(d)*b, d*a + b*conj(c))``
- conjugation:    ``conj((a, b)) = (conj(a), -b)``; ``conj(scalar) = scalar``

The 480 sign-ambiguous conventions collapse to ONE the moment these two
generative rules are fixed (no free per-pair sign choices remain). That
determinism is what :func:`octonion_table_attestation` content-addresses
(``response_sha256`` over the int8 table bytes): *same convention -> same
``tau`` reproducibly*. The resulting unordered Fano lines are
``{1,2,3} {1,4,5} {1,6,7} {2,4,6} {2,5,7} {3,4,7} {3,5,6}`` — bit-for-bit
identical to Baez (2002) §2.

A-N placement (per ``[[feedback_no_privileged_primitive_classes]]``):

- ``octonion_mult_table`` / ``octonion_table_attestation`` — **Class A**
  (content-addressing: the convention IS the provenance; the attestation is
  a SHA-256 over the table bytes).
- ``octonion_left_mult`` / ``octonion_right_mult`` — **Class M** (Clifford /
  HDC binding: ``L_a`` and ``R_a`` bind the 8-dim octonion space; the 7+7
  imaginary-unit binders are the ``14`` non-``g2`` directions of the ``28``).
- ``octonion_conjugate`` — **Class C** (chirality / orientation: conjugation
  flips the imaginary-axis sign).
- ``octonion_norm`` — **Class K + Class C** (the Class K pin-slot magnitude
  via ``srmech.amsc.cascade.magnitude`` composed with Class C sign-handling;
  **never** Python ``abs()`` per
  ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``).

Canonical SSoT:

- Baez, J.C. (2002) *The Octonions*, Bull. Amer. Math. Soc. 39, 145-205
  (arXiv:math/0105155) — Cayley-Dickson construction, the Fano plane,
  ``G2 = Aut(O)`` with Lie algebra ``Der(O)``, Spin(8) triality.
- Schafer, R.D. (1966) *An Introduction to Nonassociative Algebras*,
  Academic Press — the derivation ``D_{a,b}`` of a composition algebra.
- Boyle, L. (2020) *The Standard Model, The Exceptional Jordan Algebra, and
  Triality* (arXiv:2006.16265) — the SM-physics context (three generations
  related to SO(8) triality).
"""

from __future__ import annotations

import functools
from srmech.amsc.rational import sqrt as _rsqrt  # §22: scalar root via Class-N
from typing import Tuple

import numpy as np

from srmech.amsc import hdc as _M  # rc9: the C-dispatched octonion loop family
from srmech.amsc.cascade import magnitude as _magnitude
from srmech.amsc.format import sha256_bytes as _sha256_bytes

#: Octonion dimension (the real normed division algebra ``O``).
_DIM = 8

#: The two generative rules that fix THE convention (their bytes are the
#: ``parser_rule_hash`` provenance — change a rule and the whole table /
#: ``tau`` change, which the content-addressed hash detects).
_DOUBLING_RULE = b"(a,b)*(c,d)=(a*c - conj(d)*b, d*a + b*conj(c))"
_CONJ_RULE = b"conj((a,b))=(conj(a),-b); conj(scalar)=scalar"

#: A FIXED ISO timestamp for the self-attestation. Deterministic on
#: purpose (NOT ``datetime.now()``) so the MCP surface is reproducible: the
#: attestation of a GENERATED constant must not change between calls.
_RETRIEVED_AT = "2026-05-29T00:00:00Z"

#: The 7 unordered Fano lines of the fixed convention (Baez 2002 §2). The
#: oriented ``+1`` structure constants ``e_i e_j = +e_k`` close along these.
_FANO_LINES: Tuple[Tuple[int, int, int], ...] = (
    (1, 2, 3), (1, 4, 5), (1, 6, 7),
    (2, 4, 6), (2, 5, 7),
    (3, 4, 7), (3, 5, 6),
)


@functools.lru_cache(maxsize=1)
def _build_mult_table() -> np.ndarray:
    """Generate the ``(8, 8, 8)`` int8 structure-constant tensor (cached).

    rc10: built from the Cayley-Dickson basis cocycle ``e_i·e_j = sign·e_{i⊕j}``
    via :func:`srmech.amsc.cascade.cd_basis_product` — the C primitive
    ``srmech_cd_basis_product`` when native is present, its pure-Python loop
    otherwise. Same fixed convention as the module docstring's generative rules
    (``_DOUBLING_RULE`` / ``_CONJ_RULE``); the int8 bytes are **identical** to the
    prior recursive build, so the content-address in
    :func:`octonion_table_attestation` (a SHA-256 over the table) is unchanged.
    Built exactly once and memoised — :func:`octonion_mult_table` hands callers a
    fresh COPY each call so the cached array can never be mutated.
    """
    from srmech.amsc.cascade import cd_basis_product as _cd_basis_product
    table = np.zeros((_DIM, _DIM, _DIM), dtype=np.int8)
    for i in range(_DIM):
        for j in range(_DIM):
            idx, sign = _cd_basis_product(_DIM, i, j)
            table[i, j, idx] = np.int8(sign)
    table.flags.writeable = False
    return table


def octonion_mult_table() -> np.ndarray:
    """The ``(8, 8, 8)`` int8 structure-constant tensor ``C``.

    ``e_i * e_j = sum_k C[i, j, k] e_k`` under the fixed Cayley-Dickson-from-H
    convention (see module docstring). ``e_0`` is the identity;
    ``e_1^2 = ... = e_7^2 = -e_0``; the off-diagonal imaginary products
    anticommute. Built from the Cayley-Dickson basis cocycle
    (:func:`srmech.amsc.cascade.cd_basis_product`; the native
    ``srmech_cd_basis_product`` when present). The generation is memoised
    (:func:`_build_mult_table`); each
    call returns a fresh writeable copy (two calls are byte-identical but
    independent).

    Class A (content-addressing): the table is the MPR-attested constant
    that :func:`octonion_table_attestation` content-addresses.

    Canonical SSoT: Baez (2002) §2 (the Fano-plane multiplication table).

    Returns:
        ``(8, 8, 8)`` ``int8`` ndarray; ``C[i, j, k]`` is the ``e_k``
        coefficient of ``e_i * e_j`` (entries in ``{-1, 0, +1}``).
    """
    return np.array(_build_mult_table(), dtype=np.int8)


def octonion_table_attestation() -> dict:
    """MPR v1 self-attestation dict for the structure-constant table.

    A self-attestation for a GENERATED constant (NOT a fetched datum): the
    convention IS the provenance, so ``response_sha256`` content-addresses
    the table's int8 bytes via :func:`srmech.amsc.format.sha256_bytes`
    (Class A; **no** new ``hashlib.sha256`` per the C-library discipline).
    Returned as a plain MPR-shaped ``dict`` (NOT run through the strict
    ``format.validate_mpr_record`` — that validator targets fetched data
    with on-disk TOML descriptors; a generated-constant self-attestation
    has no such descriptor file). ``retrieved_at`` is a FIXED ISO string so
    the MCP surface is reproducible.

    Class A (content-addressing): the attestation IS a SHA-256 fingerprint.

    Canonical SSoT: Baez (2002), Bull. Amer. Math. Soc. 39, 145-205
    (arXiv:math/0105155).

    Returns:
        A plain ``dict`` with ``mpr_version``, ``data``, ``data_schema_id``,
        ``attestation`` (incl. ``response_sha256`` = ``sha256_bytes`` of the
        table), and ``rendering`` keys.
    """
    table = octonion_mult_table()
    response_sha256 = _sha256_bytes(table.astype(np.int8).tobytes())
    parser_rule_hash = _sha256_bytes(_DOUBLING_RULE + b"\n" + _CONJ_RULE)
    descriptor_hash = _sha256_bytes(
        b"srmech/qm/octonion.py::cayley_dickson_from_H"
    )
    return {
        "mpr_version": "1.0",
        "data": {
            "convention": "cayley_dickson_from_H",
            "basis_order": "e0..e7",
            "fano_triples": [list(line) for line in _FANO_LINES],
        },
        "data_schema_id": "srmech://schema/octonion_structure_constants",
        "attestation": {
            # Baez is OA on arXiv; a paywalled-only DOI is rejected per
            # [[feedback_paywalled_doi_cannot_be_attested]] — so no source_doi.
            "source_doi": None,
            "source_url": "https://arxiv.org/abs/math/0105155",
            "license": "CC0",
            "retrieved_at": _RETRIEVED_AT,
            "response_sha256": response_sha256,
            "parser_version": "srmech 0.5.0",
            "parser_rule_hash": parser_rule_hash,
            "collector_descriptor_path": "srmech/qm/octonion.py",
            "collector_descriptor_hash": descriptor_hash,
        },
        "rendering": {
            "name": "Octonion multiplication table (Cayley-Dickson from H)",
            "purpose": "Fixed sign convention for the so(8)/triality engine",
            "cite_as": (
                "Baez, J.C. (2002) The Octonions, Bull. Amer. Math. Soc. 39, "
                "145-205 (arXiv:math/0105155)"
            ),
        },
    }


def octonion_left_mult(a: np.ndarray) -> np.ndarray:
    """Left-multiplication matrix ``L_a`` (``x -> a * x``) as an ``8x8`` real.

    Column ``j`` is ``a * e_j``; ``L_a[k, j] = sum_i a_i C[i, j, k]``. For an
    imaginary unit ``e_i`` (``i >= 1``) the matrix ``L_{e_i}`` is already
    antisymmetric, so it sits directly in ``so(8)`` (one of the 7 L-type
    coset directions of the ``28``).

    Class M (Clifford / HDC binding).

    Canonical SSoT: Baez (2002) §2.3-2.4 (left/right multiplication and the
    bimodule structure underlying triality).

    Args:
        a: An 8-vector octonion (real components ``(a_0, ..., a_7)``).

    Returns:
        ``8x8`` real matrix ``L_a``.

    Raises:
        ValueError: if ``a`` is not shape ``(8,)``.
    """
    a = np.asarray(a, dtype=float)
    if a.shape != (_DIM,):
        raise ValueError(
            f"octonion_left_mult: a must be an 8-vector; got {a.shape}"
        )
    # rc9: dispatch the bind through the C-backed octonion loop operator
    # (srmech_loop_left_op_f64, native when HAS_NATIVE; pure-Python fallback).
    # L_a[k, j] = sum_i a_i C[i, j, k] is bit-identical to the per-basis binds
    # that loop_left_op column-stacks (same Cayley-Dickson-from-H convention).
    return np.asarray(_M.loop_left_op(a), dtype=float)


def octonion_right_mult(a: np.ndarray) -> np.ndarray:
    """Right-multiplication matrix ``R_a`` (``x -> x * a``) as an ``8x8`` real.

    Column ``j`` is ``e_j * a``; ``R_a[k, j] = sum_i a_i C[j, i, k]``. For an
    imaginary unit ``e_i`` (``i >= 1``) the matrix ``R_{e_i}`` is already
    antisymmetric (the other 7 R-type coset directions of the ``28``).

    Class M (Clifford / HDC binding).

    Canonical SSoT: Baez (2002) §2.3-2.4.

    Args:
        a: An 8-vector octonion.

    Returns:
        ``8x8`` real matrix ``R_a``.

    Raises:
        ValueError: if ``a`` is not shape ``(8,)``.
    """
    a = np.asarray(a, dtype=float)
    if a.shape != (_DIM,):
        raise ValueError(
            f"octonion_right_mult: a must be an 8-vector; got {a.shape}"
        )
    # rc9: dispatch through the C-backed octonion loop operator
    # (srmech_loop_right_op_f64); bit-identical to the einsum over the table.
    return np.asarray(_M.loop_right_op(a), dtype=float)


def octonion_conjugate(x: np.ndarray) -> np.ndarray:
    """Octonion conjugate ``conj(x) = (x_0, -x_1, ..., -x_7)``.

    Flips the sign of the seven imaginary axes (the scalar axis is fixed).
    Class C (chirality / orientation).

    Canonical SSoT: Baez (2002) §2.1 (conjugation and the norm form).

    Args:
        x: An 8-vector octonion.

    Returns:
        The 8-vector conjugate.

    Raises:
        ValueError: if ``x`` is not shape ``(8,)``.
    """
    x = np.asarray(x, dtype=float)
    if x.shape != (_DIM,):
        raise ValueError(
            f"octonion_conjugate: x must be an 8-vector; got {x.shape}"
        )
    # rc9: dispatch through the C-backed octonion conjugate (srmech_loop_conj_f64,
    # the Class-C imaginary-axis sign flip); bit-identical to negating x[1:].
    return np.asarray(_M.loop_conj(x), dtype=float).reshape(_DIM)


def octonion_norm(x: np.ndarray) -> float:
    """Octonion norm ``sqrt(sum x_i^2)`` (Class K + Class C; never abs()).

    The norm form of the composition algebra. The sum-of-squares is reduced
    to a Python float, passed through the **scalar** Class K pin-slot
    magnitude (:func:`srmech.amsc.cascade.magnitude` — the cascade-honest
    replacement for ``abs()`` per
    ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``), then
    ``math.sqrt``. ``magnitude`` is SCALAR-ONLY (it raises on an ndarray),
    so the reduction to a scalar happens FIRST.

    Class K + Class C.

    Canonical SSoT: Baez (2002) §2.1 (``N(x) = x conj(x)``, the norm form).

    Args:
        x: An 8-vector octonion.

    Returns:
        The non-negative Euclidean norm.

    Raises:
        ValueError: if ``x`` is not shape ``(8,)``.
    """
    x = np.asarray(x, dtype=float)
    if x.shape != (_DIM,):
        raise ValueError(
            f"octonion_norm: x must be an 8-vector; got {x.shape}"
        )
    # Reduce to a SCALAR float first (cascade.magnitude raises on ndarray),
    # then the Class K pin-slot magnitude, then the square root. No abs().
    sum_sq = float(np.sum(x * x))
    return _rsqrt(_magnitude(sum_sq))


__all__ = [
    "octonion_conjugate",
    "octonion_left_mult",
    "octonion_mult_table",
    "octonion_norm",
    "octonion_right_mult",
    "octonion_table_attestation",
]
