"""Bidirectional JSON <-> native coercion for the MCP / Anthropic surface
(v0.5.0rc14).

THE PROBLEM (found by a live probe of the rc13 catalog): 65 of 158
``srmech`` tools were advertised to MCP / Anthropic consumers but were
*uncallable*, because their declared parameter (or return) types are
``bytes`` / ``np.ndarray`` / ``complex`` — types JSON-RPC cannot express.
A tool that *accepts* JSON but *returns* an un-serialisable ndarray is
equally unusable, so the fix is **bidirectional**:

* ``coerce_param(value, type_string)`` — JSON value -> the native Python
  type the resolved callable expects (the inbound direction).
* ``serialise_native(value)`` — a native Python result -> a
  JSON-serialisable value (the outbound direction).

Encoding conventions (user decision 2026-05-29)
-----------------------------------------------
* ``bytes``        <-> base64 ``str``  (unambiguous, binary-safe; the
  earlier hex convention was lossier to read and not what the rc14 wire
  format standardises on).
* ``np.ndarray``   <-> nested JSON ``list`` (row-major, ``.tolist()``);
  complex arrays carry each element as a ``[re, im]`` 2-list.
* ``complex``      <-> ``[re, im]`` 2-list (a bare JSON number decodes to
  ``complex(n, 0)``).
* numpy scalars (``np.int64`` / ``np.float64`` / ``np.uint8`` / ...) ->
  plain Python ``int`` / ``float`` on the outbound path.
* Container types recurse element-wise (see ``_PARAM_COERCERS``).

The inbound table is keyed on the *declared* ToolEntry type-string so a
ratchet (``test_all_param_types_json_coercible``) can assert every
advertised param type has a handler — no future tool can ship an
uncallable param type unnoticed. The outbound serialiser is *structural*
(it walks the actual Python value) because a result's concrete type is
not always pinned by the declared ``ToolReturn`` string (e.g. ``Any``).

dtype inference (inbound ndarray) — the documented caveat
---------------------------------------------------------
The generic inbound ``np.ndarray`` path builds a **real** array
(``np.asarray`` — ``float64`` if any float is present, ``int64`` for
all-ints). It deliberately does NOT auto-promote ``[re, im]`` leaves to a
complex array, because a real 2-column matrix (``[[1, 2], [3, 4]]``) is
shape-indistinguishable from a length-2 complex vector — guessing would
silently corrupt the far more common real-matrix ops (graph-Laplacian,
real-symmetric eigendecomposition, real 3-/4-vectors). Consequences:

* The real-array round-trip ``coerce_param(serialise_native(x)) == x`` is
  EXACT (values and shape).
* Complex-input ops stay correct too: each casts internally via
  ``np.ascontiguousarray(value, dtype=complex128)``, and a real symmetric
  matrix IS a valid Hermitian input — the real→complex128 promotion is
  lossless.
* The only input the generic path cannot express is an array carrying
  genuine *imaginary* parts. Single complex *scalars* ride as ``[re, im]``
  via the ``complex`` coercer; bulk complex *array* work is the
  by-reference handle path (per the package-for-bulk / MCP-for-interactive
  design boundary), not the JSON MCP path. The opt-in
  ``complex_pairs_to_ndarray`` builds a complex128 array from ``[re, im]``
  leaves for the round-trip test and any future explicitly-complex param.

By-reference handle dual-grammar (v0.5.0rc16) — now LIVE
--------------------------------------------------------
A ``SpectralHandle`` is a frozen, bytes-bearing dataclass JSON-RPC cannot
carry by VALUE. rc16 carries it BY REFERENCE: a producer tool's returned
handle is intercepted by ``serialise_native`` and emitted as a tagged id
object ``{"$srmech_handle": {"uuid", "name", "kind"}}`` (registered in the
package-scope ``srmech._handles`` registry); a consumer param of declared
type ``SpectralHandle`` / ``SpectralHandle | bytes`` is resolved back to the
live object by ``coerce_param``. The union still accepts a bare base64
``str`` for raw bytes. ``chiral_dual``'s ``op`` rides as an
``operator_name`` (a dotted ``srmech.*`` unary seq->seq operator name)
resolved through the same registry's name-grammar arm.
* Integer-typed ops (``klein4`` uint8 / ``polar`` int8) receive a
  ``float64`` / ``int64`` array and re-cast internally via
  ``np.asarray(..., dtype=...)`` in their own guards — round-trip equality
  holds on *values*, not on the intermediate JSON dtype.

Pure Python; no new C symbol; ABI unchanged.
"""

from __future__ import annotations

import base64
import binascii
from typing import Any, Callable, Dict, List, Tuple

# numpy-FREE (#564): the wire form for a former ``np.ndarray`` param/return is a
# plain nested JSON ``list`` (the numpy-free ops consume/return plain Python
# lists / :class:`srmech.amsc.mat.Mat` / :class:`srmech.amsc.hv.HV` / ``complex``
# now). No ``import numpy`` here — this was the LAST top-level numpy carrier.

# ``binascii.Error`` is what ``base64.b64decode(validate=True)`` raises on
# malformed input.
_BinasciiError = binascii.Error

# Module-scope cache for the lazily-imported ``SpectralHandle`` type, so
# ``serialise_native``'s outbound interception (which runs on every
# serialise of a non-leaf object) imports the type at most once. ``None``
# until first use; a sentinel ``False`` is never stored — a failed import
# simply leaves it ``None`` (no SpectralHandle in this build).
_SPECTRAL_HANDLE_TYPE: Any = None


