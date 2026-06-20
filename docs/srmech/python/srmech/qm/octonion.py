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

import ctypes
import functools
from srmech.amsc.rational import sqrt as _rsqrt  # §22: scalar root via Class-N
from typing import List, Sequence, Tuple

from srmech.amsc import _native  # rc122: numpy-free native loop-op dispatch
from srmech.amsc.cascade import magnitude as _magnitude
from srmech.amsc.format import sha256_bytes as _sha256_bytes
from srmech.amsc.mat import Mat  # rc122: numpy-free 2-D carrier for L_a / R_a

#: Octonion dimension (the real normed division algebra ``O``).
_DIM = 8

#: ctypes pointer alias for the native dim-8 loop-op marshalling (numpy-free).
_DBLP = ctypes.POINTER(ctypes.c_double)

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
def _build_mult_table() -> Tuple[Tuple[Tuple[int, ...], ...], ...]:
    """Generate the ``(8, 8, 8)`` int8 structure-constant tensor (cached).

    rc10: built from the Cayley-Dickson basis cocycle ``e_i·e_j = sign·e_{i⊕j}``
    via :func:`srmech.amsc.cascade.cd_basis_product` — the C primitive
    ``srmech_cd_basis_product`` when native is present, its pure-Python loop
    otherwise. Same fixed convention as the module docstring's generative rules
    (``_DOUBLING_RULE`` / ``_CONJ_RULE``); the int8 bytes are **identical** to the
    prior numpy build, so the content-address in
    :func:`octonion_table_attestation` (a SHA-256 over the table) is unchanged.

    rc122 (numpy-free): the tensor is a nested tuple of ints in ``{-1, 0, +1}``
    (``Mat`` is 2-D only, so the 8×8×8 rank-3 tensor stays nested Python — the
    same precedent as ``gauge``'s structure constants). Built exactly once and
    memoised as an IMMUTABLE nested tuple; :func:`octonion_mult_table` hands
    callers a fresh mutable nested-list COPY so the cache can never be mutated.
    """
    from srmech.amsc.cascade import cd_basis_product as _cd_basis_product
    table = [[[0] * _DIM for _ in range(_DIM)] for _ in range(_DIM)]
    for i in range(_DIM):
        for j in range(_DIM):
            idx, sign = _cd_basis_product(_DIM, i, j)
            table[i][j][idx] = int(sign)
    return tuple(tuple(tuple(row) for row in plane) for plane in table)


def octonion_mult_table() -> List[List[List[int]]]:
    """The ``(8, 8, 8)`` int8 structure-constant tensor ``C``.

    ``e_i * e_j = sum_k C[i][j][k] e_k`` under the fixed Cayley-Dickson-from-H
    convention (see module docstring). ``e_0`` is the identity;
    ``e_1^2 = ... = e_7^2 = -e_0``; the off-diagonal imaginary products
    anticommute. Built from the Cayley-Dickson basis cocycle
    (:func:`srmech.amsc.cascade.cd_basis_product`; the native
    ``srmech_cd_basis_product`` when present). The generation is memoised
    (:func:`_build_mult_table`); each call returns a fresh mutable copy (two
    calls are entry-identical but independent).

    Class A (content-addressing): the table is the MPR-attested constant
    that :func:`octonion_table_attestation` content-addresses.

    rc122 (numpy-free): returns a nested ``list`` (``Mat`` is 2-D only — a
    rank-3 tensor stays nested Python); index it ``C[i][j][k]`` (NOT ``C[i, j, k]``).

    Canonical SSoT: Baez (2002) §2 (the Fano-plane multiplication table).

    Returns:
        ``8×8×8`` nested ``list[list[list[int]]]``; ``C[i][j][k]`` is the ``e_k``
        coefficient of ``e_i * e_j`` (entries in ``{-1, 0, +1}``).
    """
    return [[list(row) for row in plane] for plane in _build_mult_table()]