def _spectral_handle_type() -> Any:
    """Return the ``SpectralHandle`` class (lazily imported + cached) or
    ``None`` if ``srmech.spectral`` is unavailable. Lazy/local so
    ``_coercion`` stays a leaf module at load (it is imported during warmup
    before the spectral surface is guaranteed wired)."""
    global _SPECTRAL_HANDLE_TYPE
    if _SPECTRAL_HANDLE_TYPE is None:
        try:
            from srmech.spectral import SpectralHandle as _SH
        except Exception:  # noqa: BLE001 — no spectral surface in this build
            return None
        _SPECTRAL_HANDLE_TYPE = _SH
    return _SPECTRAL_HANDLE_TYPE


# ──────────────────────────────────────────────────────────────────────
# Scalar element coercers (inbound: one JSON leaf -> one native leaf)
# ──────────────────────────────────────────────────────────────────────


def _b64_to_bytes(value: Any, *, param: str = "") -> bytes:
    """Decode a base64 ``str`` (the rc14 wire form for ``bytes``) to raw
    bytes. Tolerates a value that is *already* ``bytes`` (an in-process
    caller may pass raw bytes through ``invoke_tool``).
    """
    if isinstance(value, (bytes, bytearray)):
        return bytes(value)
    if not isinstance(value, str):
        raise ValueError(
            f"expected base64-encoded bytes for param {param or '<bytes>'!r}; "
            f"got {type(value).__name__}"
        )
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, _BinasciiError) as exc:
        raise ValueError(
            f"expected base64-encoded bytes for param {param or '<bytes>'!r}: "
            f"{exc}"
        ) from exc


def _to_complex(value: Any, *, param: str = "") -> complex:
    """Coerce a JSON value to ``complex``.

    Accepts ``[re, im]`` (a 2-element list/tuple), a bare JSON number
    (-> ``complex(n, 0)``), or a value that is already ``complex``.
    """
    if isinstance(value, complex):
        return value
    if isinstance(value, (int, float)):
        return complex(value, 0.0)
    if isinstance(value, (list, tuple)):
        if len(value) != 2:
            raise ValueError(
                f"expected [real, imaginary] (2 numbers) for complex param "
                f"{param or '<complex>'!r}; got length {len(value)}"
            )
        re_part, im_part = value
        return complex(float(re_part), float(im_part))
    raise ValueError(
        f"expected [real, imaginary] or a number for complex param "
        f"{param or '<complex>'!r}; got {type(value).__name__}"
    )


def _to_ndarray(value: Any, *, param: str = "") -> list:
    """Coerce a nested JSON list to a **real nested Python list** — the
    numpy-free (#564) wire form for the historical ``np.ndarray`` param.

    DTYPE CAVEAT (the documented round-trip caveat). A nested list of plain
    numbers stays REAL; the generic path does NOT auto-promote ``[re, im]``
    leaves to complex, because a real 2-column matrix (e.g.
    ``[[1, 2], [3, 4]]``) is shape-indistinguishable from a length-2 complex
    vector — guessing would corrupt the far more common real-matrix ops
    (graph-Laplacian, real symmetric eigendecomposition, real 3-/4-vectors).
    This makes the round-trip ``coerce_param(serialise_native(x)) == x``
    EXACT. The only thing the generic path cannot accept on input is a nested
    list carrying genuine *imaginary* parts — express those explicitly with
    :func:`_complex_pairs_to_ndarray` (the ``complex`` element coercer handles
    single complex scalars; bulk complex array work is the by-reference handle
    path, not the JSON MCP path)."""
    if isinstance(value, tuple):
        return [list(v) if isinstance(v, (list, tuple)) else v for v in value]
    return value


def _to_mat(value: Any, *, param: str = "") -> Any:
    """Coerce a nested JSON list-of-rows to a real :class:`srmech.amsc.mat.Mat`
    (the numpy-free 2-D carrier; v0.7.5rc72 ``mat_matmul`` bridge). A value
    already a ``Mat`` passes through unchanged.

    Same real-only caveat as :func:`_to_ndarray`: a nested list of plain numbers
    builds a REAL ``Mat`` (a 2-column real matrix is shape-indistinguishable from
    a length-2 complex vector, so the generic JSON path never guesses imaginary
    parts); genuine-complex ``Mat`` work rides the in-process / by-reference
    handle path, not the JSON MCP path."""
    from srmech.amsc.mat import Mat  # numpy-free carrier; lazy to avoid a cycle
    if isinstance(value, Mat):
        return value
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of rows for param {param or '<mat>'!r}; "
            f"got {type(value).__name__}"
        )
    return Mat.from_rows([list(r) for r in value], is_complex=False)


def _to_vec(value: Any, *, param: str = "") -> Any:
    """Coerce a flat JSON list to the **natural flat Python list** — the
    numpy-free wire form for a ``Vec``-typed (1-D carrier) param (v0.7.5rc132).

    The carrier is AGNOSTIC about input: every numpy-free op that takes a 1-D
    operand iterates it (``[float(x) for x in v]`` / ``Vec.from_sequence(v)`` /
    a length-n scan), so a flat ``list`` / ``tuple`` / ``array.array`` / ``Vec``
    are all accepted. The honest, minimal coercer therefore produces the flat
    Python structure (a ``list``) and lets the op's own acceptance handle the
    final carrier — never wraps numpy. A value already a ``Vec`` (an in-process
    caller) passes through unchanged."""
    from srmech.amsc.vec import Vec  # numpy-free 1-D carrier; lazy to avoid a cycle
    if isinstance(value, Vec):
        return value
    if isinstance(value, tuple):
        return list(value)
    return value


def _to_hv(value: Any, *, param: str = "") -> Any:
    """Coerce a flat JSON int list to the **natural flat Python list** — the
    numpy-free wire form for an ``HV``-typed (hypervector byte carrier) param
    (v0.7.5rc132).

    The carrier is AGNOSTIC about input: the hdc / genome / octonion ops that
    take a hypervector validate it through their own ``_as_klein4_buf`` /
    ``_as_polar`` / ``_as_loop`` (each iterates a ``list`` / ``tuple`` /
    ``array.array`` / ``HV`` / ``bytes`` and casts per-element), so the honest,
    minimal coercer produces the flat Python structure (a ``list``) and lets the
    op's own acceptance build the final ``HV`` / ``array('B')`` / ``list[float]``.
    A value already an ``HV`` (an in-process caller) passes through unchanged."""
    from srmech.amsc.hv import HV  # numpy-free hypervector carrier; lazy
    if isinstance(value, HV):
        return value
    if isinstance(value, tuple):
        return list(value)
    return value


def _to_poly(value: Any, *, param: str = "") -> Any:
    """Coerce a JSON value to the **natural ascending-degree coefficient form** for
    a ``Poly``-typed param (rc41 ``gosper`` term-ratio operands).

    The op's ``Poly`` acceptance (:meth:`srmech.amsc.poly.Poly.from_coeffs`) is
    AGNOSTIC about input: it iterates a coefficient sequence where each entry is
    an exact-rational coefficient — an ``int``, or a ``[num, den]`` integer pair
    (a 2-list JSON carries naturally). So the honest, minimal coercer produces the
    flat Python list and lets ``Poly.from_coeffs`` build the carrier — never a
    float (a Poly coefficient must be exact). A value already a ``Poly`` (an
    in-process caller) passes through unchanged."""
    from srmech.amsc.poly import Poly  # exact-ℚ polynomial carrier; lazy
    if isinstance(value, Poly):
        return value
    if isinstance(value, tuple):
        return list(value)
    return value


def _to_bipoly(value: Any, *, param: str = "") -> Any:
    """Coerce a JSON value to the natural form for a ``BiPoly``-typed param (rc42
    ``zeilberger`` bivariate term-ratio operands).

    A ``BiPoly`` is a polynomial in ``k`` whose coefficients are
    :class:`~srmech.amsc.poly.Poly` in ``n``. The op's coercion
    (:meth:`srmech.amsc.zeilberger.BiPoly.coerce`) accepts: a ``BiPoly`` (passes
    through); a ``Poly`` (read as a polynomial in ``k`` alone); or a
    ``k``-ascending list whose entries are each a Poly-in-n (an ``n``-coefficient
    list). So the honest, minimal coercer hands the natural nested list through —
    a JSON ``[[a, b], [c]]`` rides as k-slot 0 = Poly-in-n ``[a, b]``, k-slot 1 =
    ``[c]`` — and lets ``BiPoly.coerce`` build the carrier (never a float; a
    coefficient must be exact). A ``BiPoly`` / ``Poly`` / tuple passes naturally."""
    from srmech.amsc.zeilberger import BiPoly  # exact-ℚ bivariate carrier; lazy
    from srmech.amsc.poly import Poly
    if isinstance(value, (BiPoly, Poly)):
        return value
    if isinstance(value, tuple):
        return list(value)
    return value


def _to_tripoly(value: Any, *, param: str = "") -> Any:
    """Coerce a JSON value to the natural form for a ``TriPoly``-typed param (rc53
    ``apagodu_zeilberger`` trivariate term-ratio operands).

    A ``TriPoly`` is a polynomial in ``ℚ[n,j,k]`` — a ``j``-ascending tuple of
    :class:`~srmech.amsc.zeilberger.BiPoly` in ``(n,k)``. The op's coercion
    (:meth:`srmech.amsc.tripoly.TriPoly._as_tripoly`) accepts a ``TriPoly`` (passes
    through), a lower carrier (``BiPoly`` in ``(n,k)`` / ``Poly`` in ``k``), or the
    natural nested list. So the honest, minimal coercer hands the value through
    (tuple→list) and lets the op build the carrier (never a float; a coefficient
    must be exact). A ``TriPoly`` / ``BiPoly`` / ``Poly`` / tuple passes naturally."""
    from srmech.amsc.tripoly import TriPoly  # exact-ℚ trivariate carrier; lazy
    from srmech.amsc.zeilberger import BiPoly
    from srmech.amsc.poly import Poly
    if isinstance(value, (TriPoly, BiPoly, Poly)):
        return value
    if isinstance(value, tuple):
        return list(value)
    return value


def _to_qpoly(value: Any, *, param: str = "") -> Any:
    """Coerce a JSON value to the natural form for a ``QPoly``-typed param (rc55
    ``q_gosper`` q-hypergeometric term-ratio operands).

    A ``QPoly`` is a Laurent polynomial in ``x = qⁿ`` over ``ℚ[q]`` — an
    ascending-x sequence of :class:`~srmech.amsc.poly.Poly`-in-``q`` cells. The op's
    coercion (:func:`srmech.amsc.q_gosper._coerce_qpoly`) accepts a ``QPoly`` (passes
    through), a lower carrier (a ``Poly`` in ``q`` → an ``x**0`` cell), or the
    natural nested-list form (an ascending-x list of ``ℚ[q]`` coefficient cells). So
    the honest, minimal coercer hands the value through (tuple→list) and lets the op
    build the carrier (never a float; a coefficient must be exact). A ``QPoly`` /
    ``Poly`` / tuple passes naturally."""
    from srmech.amsc.qpoly import QPoly  # exact-ℚ[q] q-shift carrier; lazy
    from srmech.amsc.poly import Poly
    if isinstance(value, (QPoly, Poly)):
        return value
    if isinstance(value, tuple):
        return list(value)
    return value