def _table_int8_bytes() -> bytes:
    """C-order int8 serialization of the structure-constant tensor (numpy-free).

    Bit-identical to the prior numpy ``int8`` ``tobytes()`` serialization: 512
    bytes, one signed two's-complement byte per entry in C (row-major i, j, k)
    order (``-1 -> 0xFF``, ``0 -> 0x00``, ``+1 -> 0x01`` via ``v & 0xFF``). This keeps
    the :func:`octonion_table_attestation` ``response_sha256`` unchanged
    (Class A content-address) across the rc122 numpy-free flip.
    """
    table = _build_mult_table()
    out = bytearray(_DIM * _DIM * _DIM)
    pos = 0
    for i in range(_DIM):
        for j in range(_DIM):
            row = table[i][j]
            for k in range(_DIM):
                out[pos] = row[k] & 0xFF  # two's-complement signed byte; no abs()
                pos += 1
    return bytes(out)


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
    response_sha256 = _sha256_bytes(_table_int8_bytes())
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


def _as_octonion(v: Sequence[float], op: str) -> List[float]:
    """Coerce ``v`` to a plain ``list[float]`` of length 8 (numpy-free).

    Accepts any 1-D sequence (list / tuple / ndarray); a 2-D / wrong-length
    input raises the same ``ValueError`` the prior numpy ``asarray(...).shape``
    check produced. ``Mat`` is rejected here (these ops take a vector, not a
    matrix)."""
    if isinstance(v, Mat):
        raise ValueError(f"{op}: a must be an 8-vector; got a Mat {v.shape}")
    try:
        out = [float(c) for c in v]
    except TypeError as exc:  # 0-D scalar / non-iterable
        raise ValueError(f"{op}: a must be an 8-vector; got {v!r}") from exc
    if len(out) != _DIM:
        raise ValueError(f"{op}: a must be an 8-vector; got length {len(out)}")
    return out


def _loop_op_native_ready(symbol: str) -> bool:
    """True iff the native lib is loaded AND exports ``symbol`` (numpy-free)."""
    return bool(
        _native.HAS_NATIVE and _native.LIB is not None
        and hasattr(_native.LIB, symbol)
    )


def _try_native_loop_op(symbol: str, a: List[float]) -> List[List[float]]:
    """Dispatch a dim-8 loop operator (``srmech_loop_{left,right}_op_f64``) to the
    C peer, returning the ``8x8`` result as a nested ``list`` — or ``None`` to
    signal the numpy-free table fallback. Marshals through ctypes only (no numpy):
    the native flat output is row-major ``out[k*8 + j]`` = ``M[k][j]``."""
    if not _loop_op_native_ready(symbol):
        return None
    Arr = ctypes.c_double * _DIM
    MatC = ctypes.c_double * (_DIM * _DIM)
    c_a = Arr(*(float(v) for v in a))
    c_out = MatC()
    rc = getattr(_native.LIB, symbol)(
        ctypes.cast(c_a, _DBLP), ctypes.c_size_t(_DIM), ctypes.cast(c_out, _DBLP)
    )
    if rc != _native.SRMECH_OK:
        return None
    return [[float(c_out[k * _DIM + j]) for j in range(_DIM)] for k in range(_DIM)]


def octonion_left_mult(a: Sequence[float]) -> Mat:
    """Left-multiplication matrix ``L_a`` (``x -> a * x``) as an ``8x8`` real ``Mat``.

    Column ``j`` is ``a * e_j``; ``L_a[k, j] = sum_i a_i C[i, j, k]``. For an
    imaginary unit ``e_i`` (``i >= 1``) the matrix ``L_{e_i}`` is already
    antisymmetric, so it sits directly in ``so(8)`` (one of the 7 L-type
    coset directions of the ``28``).

    Class M (Clifford / HDC binding).

    Canonical SSoT: Baez (2002) §2.3-2.4 (left/right multiplication and the
    bimodule structure underlying triality).

    rc122 (numpy-free): dispatches to the C-backed ``srmech_loop_left_op_f64``
    (native when present; bit-identical numpy-free table fallback otherwise) and
    returns a real ``Mat`` (was an ndarray). ``L_a[k][j] = sum_i a_i C[i][j][k]``
    is bit-identical to the per-basis binds ``loop_left_op`` column-stacks (same
    Cayley-Dickson-from-H convention).

    Args:
        a: An 8-vector octonion (real components ``(a_0, ..., a_7)``).

    Returns:
        ``8x8`` real ``Mat`` ``L_a``.

    Raises:
        ValueError: if ``a`` is not an 8-vector.
    """
    a = _as_octonion(a, "octonion_left_mult")
    native = _try_native_loop_op("srmech_loop_left_op_f64", a)
    if native is not None:
        return Mat.from_rows(native, is_complex=False)
    table = _build_mult_table()
    rows = [[sum(a[i] * table[i][j][k] for i in range(_DIM)) for j in range(_DIM)]
            for k in range(_DIM)]
    return Mat.from_rows(rows, is_complex=False)