def _to_qbipoly(value: Any, *, param: str = "") -> Any:
    """Coerce a JSON value to the natural form for a ``QBiPoly``-typed param (rc56
    ``q_zeilberger`` bivariate-q term-ratio operands).

    A ``QBiPoly`` is the q-analog of ``BiPoly`` — a polynomial in ``Y = qᵏ`` whose
    coefficients are :class:`~srmech.amsc.qpoly.QPoly` in ``X = qⁿ`` (over ``ℚ[q]``).
    The op's coercion (:meth:`srmech.amsc.qbipoly.QBiPoly.coerce`) accepts a
    ``QBiPoly`` (passes through), a ``QPoly`` (read as a polynomial in ``Y`` alone), a
    ``Poly`` in ``q`` (a scalar), or the natural nested-``Y``-degree list whose entries
    are each a ``QPoly``-in-``X`` (or QPoly-coercible cell). So the honest, minimal
    coercer hands the value through (tuple→list) and lets the op build the carrier
    (never a float; a coefficient must be exact). A ``QBiPoly`` / ``QPoly`` / ``Poly``
    / tuple passes naturally."""
    from srmech.amsc.qbipoly import QBiPoly  # exact bivariate-ℚ[q] carrier; lazy
    from srmech.amsc.qpoly import QPoly
    from srmech.amsc.poly import Poly
    if isinstance(value, (QBiPoly, QPoly, Poly)):
        return value
    if isinstance(value, tuple):
        return list(value)
    return value


def _to_ellratio(value: Any, *, param: str = "") -> Any:
    """Coerce a JSON value to the natural form for an ``EllRatio``-typed param (rc61
    ``elliptic_gosper`` elliptic-hypergeometric term-ratio operand).

    An ``EllRatio`` is a theta-quotient ``∏θ(αx;p)/∏θ(βx;p)`` over an exact-``ℚ``
    monomial prefactor. The op's coercion
    (:func:`srmech.amsc.elliptic_gosper._coerce_ratio`) accepts an ``EllRatio``
    (passes through) or a lower carrier (an ``EllMonomial`` → a pure-monomial ratio;
    a ``Theta`` → a single numerator theta). For a JSON caller the natural minimal
    operand is a single exact-``ℚ`` SCALAR (the elliptic-geometric constant ratio
    ``r = z``, the engine's canonical certifiable case): an int / ``(num, den)`` pair
    builds the scalar ``EllRatio.monomial(EllMonomial.scalar(z))``. An ``EllRatio`` /
    ``EllMonomial`` / ``Theta`` passes through (never a float; a coefficient must be
    exact)."""
    from srmech.amsc.ellbase import EllMonomial, EllRatio, Theta  # exact carrier; lazy
    from srmech.amsc.q import Q
    if isinstance(value, (EllRatio, EllMonomial, Theta)):
        return value
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return EllRatio.monomial(EllMonomial.scalar(Q(value, 1)))
    if (isinstance(value, (list, tuple)) and len(value) == 2
            and isinstance(value[0], int) and isinstance(value[1], int)
            and value[1] != 0):
        return EllRatio.monomial(EllMonomial.scalar(Q(value[0], value[1])))
    return value


def _to_mat_or_vec(value: Any, *, param: str = "") -> Any:
    """Coerce a ``Mat | Vec`` (shape-polymorphic) param: a nested list rides as
    a 2-D matrix, a flat list as a 1-D vector — both pass through as the natural
    Python structure (the numpy-free op's ``_as_rows`` / shape-polymorphic kernel
    inspects nesting). A ``Mat`` / ``Vec`` / tuple is accepted too; the op is the
    canonical validator (v0.7.5rc132)."""
    if isinstance(value, tuple):
        return list(value)
    return value


def _seq_vec(value: Any, *, param: str = "") -> List[Any]:
    """``Sequence[Vec]`` -> list of flat lists (each a 1-D operand; numpy-free
    wire form). The op iterates each element, so a flat ``list`` / ``tuple`` /
    ``Vec`` per slot is accepted (v0.7.5rc132)."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of 1-D vectors for param "
            f"{param or '<seq-vec>'!r}; got {type(value).__name__}"
        )
    return [_to_vec(v, param=param) for v in value]


def _seq_hv(value: Any, *, param: str = "") -> List[Any]:
    """``Sequence[HV]`` -> list of flat lists (each a hypervector; numpy-free
    wire form). The genome / hdc ops iterate each element, so a flat ``list`` /
    ``tuple`` / ``HV`` per slot is accepted (v0.7.5rc132)."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of hypervectors for param "
            f"{param or '<seq-hv>'!r}; got {type(value).__name__}"
        )
    return [_to_hv(v, param=param) for v in value]


def _tuple_mat(value: Any, *, param: str = "") -> Tuple[Any, ...]:
    """``tuple[Mat, ...]`` -> tuple of nested lists (the QM gauge / einsum ops
    take a *tuple* of matrices / arrays). Each element passes through as its
    natural nested-list structure; the op is the canonical validator. JSON has
    no tuple, so a list arrives and is re-tupled (v0.7.5rc132)."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of matrices for param "
            f"{param or '<tuple-mat>'!r}; got {type(value).__name__}"
        )
    return tuple(value)


def _seq_tuple(value: Any, *, param: str = "") -> List[tuple]:
    """``Sequence[tuple]`` -> list of re-tupled pairs (v0.7.5rc134). JSON has no
    tuple, so a list of ``[label, payload]`` pairs arrives and each is re-tupled
    so the op's ``for a, b in seq`` unpacking sees genuine tuples. Used by
    ``genome.chromosome(genes=[(label, leaves), ...])``; the op is the canonical
    validator of the pair contents (label str + leaves hypervector list)."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of pairs for param "
            f"{param or '<seq-tuple>'!r}; got {type(value).__name__}"
        )
    return [tuple(v) for v in value]


def _is_re_im_leaf(value: Any) -> bool:
    """True iff ``value`` is a ``[re, im]`` leaf — a length-2 sequence of
    plain numbers (not a nested container)."""
    return (
        isinstance(value, (list, tuple))
        and len(value) == 2
        and all(isinstance(x, (int, float)) and not isinstance(x, bool)
                for x in value)
    )


def _complex_pairs_to_ndarray(value: Any, *, param: str = "") -> Any:
    """Build a nested list of ``complex`` from nested ``[re, im]`` leaves — the
    numpy-free (#564) inverse of the outbound complex serialisation (each
    scalar rides as a 2-list ``[re, im]``). Used by round-trip tests and any
    op declaring an explicitly-complex array param; the generic
    :func:`_to_ndarray` deliberately does NOT call this (see its dtype caveat).
    """
    if _is_re_im_leaf(value):
        return complex(float(value[0]), float(value[1]))
    if isinstance(value, (list, tuple)):
        return [_complex_pairs_to_ndarray(v, param=param) for v in value]
    raise ValueError(
        f"complex ndarray param {param or '<ndarray>'!r}: innermost axis must "
        f"be [re, im] (length 2); got {type(value).__name__}"
    )


# ──────────────────────────────────────────────────────────────────────
# Inbound dispatch table: declared ToolEntry type-string -> coercer
#
# The KEY is the exact ``ToolParameter.type`` string. ``coerce_param``
# looks the param's declared type up here; a hit applies the coercer, a
# miss passes the value through unchanged (the callable is the canonical
# validator). The ratchet asserts EVERY declared param type has an entry
# here (pass-through types included), so no uncallable type slips by.
# ──────────────────────────────────────────────────────────────────────


def _identity(value: Any, *, param: str = "") -> Any:
    """Pass a JSON-native (or object-handle / pass-through) value through
    unchanged. The underlying callable validates it."""
    return value


def _seq_bytes(value: Any, *, param: str = "") -> List[bytes]:
    """``Sequence[bytes]`` / ``list[bytes]`` -> list of base64-decoded
    bytes."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of base64 strings for param "
            f"{param or '<seq-bytes>'!r}; got {type(value).__name__}"
        )
    return [_b64_to_bytes(v, param=param) for v in value]


def _seq_ndarray(value: Any, *, param: str = "") -> List[list]:
    """``Sequence[np.ndarray]`` -> list of nested lists (each from a nested
    JSON list; numpy-free wire form, #564)."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of nested arrays for param "
            f"{param or '<seq-ndarray>'!r}; got {type(value).__name__}"
        )
    return [_to_ndarray(v, param=param) for v in value]


def _tuple_ndarray(value: Any, *, param: str = "") -> Tuple[list, ...]:
    """``tuple[np.ndarray, ...]`` -> tuple of nested lists (the QM gauge ops
    take a *tuple* of generator matrices)."""
    return tuple(_seq_ndarray(value, param=param))


def _seq_complex(value: Any, *, param: str = "") -> List[complex]:
    """``list[complex]`` / ``Sequence[complex]`` -> list of ``complex`` (the
    rc36 ``dft`` / ``idft`` signal vector). Each element rides as ``[re, im]``
    (or a bare number for a real sample), matched to the outbound
    complex-list serialisation (``serialise_native`` emits each ``complex``
    as ``[re, im]``)."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of complex numbers for param "
            f"{param or '<seq-complex>'!r}; got {type(value).__name__}"
        )
    return [_to_complex(v, param=param) for v in value]


def _seq_seq_complex(value: Any, *, param: str = "") -> List[List[complex]]:
    """``list[list[complex]]`` -> list of rows of ``complex`` (the rc36
    ``kron`` matrix operands). Each row is a :func:`_seq_complex`; each scalar
    rides as ``[re, im]``."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of rows for param "
            f"{param or '<seq-seq-complex>'!r}; got {type(value).__name__}"
        )
    return [_seq_complex(row, param=param) for row in value]


def _mapping_bytes_bytes(value: Any, *, param: str = "") -> Dict[bytes, bytes]:
    """``Mapping[bytes, bytes]`` (``template.render``) -> dict of
    base64-decoded key -> base64-decoded value bytes."""
    if not isinstance(value, dict):
        raise ValueError(
            f"expected an object {{base64-key: base64-value}} for param "
            f"{param or '<map-bytes>'!r}; got {type(value).__name__}"
        )
    return {
        _b64_to_bytes(k, param=param): _b64_to_bytes(v, param=param)
        for k, v in value.items()
    }