def octonion_right_mult(a: Sequence[float]) -> Mat:
    """Right-multiplication matrix ``R_a`` (``x -> x * a``) as an ``8x8`` real ``Mat``.

    Column ``j`` is ``e_j * a``; ``R_a[k, j] = sum_i a_i C[j, i, k]``. For an
    imaginary unit ``e_i`` (``i >= 1``) the matrix ``R_{e_i}`` is already
    antisymmetric (the other 7 R-type coset directions of the ``28``).

    Class M (Clifford / HDC binding).

    Canonical SSoT: Baez (2002) §2.3-2.4.

    rc122 (numpy-free): dispatches to the C-backed ``srmech_loop_right_op_f64``
    (native when present; bit-identical numpy-free table fallback otherwise) and
    returns a real ``Mat`` (was an ndarray). ``R_a[k][j] = sum_i a_i C[j][i][k]``.

    Args:
        a: An 8-vector octonion.

    Returns:
        ``8x8`` real ``Mat`` ``R_a``.

    Raises:
        ValueError: if ``a`` is not an 8-vector.
    """
    a = _as_octonion(a, "octonion_right_mult")
    native = _try_native_loop_op("srmech_loop_right_op_f64", a)
    if native is not None:
        return Mat.from_rows(native, is_complex=False)
    table = _build_mult_table()
    rows = [[sum(a[i] * table[j][i][k] for i in range(_DIM)) for j in range(_DIM)]
            for k in range(_DIM)]
    return Mat.from_rows(rows, is_complex=False)


def octonion_conjugate(x: Sequence[float]) -> List[float]:
    """Octonion conjugate ``conj(x) = (x_0, -x_1, ..., -x_7)``.

    Flips the sign of the seven imaginary axes (the scalar axis is fixed).
    Class C (chirality / orientation).

    Canonical SSoT: Baez (2002) §2.1 (conjugation and the norm form).

    rc122 (numpy-free): the Class-C imaginary-axis sign flip is a plain list
    comprehension (``-x_i`` for ``i >= 1``; no ``abs()``); returns a
    ``list[float]`` (was an ndarray).

    Args:
        x: An 8-vector octonion.

    Returns:
        The 8-vector conjugate as a ``list[float]``.

    Raises:
        ValueError: if ``x`` is not an 8-vector.
    """
    x = _as_octonion(x, "octonion_conjugate")
    return [x[0]] + [-x[i] for i in range(1, _DIM)]


def octonion_norm(x: Sequence[float]) -> float:
    """Octonion norm ``sqrt(sum x_i^2)`` (Class K + Class C; never abs()).

    The norm form of the composition algebra. The sum-of-squares is reduced
    to a Python float, passed through the **scalar** Class K pin-slot
    magnitude (:func:`srmech.amsc.cascade.magnitude` — the cascade-honest
    replacement for ``abs()`` per
    ``[[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]``), then the
    Class-N ``rational.sqrt``. ``magnitude`` is SCALAR-ONLY, so the reduction
    to a scalar happens FIRST.

    Class K + Class C.

    rc122 (numpy-free): the sum-of-squares is a pure-Python ``sum`` over the
    coerced ``list[float]`` (no numpy reduction).

    Canonical SSoT: Baez (2002) §2.1 (``N(x) = x conj(x)``, the norm form).

    Args:
        x: An 8-vector octonion.

    Returns:
        The non-negative Euclidean norm.

    Raises:
        ValueError: if ``x`` is not an 8-vector.
    """
    x = _as_octonion(x, "octonion_norm")
    # Reduce to a SCALAR float first (cascade.magnitude raises on a sequence),
    # then the Class K pin-slot magnitude, then the square root. No abs().
    sum_sq = sum(xi * xi for xi in x)
    return float(_rsqrt(_magnitude(sum_sq)))


__all__ = [
    "octonion_conjugate",
    "octonion_left_mult",
    "octonion_mult_table",
    "octonion_norm",
    "octonion_right_mult",
    "octonion_table_attestation",
]