def _list_tuple_bytes_int(
    value: Any, *, param: str = ""
) -> List[Tuple[bytes, int]]:
    """``list[tuple[bytes, int]]`` (``dispatch.match`` rules) -> list of
    (base64-bytes, int) tuples. Each element rides as ``[base64, int]``."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of [base64, int] pairs for param "
            f"{param or '<rules>'!r}; got {type(value).__name__}"
        )
    out: List[Tuple[bytes, int]] = []
    for i, pair in enumerate(value):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(
                f"param {param or '<rules>'!r}[{i}] must be a "
                f"[base64-bytes, int] pair"
            )
        out.append((_b64_to_bytes(pair[0], param=param), int(pair[1])))
    return out


def _list_tuple_bytes_bytes(
    value: Any, *, param: str = ""
) -> List[Tuple[bytes, bytes]]:
    """``list[tuple[bytes, bytes]]`` (``naming.lookup`` pairs) -> list of
    (base64-bytes, base64-bytes) tuples. Each element rides as
    ``[base64-key, base64-value]``."""
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"expected a list of [base64-key, base64-value] pairs for param "
            f"{param or '<pairs>'!r}; got {type(value).__name__}"
        )
    out: List[Tuple[bytes, bytes]] = []
    for i, pair in enumerate(value):
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError(
                f"param {param or '<pairs>'!r}[{i}] must be a "
                f"[base64-key, base64-value] pair"
            )
        out.append(
            (_b64_to_bytes(pair[0], param=param),
             _b64_to_bytes(pair[1], param=param))
        )
    return out


def _to_path(value: Any, *, param: str = "") -> Any:
    """``pathlib.Path`` <- str."""
    import pathlib
    if isinstance(value, pathlib.PurePath):
        return value
    return pathlib.Path(value)


def _to_int_tuple(value: Any, *, param: str = "") -> Tuple[int, ...]:
    """``tuple[int, int]`` <- a JSON list of ints (the rational ops take a
    ``(num, den)`` pair). JSON has no tuple; a list arrives."""
    if isinstance(value, tuple):
        return value
    if not isinstance(value, list):
        raise ValueError(
            f"expected a list for tuple param {param or '<int-tuple>'!r}; "
            f"got {type(value).__name__}"
        )
    return tuple(value)


# ──────────────────────────────────────────────────────────────────────
# rc16 — by-reference handle dual-grammar coercers
#
# A ``SpectralHandle`` is a frozen, bytes-bearing dataclass JSON-RPC cannot
# carry by VALUE; rc16 carries it BY REFERENCE as a tagged id object
# ``{"$srmech_handle": {"uuid", "name", "kind"}}`` minted by a producer tool
# and resolved through the package-scope ``srmech._handles`` registry. The
# cross-module touches are LOCAL (function-body) imports so ``_coercion``
# stays a leaf module at load (it is imported during warmup, before the
# spectral surface is guaranteed wired).
# ──────────────────────────────────────────────────────────────────────


def _resolve_spectral_handle(value: Any, *, param: str = "") -> Any:
    """Resolve a ``{"$srmech_handle": {...}}`` id object to the live
    :class:`srmech.spectral.SpectralHandle`. Tolerates a value that is
    ALREADY a ``SpectralHandle`` (an in-process caller may pass the real
    object through ``invoke_tool``, mirroring how :func:`_b64_to_bytes`
    tolerates raw bytes)."""
    from srmech._handles import (
        HANDLE_ENVELOPE_KEY,
        get_handle_registry,
        is_handle_envelope,
    )

    if is_handle_envelope(value):
        return get_handle_registry().resolve(
            value[HANDLE_ENVELOPE_KEY], kind="spectral"
        )
    # Already-native pass-through (the underlying fn validates it).
    return value


def _resolve_spectral_handle_or_bytes(value: Any, *, param: str = "") -> Any:
    """Discriminate the ``SpectralHandle | bytes`` union on JSON shape: a
    dict carrying the ``$srmech_handle`` sentinel -> registry-resolve to a
    ``SpectralHandle``; otherwise the existing base64-``str`` / raw-``bytes``
    path (raw-bytes callers preserved exactly — the union contract)."""
    from srmech._handles import is_handle_envelope

    if is_handle_envelope(value):
        return _resolve_spectral_handle(value, param=param)
    return _b64_to_bytes(value, param=param)


def _resolve_operator_name(value: Any, *, param: str = "") -> Any:
    """Resolve an ``operator_name`` (a dotted ``srmech.*`` unary
    sequence->sequence operator name) to its live callable via the
    registry's name-grammar arm. Tolerates an already-callable value for
    in-process callers."""
    if callable(value):
        return value
    from srmech._handles import resolve_operator_name

    return resolve_operator_name(value)


def _to_uint32_acc(value: Any, *, param: str = "") -> Any:
    """``array('I')`` / ``array('I')|None`` -> the §50 holographic-bundle
    accumulator (rc155). ``None`` passes through (the ``klein4_bundle_accumulate``
    create case); an ``array('I')`` rides unchanged (an in-process caller); a JSON
    list of ints — the cross-JSON wire form, matching ``serialise_native``'s
    ``array('I')`` -> ``list[int]`` — is rebuilt into ``array('I')``."""
    if value is None:
        return None
    from array import array as _array
    if isinstance(value, _array):
        return value
    if isinstance(value, (list, tuple)):
        return _array("I", [int(x) for x in value])
    raise ValueError(
        f"expected a list of uint32 ints (or None) for accumulator param "
        f"{param or '<acc>'!r}; got {type(value).__name__}"
    )


#: Declared-type-string -> inbound coercer. Pass-through (``_identity``)
#: entries are JSON-native or opaque-handle types that ``invoke_tool``
#: cannot meaningfully coerce — they are listed EXPLICITLY (not defaulted)
#: so the ratchet can prove every advertised type is accounted for.
_PARAM_COERCERS: Dict[str, Callable[..., Any]] = {
    # ── non-JSON scalar types (the core of the 65/158 fix) ──
    "bytes": _b64_to_bytes,
    "complex": _to_complex,
    # ── numpy-free carrier-spirit param types (v0.7.5rc132). The carrier is
    #    AGNOSTIC about input — the coercer produces the natural Python structure
    #    (nested list for Mat, flat list for Vec/HV) and the op's own acceptance
    #    builds the final carrier. NO numpy is ever named where a caller sees it. ──
    "Mat": _to_mat,            # v0.7.5rc72: numpy-free 2-D carrier (mat_matmul bridge)
    "Vec": _to_vec,            # v0.7.5rc132: numpy-free 1-D carrier
    "HV": _to_hv,              # v0.7.5rc132: numpy-free hypervector byte carrier
    "Poly": _to_poly,          # 0.9.0rc41: exact-ℚ polynomial carrier (gosper term ratio)
    "BiPoly": _to_bipoly,      # 0.9.0rc42: exact-ℚ[n,k] bivariate carrier (zeilberger ratios)
    "TriPoly": _to_tripoly,    # 0.9.0rc53: exact-ℚ[n,j,k] trivariate carrier (apagodu_zeilberger ratios)
    "QPoly": _to_qpoly,        # 0.9.0rc55: exact-ℚ[q] q-shift carrier (q_gosper q-term ratios)
    "QBiPoly": _to_qbipoly,    # 0.9.0rc56: exact bivariate-ℚ[q] carrier (q_zeilberger ratios)
    "EllRatio": _to_ellratio,  # 0.9.0rc61: exact modified-theta-quotient carrier (elliptic_gosper term ratio)
    "Optional[Vec]": _to_vec,
    "Optional[HV]": _to_hv,
    "Mat | Vec": _to_mat_or_vec,   # shape-polymorphic 2-D-or-1-D operand
    # ── the legacy ``np.ndarray`` keys are KEPT (no param advertises them any
    #    more, but the round-trip / wire-form tests still key off the historical
    #    type-string) — both map to the numpy-free nested-list coercer. ──
    "np.ndarray": _to_ndarray,
    "Optional[np.ndarray]": _to_ndarray,
    # ── container element-recursion ──
    "Sequence[bytes]": _seq_bytes,
    "list[bytes]": _seq_bytes,   # v0.7.0rc10: format.sha256_batch `datas`
    "Sequence[Vec]": _seq_vec,   # v0.7.5rc132: coupling.signed_sum_squared sources
    "Sequence[HV]": _seq_hv,     # v0.7.5rc132: genome / hdc bundle hypervector lists
    "Sequence[str]": _identity,  # v0.7.5rc155: hdc.cooccurrence_fold `tokens` (JSON-native)
    # v0.7.5rc155: the §50 holographic-bundle accumulator (klein4_bundle_accumulate
    # /_resolve) — a (1+2*D) uint32 array, or None for the create case.
    "array('I')": _to_uint32_acc,
    "array('I')|None": _to_uint32_acc,
    "tuple[Mat, ...]": _tuple_mat,  # v0.7.5rc132: gauge generators / einsum operands
    "Sequence[tuple]": _seq_tuple,  # v0.7.5rc134: genome.chromosome(genes=[(label, leaves), ...])
    "list[list[list[float]]]": _identity,  # rank-3 nested list, JSON-native (gauge f^abc)
    "list[list[int]]": _identity,  # v0.9.0rc44: modular_linalg.gf_rref `rows` matrix, JSON-native
    # ── legacy numpy-free Sequence/tuple keys kept for wire-form tests ──
    "Sequence[np.ndarray]": _seq_ndarray,
    "tuple[np.ndarray, ...]": _tuple_ndarray,
    "list[complex]": _seq_complex,            # v0.7.0rc36: spectral_cascades.{dft,idft}
    "list[list[complex]]": _seq_seq_complex,  # v0.7.0rc36: spectral_cascades.kron
    "Mapping[bytes, bytes]": _mapping_bytes_bytes,
    "list[tuple[bytes, int]]": _list_tuple_bytes_int,
    "list[tuple[bytes, bytes]]": _list_tuple_bytes_bytes,
    # ── JSON-native-ish that still want a light shape fix ──
    "pathlib.Path": _to_path,
    "tuple[int, int]": _to_int_tuple,
    "list[tuple[int, int]]": _identity,   # nested lists JSON-native
    # v0.7.5rc29: exact_dft.lift `spectrum` — the exact Z[zeta_N] spectrum is a
    # list of (real_vec, imag_vec) integer pairs; nested lists are JSON-native.
    "list[tuple[list[int], list[int]]]": _identity,
    # ── JSON-native scalars (explicit pass-through) ──
    "int": _identity,
    "Optional[int]": _identity,
    "float": _identity,
    "Optional[float]": _identity,
    "number": _identity,
    "bool": _identity,
    "str": _identity,
    "Optional[str]": _identity,
    "dict": _identity,
    "Optional[dict]": _identity,
    "list": _identity,
    "list[int]": _identity,
    "Optional[list[float]]": _identity,
    "iterable[int]": _identity,
    "sequence": _identity,
    "int | float | str | list | dict": _identity,
    # ── opaque in-process handle types (cannot ride JSON; the schema
    #    renders them as objects and an in-process caller passes the real
    #    object through). Listed so the ratchet stays exhaustive. ──
    "ChainSpec": _identity,
    # ── rc16 by-reference handle dual-grammar (was _identity in rc14/15;
    #    now REAL resolvers — the $srmech_handle envelope -> live object). ──
    "SpectralHandle": _resolve_spectral_handle,
    "SpectralHandle | bytes": _resolve_spectral_handle_or_bytes,
    #: ``operator_name`` is chiral_dual's ``op``: a dotted ``srmech.*`` unary
    #: seq->seq operator NAME resolved to its callable (rc16). ``callable``
    #: is RETAINED (other tools / the DSL / direct callers still pass a live
    #: callable; the exhaustiveness ratchet needs the key present).
    "operator_name": _resolve_operator_name,
    "callable": _identity,
    "numpy.random.Generator": _identity,
}


def has_coercer(type_string: str) -> bool:
    """True iff the inbound dispatch has an explicit handler for this
    declared type-string. The type-coercibility ratchet calls this for
    every advertised param type."""
    return type_string in _PARAM_COERCERS


def coerce_param(value: Any, type_string: str, *, param: str = "") -> Any:
    """Coerce one inbound JSON ``value`` to the native type its declared
    ``type_string`` names. A type with no registered coercer passes
    through unchanged (the underlying callable is the canonical
    validator).

    A JSON ``null`` (Python ``None``) always passes through unchanged —
    it means "absent / use the default" for an ``Optional[...]`` param,
    regardless of the declared element type (so an explicit ``null`` for
    an ``Optional[np.ndarray]`` stays ``None``, not a 0-d object array).
    """
    if value is None:
        return None
    coercer = _PARAM_COERCERS.get(type_string)
    if coercer is None:
        return value
    return coercer(value, param=param)


# ──────────────────────────────────────────────────────────────────────
# Outbound serialisation: native Python result -> JSON-serialisable value
#
# Structural (walks the value), because a result's concrete type is not
# always pinned by the declared ``ToolReturn`` string (``Any`` / union
# returns). Round-trippable for the scalar leaf types:
# ``coerce_param(serialise_native(x), <type>) == x`` for bytes / complex /
# ndarray (modulo ndarray dtype — see the module docstring caveat).
# ──────────────────────────────────────────────────────────────────────


def serialise_native(value: Any) -> Any:
    """Recursively convert a native Python result to a JSON-serialisable
    value.

    * ``bytes`` -> base64 ``str``
    * :class:`srmech.amsc.mat.Mat` -> nested list (complex -> ``[re, im]`` leaves)
    * ``complex`` -> ``[re, im]``
    * tuples / lists / sets -> list (recursed)
    * dicts -> dict (values recursed; keys base64'd if bytes)
    * ``pathlib.PurePath`` -> ``str``

    numpy-FREE (#564): the core ops return :class:`Mat` / :class:`HV` / nested
    ``list`` / ``complex`` — never ``np.ndarray`` — so there is no ndarray
    branch. A ``complex`` leaf (whether bare or inside a nested list) rides as
    ``[re, im]`` via the recursion.

    Anything else is returned unchanged for ``json.dumps`` to handle (or
    for the caller's ``default=`` fallback to catch).
    """
    # rc16 — SpectralHandle returns cross JSON BY REFERENCE. Intercept the
    # opaque frozen handle BEFORE the generic dataclass/dict fall-through
    # (which would otherwise base64 its inline ``coefficients_bytes`` and
    # leak the full payload): register it in the in-process handle registry
    # and emit the ``{"$srmech_handle": {uuid, name, kind}}`` id object the
    # LLM copies verbatim into the next tool's input. (Checked first so the
    # interception ordering is unambiguous.)
    _sh_type = _spectral_handle_type()
    if _sh_type is not None and isinstance(value, _sh_type):
        from srmech._handles import encode_envelope, get_handle_registry

        uuid_hex, name = get_handle_registry().register(value, kind="spectral")
        return encode_envelope(uuid_hex, name, "spectral")
    # bytes -> base64
    if isinstance(value, (bytes, bytearray)):
        return base64.b64encode(bytes(value)).decode("ascii")
    # complex -> [re, im]
    if isinstance(value, complex):
        return [value.real, value.imag]
    # srmech HV handle (numpy-free Klein-4 carrier, v0.7.0rc29) -> list[int].
    # The core ops return HV; cross JSON-RPC by value as a plain integer list.
    from srmech.amsc.hv import HV as _HV
    if isinstance(value, _HV):
        return value.tolist()
    # srmech Mat (numpy-free 2-D carrier, v0.7.5rc72) -> nested list. A complex
    # Mat serialises each entry as a ``[re, im]`` leaf via the recursion on the
    # nested list (Mat.tolist() yields a list[list[complex]]).
    from srmech.amsc.mat import Mat as _Mat
    if isinstance(value, _Mat):
        return serialise_native(value.tolist())
    # srmech Vec (numpy-free 1-D carrier, rc129) -> flat list. A complex Vec
    # serialises each entry as a ``[re, im]`` leaf via the recursion (Vec.tolist()
    # yields a flat list[float] / list[complex]). The 1-D peer of the Mat branch.
    from srmech.amsc.vec import Vec as _Vec
    if isinstance(value, _Vec):
        return serialise_native(value.tolist())
    # dict -> recurse (a bytes key serialises to its base64 string)
    if isinstance(value, dict):
        out: Dict[Any, Any] = {}
        for k, v in value.items():
            key = (
                base64.b64encode(bytes(k)).decode("ascii")
                if isinstance(k, (bytes, bytearray))
                else k
            )
            out[key] = serialise_native(v)
        return out
    # tuple / list / set -> list (recurse)
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialise_native(v) for v in value]
    # pathlib.Path -> str
    import pathlib
    if isinstance(value, pathlib.PurePath):
        return str(value)
    return value


__all__ = [
    "coerce_param",
    "has_coercer",
    "serialise_native",
    "complex_pairs_to_ndarray",
]


#: Public alias for the explicit ``[re, im]``-leaf -> complex128 array
#: coercer (the generic ``np.ndarray`` path stays real per its dtype
#: caveat; this is the opt-in complex-array builder for round-trip tests
#: and any future explicitly-complex array param).
complex_pairs_to_ndarray = _complex_pairs_to_ndarray
