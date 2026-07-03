"""srmech.amsc.op_provenance — OPERATORS⊗OPERANDS as ONE addressable object
(rc117; the op-carrying carrier — dives #718 / #719 + the joint review).

The value of an inexact-frontier op (a float64 eigensolve, a series-truncate
readout) is a PROJECTION; the exact generating operation is the SSOT. This
module attaches the operation to the result — the two truths (operand /
operator, field / excitation) held in ONE addressable object — so that where
value-exactness is lost (asymptotic limits, float projections, platform
divergence), exactness stays ADDRESSABLE at the OPERATION level.

The provenance RECORD (hashed via the MPRRecord-style canonical byte image,
``json.dumps(record, sort_keys=True, ensure_ascii=False)`` → Class-A
``sha256_bytes``; C peer ``srmech_op_provenance_hash``):

.. code-block:: python

    {
      "op": "srmech.amsc.rational.sin_series_truncate",   # dotted op name
      "params": {...},          # ALL params, canonicalised (floats hex-tagged)
      "input_sha256": [...],    # per-input canonical-image hashes, sorted-key order
      "family": {"target_id": "sin(1/1)", "tower_kind": "interior"} | None,
      "rung": {...},            # the PRECISION-param subset of params
      "leaves_exact": True,     # every INPUT leaf bottoms out exact
      "chain_sha256": "<64hex>" # the record's own canonical hash (cached;
    }                           #   EXCLUDED from its own pre-image)

**FAMILY vs INSTANCE — resonator vs rung.** The ``family`` address is the
(asymptotic TARGET id, TOWER-KIND) pair; the instance is (family,
``chain_sha256``, ``rung``). ``tower_kind`` is a real two-valued choice from
the mathematics: ``"interior"`` (Taylor-type additive/smooth approach — the
series_truncate ops) vs ``"edge"`` (CF-type multiplicative/reciprocal
approach — best_rational continued-fraction convergents, and the Jacobi
eigensolve towers, whose rungs COMPOSE rotations rather than add terms).
Precision params (num_terms, max_denominator, tolerance, …) are the RUNG
INDEX in the declared tower — EXCLUDED from the family address, INCLUDED in
the instance. N truncations of one target = ONE family address + N instance
addresses: the asymptote is addressed by its generator.

**THE FAMILY NAMESPACE = the attestation registry (MPM as the
operation-identity authority).** A family ``target_id`` must be a
NAMED/ATTESTED object — either derived by the op's registered namer (e.g.
``"sin(1/1)"`` from the exact reduced input rational, or
``"eigvals(sha256:<hash>)"`` from an exact input matrix's content-address) or
supplied explicitly by the caller (who thereby attests the naming; the
op-intrinsic ``tower_kind`` is never overridable). Family-equality is
decidable exactly when targets are named; unnamed targets (e.g. a float-leaf
matrix) get NO family — instance-only addressing.

**EXACT LEAVES.** The carried operation's inputs must bottom out in exact
data (ints / rationals / strings / content-hash refs of exact carriers).
When an input leaf is a float / complex, the guarantee weakens to
same-op-on-same-bit-pattern — recorded honestly as ``leaves_exact: False``
(the float rides as its EXACT IEEE-754 bit pattern, ``float.hex``, so the
address is still well-defined and platform-stable).

**THE HONEST VERDICT PAIR (the load-bearing contract).**
Equality-of-programs is undecidable, so op-equality is ONE-SIDED:
:func:`op_verdict` returns ``"EQUAL"`` (identical canonical chain —
same generating program + same pinned inputs ⟹ same ideal object, SOUND) or
``"UNKNOWN"`` (different chain — NOT unequal; an algebraically-equal but
syntactically-different cascade hashes differently and honestly stays
UNKNOWN). :func:`family_verdict` returns ``"SAME_TARGET"`` / ``"UNKNOWN"``
with the same one-sidedness. NEITHER ever returns a false "UNEQUAL".

**Float-free canonical image by construction.** The canonical record bytes
contain NO raw JSON floats — a float is tagged ``{"__float64__":
float.hex(x)}``, an int beyond int64 ``{"__bigint__": "<decimal>"}``, a
rational ``{"__rational__": [num, den]}``, a complex ``{"__complex128__":
[re_hex, im_hex]}``, an exact-carrier reference ``{"__exact_ref__":
"<64hex>"}``. This keeps the Python and C canonical writers byte-identical
(C doubles render %.17g, not Python ``repr`` — so raw floats are REJECTED,
never silently forked).

srmech ops only: Class A ``sha256_bytes`` (content addressing), the
registered Class-N / Class-L runners (re-projection). numpy-free; no
``abs()``; no raw ``hashlib``.
"""

from __future__ import annotations

import json
from fractions import Fraction
from typing import Any, Callable, Dict, List, Optional, Tuple

from .format import sha256_bytes

__all__ = [
    "carry",
    "op_provenance_hash",
    "op_verdict",
    "family_verdict",
    "reproject",
]

# The two tower kinds (the real two-valued choice from the mathematics).
_TOWER_INTERIOR = "interior"   # Taylor-type additive/smooth approach
_TOWER_EDGE = "edge"           # CF-type multiplicative/reciprocal approach

# int64 domain of the C-side canonical writer (srmech_json INT is int64).
_INT64_MIN = -(2 ** 63)
_INT64_MAX = 2 ** 63 - 1

# The reserved single-key canonical tags (idempotent pass-through set).
_EXACT_TAGS = ("__bigint__", "__rational__", "__exact_ref__")
_INEXACT_TAGS = ("__float64__", "__complex128__")


# ──────────────────────────────────────────────────────────────────────
# Canonicalisation — the load-bearing boundary. "Same operation" ==
# identical canonical bytes of the record. Algebraically-equal but
# syntactically-different cascades canonicalise DIFFERENTLY and so hash
# differently → verdict UNKNOWN, never a false EQUAL.
# ──────────────────────────────────────────────────────────────────────

def _canon_bytes(obj: Any) -> bytes:
    """The MPRRecord-style canonical byte image: ``json.dumps(obj,
    sort_keys=True, ensure_ascii=False)`` UTF-8 encoded — the SAME
    convention ``MPRRecord.to_json_line`` and the genome manifest use, and
    the byte-parity contract of the C ``srmech_json_write_ws`` writer."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _is_tag(value: Any) -> Optional[str]:
    """Return the tag name when ``value`` is an already-canonical reserved
    single-key tag dict; else ``None`` (canonicalisation is idempotent)."""
    if isinstance(value, dict) and len(value) == 1:
        key = next(iter(value))
        if key in _EXACT_TAGS or key in _INEXACT_TAGS:
            return key
    return None


def _canon(value: Any) -> Tuple[Any, bool]:
    """Canonicalise ``value`` to a float-free JSON-shaped form.

    Returns ``(canonical, exact)`` where ``exact`` is True iff every leaf
    bottoms out in exact data (int / rational / str / bool / None /
    ``__exact_ref__``). Floats and complexes are tagged with their EXACT
    IEEE-754 bit pattern (``float.hex``) — well-defined and platform-stable,
    but honestly INEXACT leaves. Ints beyond int64 are tagged as decimal
    strings so the C canonical writer's int64 domain is never exceeded.
    """
    tag = _is_tag(value)
    if tag is not None:                     # already-canonical tag: idempotent
        return value, tag in _EXACT_TAGS
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value, True
    if isinstance(value, int):
        if _INT64_MIN <= value <= _INT64_MAX:
            return value, True
        return {"__bigint__": str(value)}, True
    if isinstance(value, float):
        return {"__float64__": value.hex()}, False
    if isinstance(value, complex):
        return (
            {"__complex128__": [value.real.hex(), value.imag.hex()]},
            False,
        )
    if isinstance(value, Fraction):
        num, _ = _canon(value.numerator)
        den, _ = _canon(value.denominator)
        return {"__rational__": [num, den]}, True
    # srmech Q (and any exact-rational scalar with int numerator/denominator
    # accessors) — duck-typed AFTER int/float so builtins take their branch.
    if (
        hasattr(value, "numerator") and hasattr(value, "denominator")
        and isinstance(getattr(value, "numerator"), int)
        and isinstance(getattr(value, "denominator"), int)
    ):
        num, _ = _canon(value.numerator)
        den, _ = _canon(value.denominator)
        return {"__rational__": [num, den]}, True
    if isinstance(value, (list, tuple)):
        out: List[Any] = []
        exact = True
        for item in value:
            c, e = _canon(item)
            out.append(c)
            exact = exact and e
        return out, exact
    if isinstance(value, dict):
        cd: Dict[str, Any] = {}
        exact = True
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError(
                    "op_provenance canonicalisation: dict keys must be str; "
                    f"got {type(k).__name__} key {k!r}")
            c, e = _canon(v)
            cd[k] = c
            exact = exact and e
        return cd, exact
    # Mat / Vec carriers project to their nested-list float readout (an
    # honestly INEXACT leaf set — the float64 buffer IS a projection).
    shape = getattr(value, "shape", None)
    if shape is not None and isinstance(shape, tuple):
        if len(shape) == 1:
            return _canon([value[i] for i in range(shape[0])])
        if len(shape) == 2:
            return _canon(
                [[value[i][j] for j in range(shape[1])]
                 for i in range(shape[0])])
    raise ValueError(
        "op_provenance canonicalisation: unsupported leaf type "
        f"{type(value).__name__} — pass int / float / str / bool / None / "
        "Fraction / Q / complex / list / dict / Mat / Vec, or an "
        "{'__exact_ref__': '<64hex>'} content-hash of an exact carrier")


def _decanon(value: Any) -> Any:
    """Reverse :func:`_canon`'s tags back to native Python values (the
    re-projection direction). ``__exact_ref__`` tags pass through opaque —
    a content-hash names an exact carrier but does not CARRY it."""
    tag = _is_tag(value)
    if tag == "__bigint__":
        return int(value["__bigint__"])
    if tag == "__float64__":
        return float.fromhex(value["__float64__"])
    if tag == "__rational__":
        num, den = value["__rational__"]
        return Fraction(_decanon(num), _decanon(den))
    if tag == "__complex128__":
        re_hex, im_hex = value["__complex128__"]
        return complex(float.fromhex(re_hex), float.fromhex(im_hex))
    if tag == "__exact_ref__":
        return value
    if isinstance(value, list):
        return [_decanon(v) for v in value]
    if isinstance(value, dict):
        return {k: _decanon(v) for k, v in value.items()}
    return value


def _validate_record_domain(value: Any, path: str = "record") -> None:
    """Reject record content OUTSIDE the canonical float-free domain —
    raw floats (C %.17g vs Python repr would silently fork the hash) and
    ints beyond int64 (outside the C parser's INT domain). The fix is the
    tag encoding: floats ride as {'__float64__': float.hex(x)}, big ints
    as {'__bigint__': '<decimal>'} — :func:`carry` does this for you."""
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return
    if isinstance(value, int):
        if _INT64_MIN <= value <= _INT64_MAX:
            return
        raise ValueError(
            f"op_provenance_hash: {path} holds an int beyond int64 "
            f"({value!r}) — tag it as {{'__bigint__': '{value}'}} so the "
            "canonical image stays inside the C writer's domain")
    if isinstance(value, float):
        raise ValueError(
            f"op_provenance_hash: {path} holds a raw float ({value!r}) — the "
            "canonical record image is float-free BY CONSTRUCTION (C doubles "
            "render %.17g, not Python repr, so a raw float silently forks "
            "the hash). Tag it as {'__float64__': float.hex(x)}; carry() "
            "does this canonicalisation for you")
    if isinstance(value, list):
        for i, item in enumerate(value):
            _validate_record_domain(item, f"{path}[{i}]")
        return
    if isinstance(value, dict):
        for k, v in value.items():
            if not isinstance(k, str):
                raise ValueError(
                    f"op_provenance_hash: {path} has a non-str key {k!r}")
            _validate_record_domain(v, f"{path}[{k!r}]")
        return
    raise ValueError(
        f"op_provenance_hash: {path} holds a non-JSON-shaped "
        f"{type(value).__name__} — records are canonical JSON-shaped dicts")


# ──────────────────────────────────────────────────────────────────────
# The canonical hasher (Class A; C peer srmech_op_provenance_hash).
# ──────────────────────────────────────────────────────────────────────

def _hash_native(record_min: Dict[str, Any]) -> Optional[str]:
    """Native dispatch: serialise the (chain-stripped) record and hand the
    bytes to ``srmech_op_provenance_hash`` (parse → canonical rewrite →
    ``srmech_sha256_hex``). Returns the 64-hex digest, or ``None`` on any
    missing symbol / non-OK status (caller runs the pure path)."""
    from . import _native
    if not (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_op_provenance_hash")
        and hasattr(_native.LIB, "srmech_op_provenance_hash_arena_bytes")
    ):
        return None
    import ctypes
    raw = json.dumps(record_min, ensure_ascii=False).encode("utf-8")
    ws_bytes = int(_native.LIB.srmech_op_provenance_hash_arena_bytes(
        ctypes.c_size_t(len(raw))))
    ws = (ctypes.c_char * ws_bytes)()
    out_hex = (ctypes.c_char * 65)()
    rc = _native.LIB.srmech_op_provenance_hash(
        raw, ctypes.c_size_t(len(raw)), ws, ctypes.c_size_t(ws_bytes),
        out_hex,
    )
    if rc != _native.SRMECH_OK:
        return None
    return out_hex.value.decode("ascii")


def op_provenance_hash(record: Dict[str, Any]) -> str:
    """The canonical provenance hasher (Class A): SHA-256 of the record's
    MPRRecord-style canonical byte image, EXCLUDING the record's own cached
    ``chain_sha256`` field (rc117; dive #718).

    The pre-image is ``json.dumps(record_minus_chain, sort_keys=True,
    ensure_ascii=False)`` UTF-8 bytes — the SAME canonicalisation
    ``MPRRecord.to_json_line`` and the genome manifest use, and the byte-
    parity contract of the C canonical writer, so the C peer
    ``srmech_op_provenance_hash`` (parse → canonical rewrite →
    ``srmech_sha256_hex``) produces the IDENTICAL digest from ANY JSON
    formatting of the same record (native-authoritative when present;
    pure Python the complete alternative).

    The record must be float-free canonical JSON (raw floats / ints beyond
    int64 are REJECTED with the tag-encoding fix named in the error —
    :func:`carry` builds records in this form). Two records hash equal IFF
    their canonical images are byte-identical: this hash IS the operation
    address :func:`op_verdict` compares.

    Raises:
        ValueError: non-dict record, raw float / beyond-int64 int /
            non-str key / non-JSON-shaped leaf anywhere in the record.
    """
    if not isinstance(record, dict):
        raise ValueError(
            f"op_provenance_hash: record must be a dict; got "
            f"{type(record).__name__}")
    record_min = {k: v for k, v in record.items() if k != "chain_sha256"}
    _validate_record_domain(record_min)
    native = _hash_native(record_min)
    if native is not None:
        return native
    return sha256_bytes(_canon_bytes(record_min))


# ──────────────────────────────────────────────────────────────────────
# The op registry — the name-keyed re-runnable operations (the genome
# op-log / DSL run_toml_chain model: re-run by name; only REGISTERED ops
# carry + re-project — the registry IS the contract).
# ──────────────────────────────────────────────────────────────────────

class _OpSpec:
    """One registered frontier op: how to run it, which params are the rung,
    which tower it climbs, and how its family target is named."""

    __slots__ = ("runner", "input_keys", "defaults", "rung_keys",
                 "tower_kind", "family_fn")

    def __init__(self, runner, input_keys, defaults, rung_keys, tower_kind,
                 family_fn):
        self.runner = runner
        self.input_keys = tuple(input_keys)
        self.defaults = dict(defaults)
        self.rung_keys = tuple(rung_keys)
        self.tower_kind = tower_kind
        self.family_fn = family_fn


def _reduced_point(inputs: Dict[str, Any]) -> str:
    """The reduced, sign-normalised exact rational point ``p/q`` a series /
    best_rational op is anchored at — the NAMED part of its family target.
    ``Fraction`` reduces and normalises the sign (den > 0), so ``sin(2/2)``
    and ``sin(1/1)`` name ONE target."""
    fr = Fraction(int(inputs["numerator"]), int(inputs["denominator"]))
    return f"{fr.numerator}/{fr.denominator}"


def _series_family(fn_label: str):
    def fam(inputs, canon_inputs, input_hashes, leaves_exact):
        if not leaves_exact:
            return None
        return {"target_id": f"{fn_label}({_reduced_point(inputs)})",
                "tower_kind": _TOWER_INTERIOR}
    return fam


def _series_runner(fn):
    def run(inputs, params):
        return fn(int(inputs["numerator"]), int(inputs["denominator"]),
                  int(params["num_terms"]))
    return run


def _matrix_family(label: str):
    """Family namer for the Class-L frontier: the target is the named
    spectral object of an EXACT input matrix, addressed by the matrix's
    canonical content-hash (the attestation-registry naming: an exact
    matrix IS a named object via its content address). Float-leaf inputs
    are UNNAMED targets → no family (instance-only)."""
    def fam(inputs, canon_inputs, input_hashes, leaves_exact):
        if not leaves_exact:
            return None
        h = sha256_bytes(_canon_bytes(canon_inputs["matrix"]))
        return {"target_id": f"{label}(sha256:{h})",
                "tower_kind": _TOWER_EDGE}
    return fam


def _jacobi_runner(inputs, params):
    from . import laplacian as _L
    return _L.jacobi_eigvals(inputs["matrix"],
                             max_sweeps=int(params["max_sweeps"]),
                             tolerance=float(params["tolerance"]))


def _symmetric_runner(inputs, params):
    from . import laplacian as _L
    return _L.symmetric_eigendecompose(inputs["matrix"])


def _hermitian_runner(inputs, params):
    from . import laplacian as _L
    return _L.hermitian_eigendecompose(inputs["matrix"])


def _heat_trace_runner(inputs, params):
    from . import laplacian as _L
    t = inputs["t"]
    if not isinstance(t, (int, float, list, tuple)):
        # An exact rational time (Fraction / Q) is the PINNED input; the
        # underlying float64 op consumes its float READOUT — exactly the
        # exact-operation / projected-value split this module carries.
        t = float(t)
    return _L.heat_trace(inputs["L"], t)


def _heat_trace_family(inputs, canon_inputs, input_hashes, leaves_exact):
    if not leaves_exact:
        return None
    h_l = sha256_bytes(_canon_bytes(canon_inputs["L"]))
    h_t = sha256_bytes(_canon_bytes(canon_inputs["t"]))
    return {"target_id": f"heat_trace(sha256:{h_l},sha256:{h_t})",
            "tower_kind": _TOWER_EDGE}


def _resonant_runner(inputs, params):
    from . import coupling as _coupling
    return _coupling.resonant_spectrum(inputs["L"],
                                       orders=int(params["orders"]),
                                       max_den=int(params["max_den"]))


def _resonant_family(inputs, canon_inputs, input_hashes, leaves_exact):
    if not leaves_exact:
        return None
    h = sha256_bytes(_canon_bytes(canon_inputs["L"]))
    return {"target_id": f"resonant_spectrum(sha256:{h})",
            "tower_kind": _TOWER_EDGE}


def _best_rational_runner(inputs, params):
    from . import rational as _rational
    return _rational.best_rational(int(inputs["numerator"]),
                                   int(inputs["denominator"]),
                                   int(params["max_denominator"]))


def _best_rational_family(inputs, canon_inputs, input_hashes, leaves_exact):
    if not leaves_exact:
        return None
    return {"target_id": f"rational({_reduced_point(inputs)})",
            "tower_kind": _TOWER_EDGE}


def _build_registry() -> Dict[str, _OpSpec]:
    from . import rational as _rational
    reg: Dict[str, _OpSpec] = {}
    # Class-N series-truncate family — the INTERIOR (Taylor additive) towers.
    # rung = num_terms (the truncation order).
    for label in ("sin", "cos", "exp", "log1p", "atan"):
        fn = getattr(_rational, f"{label}_series_truncate")
        reg[f"srmech.amsc.rational.{label}_series_truncate"] = _OpSpec(
            runner=_series_runner(fn),
            input_keys=("numerator", "denominator"),
            defaults={},
            rung_keys=("num_terms",),
            tower_kind=_TOWER_INTERIOR,
            family_fn=_series_family(label),
        )
    # Class-N best_rational — the EDGE (continued-fraction) tower; rung =
    # max_denominator (the CF convergent ceiling).
    reg["srmech.amsc.rational.best_rational"] = _OpSpec(
        runner=_best_rational_runner,
        input_keys=("numerator", "denominator"),
        defaults={},
        rung_keys=("max_denominator",),
        tower_kind=_TOWER_EDGE,
        family_fn=_best_rational_family,
    )
    # Class-L float64 frontier — EDGE towers (the Jacobi rung COMPOSES
    # Givens rotations; a multiplicative approach, not an additive one).
    reg["srmech.amsc.laplacian.jacobi_eigvals"] = _OpSpec(
        runner=_jacobi_runner,
        input_keys=("matrix",),
        defaults={"max_sweeps": 100, "tolerance": 1e-12},
        rung_keys=("max_sweeps", "tolerance"),
        tower_kind=_TOWER_EDGE,
        family_fn=_matrix_family("eigvals"),
    )
    reg["srmech.amsc.laplacian.symmetric_eigendecompose"] = _OpSpec(
        runner=_symmetric_runner,
        input_keys=("matrix",),
        defaults={},
        rung_keys=(),
        tower_kind=_TOWER_EDGE,
        family_fn=_matrix_family("eigensystem"),
    )
    reg["srmech.amsc.laplacian.hermitian_eigendecompose"] = _OpSpec(
        runner=_hermitian_runner,
        input_keys=("matrix",),
        defaults={},
        rung_keys=(),
        tower_kind=_TOWER_EDGE,
        family_fn=_matrix_family("eigensystem"),
    )
    reg["srmech.amsc.laplacian.heat_trace"] = _OpSpec(
        runner=_heat_trace_runner,
        input_keys=("L", "t"),
        defaults={},
        rung_keys=(),
        tower_kind=_TOWER_EDGE,
        family_fn=_heat_trace_family,
    )
    reg["srmech.amsc.coupling.resonant_spectrum"] = _OpSpec(
        runner=_resonant_runner,
        input_keys=("L",),
        defaults={"orders": 2, "max_den": 64},
        rung_keys=("orders", "max_den"),
        tower_kind=_TOWER_EDGE,
        family_fn=_resonant_family,
    )
    return reg


_REGISTRY: Optional[Dict[str, _OpSpec]] = None


def _registry() -> Dict[str, _OpSpec]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY


def _lookup(op: str) -> _OpSpec:
    reg = _registry()
    spec = reg.get(op)
    if spec is None:
        raise ValueError(
            f"op_provenance: unknown op {op!r} — the provenance registry "
            "covers the rc117 value-inexact frontier only; registered ops: "
            + ", ".join(sorted(reg)))
    return spec


# ──────────────────────────────────────────────────────────────────────
# carry — the attachment mechanism (the op-carrying carrier).
# ──────────────────────────────────────────────────────────────────────

def carry(
    op: str,
    inputs: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    *,
    family: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Run a registered frontier op AND attach its exact generating
    operation — the op-carrying carrier (rc117; dives #718/#719).

    Returns ``{"value": <the op's normal result>, "inputs": <canonicalised
    pinned inputs>, "provenance": <the record>}``. Existing op signatures
    are untouched — provenance is an OPT-IN entry point over a name-keyed
    registry (the genome op-log / DSL run_toml_chain re-run-by-name model),
    and the same registry powers :func:`reproject`.

    Args:
        op: the registered dotted op name (e.g.
            ``"srmech.amsc.rational.sin_series_truncate"``,
            ``"srmech.amsc.laplacian.jacobi_eigvals"``). Unknown ops raise
            ``ValueError`` naming the registered set — only registered
            operations carry (the registry IS the contract).
        inputs: the op's pinned operand inputs, keyed by name (the series
            ops take ``numerator``/``denominator``; the Class-L ops take
            ``matrix`` / ``L`` (+ ``t`` for heat_trace)). Leaves are
            canonicalised (floats → exact ``float.hex`` bit-pattern tags,
            honestly ``leaves_exact: False``).
        params: op parameters (e.g. ``num_terms``, ``tolerance``).
            Defaults are MATERIALISED into the record, so a default and an
            explicit-default call carry ONE operation address.
        family: optional explicit family naming ``{"target_id": <named
            target>}`` — the caller ATTESTS the target naming (e.g. a
            best_rational tower addressed at ``"sin(1/1)"``). The
            ``tower_kind`` is op-intrinsic and NOT overridable (passing one
            that contradicts the op's registered kind raises). When omitted,
            the op's registered namer derives the family (or ``None`` for
            unnamed/inexact targets — instance-only).

    Raises:
        ValueError: unknown op / missing or unknown input keys / unknown
            params / a malformed family override.
    """
    spec = _lookup(op)
    if not isinstance(inputs, dict):
        raise ValueError(
            f"carry: inputs must be a dict keyed by operand name; got "
            f"{type(inputs).__name__}")
    got, want = set(inputs), set(spec.input_keys)
    if got != want:
        raise ValueError(
            f"carry: {op} takes inputs {sorted(want)}; got {sorted(got)}")
    merged = dict(spec.defaults)
    for k, v in (params or {}).items():
        if k not in spec.defaults and k not in spec.rung_keys:
            raise ValueError(
                f"carry: {op} has no param {k!r} (params: "
                f"{sorted(set(spec.defaults) | set(spec.rung_keys))})")
        merged[k] = v
    missing = [k for k in spec.rung_keys if k not in merged]
    if missing:
        raise ValueError(
            f"carry: {op} needs rung param(s) {missing} (no default)")

    canon_inputs: Dict[str, Any] = {}
    leaves_exact = True
    for k in sorted(inputs):
        c, e = _canon(inputs[k])
        canon_inputs[k] = c
        leaves_exact = leaves_exact and e
    input_hashes = [
        sha256_bytes(_canon_bytes([k, canon_inputs[k]]))
        for k in sorted(canon_inputs)
    ]

    if family is not None:
        if (not isinstance(family, dict)
                or not isinstance(family.get("target_id"), str)
                or not family["target_id"]):
            raise ValueError(
                "carry: family override must be a dict with a non-empty "
                "str 'target_id' (the caller-attested named target)")
        kind = family.get("tower_kind", spec.tower_kind)
        if kind != spec.tower_kind:
            raise ValueError(
                f"carry: tower_kind is op-intrinsic — {op} climbs the "
                f"{spec.tower_kind!r} tower; a family override cannot "
                f"declare {kind!r}")
        fam = {"target_id": family["target_id"],
               "tower_kind": spec.tower_kind}
    else:
        fam = spec.family_fn(inputs, canon_inputs, input_hashes, leaves_exact)

    params_canon, _ = _canon(merged)
    rung = {k: params_canon[k] for k in spec.rung_keys}
    record: Dict[str, Any] = {
        "op": op,
        "params": params_canon,
        "input_sha256": input_hashes,
        "family": fam,
        "rung": rung,
        "leaves_exact": leaves_exact,
    }
    record["chain_sha256"] = op_provenance_hash(record)
    value = spec.runner(inputs, merged)
    return {"value": value, "inputs": canon_inputs, "provenance": record}


# ──────────────────────────────────────────────────────────────────────
# The honest verdict pair.
# ──────────────────────────────────────────────────────────────────────

_RECORD_CORE_KEYS = ("op", "params", "input_sha256")


def _as_record(p: Any, arg: str) -> Dict[str, Any]:
    """Accept a bare provenance record OR a full :func:`carry` result
    (unwrapped via its ``"provenance"`` key); validate the record core."""
    if isinstance(p, dict) and isinstance(p.get("provenance"), dict):
        p = p["provenance"]
    if not isinstance(p, dict):
        raise ValueError(
            f"op_provenance: {arg} must be a provenance record dict (or a "
            f"carry() result); got {type(p).__name__}")
    missing = [k for k in _RECORD_CORE_KEYS if k not in p]
    if missing:
        raise ValueError(
            f"op_provenance: {arg} is not a provenance record — missing "
            f"key(s) {missing}")
    return p


def op_verdict(p1: Any, p2: Any) -> str:
    """The honest one-sided op-equality verdict: ``"EQUAL"`` or
    ``"UNKNOWN"`` — NEVER a false "UNEQUAL" (rc117; dive #718).

    ``"EQUAL"`` iff the two provenances' canonical chain hashes agree
    (recomputed via :func:`op_provenance_hash`, never trusting the cached
    field): identical generating program + identical pinned inputs ⟹ the
    same ideal object BY CONSTRUCTION — sound even where the float
    readouts diverge in the last ulp (platform divergence is a projection
    artifact, not a different object). When ``leaves_exact`` is False the
    EQUAL means same-op-on-same-bit-pattern (stated in the records).

    ``"UNKNOWN"`` otherwise — equality of programs is undecidable, so a
    DIFFERENT chain proves nothing: an algebraically-equal but
    syntactically-different cascade, a different truncation rung, or a
    coincidentally-equal value from a different op all stay UNKNOWN
    (never a false EQUAL, never a false UNEQUAL). This asymmetry IS the
    contract.

    Accepts bare provenance records or full :func:`carry` results.
    """
    r1 = _as_record(p1, "p1")
    r2 = _as_record(p2, "p2")
    if op_provenance_hash(r1) == op_provenance_hash(r2):
        return "EQUAL"
    return "UNKNOWN"


def family_verdict(p1: Any, p2: Any) -> str:
    """The honest one-sided family verdict: ``"SAME_TARGET"`` or
    ``"UNKNOWN"`` — NEVER a false "DIFFERENT" (rc117; dive #719).

    ``"SAME_TARGET"`` iff BOTH provenances carry a family (a NAMED/ATTESTED
    target — the attestation-registry namespace) and the full family
    addresses agree: same ``target_id`` AND same ``tower_kind``. Every
    truncation rung of one target in one tower shares this address — the
    asymptote addressed by its generator.

    ``"UNKNOWN"`` otherwise. Note the tower distinction is part of the
    address: the SAME named target approached by the interior (Taylor) and
    the edge (continued-fraction) towers is two DIFFERENT families — the
    shared target is still visible by comparing the ``target_id`` fields
    directly, but this verdict speaks for the family address. Unnamed
    targets (``family: None`` — e.g. float-leaf inputs) are instance-only
    and always UNKNOWN here (family-equality is decidable exactly when
    targets are named).

    Accepts bare provenance records or full :func:`carry` results.
    """
    r1 = _as_record(p1, "p1")
    r2 = _as_record(p2, "p2")
    f1, f2 = r1.get("family"), r2.get("family")
    if (
        isinstance(f1, dict) and isinstance(f2, dict)
        and f1.get("target_id") and f1.get("target_id") == f2.get("target_id")
        and f1.get("tower_kind") == f2.get("tower_kind")
    ):
        return "SAME_TARGET"
    return "UNKNOWN"


# ──────────────────────────────────────────────────────────────────────
# reproject — the operation as SSOT.
# ──────────────────────────────────────────────────────────────────────

def reproject(
    provenance: Any,
    overrides: Optional[Dict[str, Any]] = None,
    inputs: Optional[Dict[str, Any]] = None,
    **rung_override: Any,
) -> Dict[str, Any]:
    """Re-run the carried operation at a (possibly different) rung — the
    value is RE-COMPUTED from the operation-as-SSOT (rc117; dive #718).

    ``provenance`` is a full :func:`carry` result (which carries the pinned
    ``inputs`` alongside the record) or a bare record plus an explicit
    ``inputs=`` dict. Either way the supplied inputs are RE-VERIFIED
    against the record's ``input_sha256`` before anything runs (the MPM
    re-verification: a provenance that can't be re-verified is broken).

    Rung overrides come as keyword args (or an ``overrides=`` dict — both
    merge; kwargs win). ONLY the op's declared rung (precision) params may
    be overridden — overriding a non-rung param would change the target,
    i.e. a different operation, not a re-projection. An EMPTY override
    re-derives the carried value verbatim from the operation. The family
    address is PRESERVED (rung-independent by construction), so the result
    is a new instance of the SAME family:
    ``family_verdict(carried, reproject(carried, ...)) == "SAME_TARGET"``.

    Returns a fresh ``{"value", "inputs", "provenance"}`` carry-result.

    Raises:
        ValueError: unregistered op / missing inputs / an input that fails
            hash re-verification / a non-rung override key.
    """
    if isinstance(provenance, dict) and isinstance(
            provenance.get("provenance"), dict):
        if inputs is None:
            inputs = provenance.get("inputs")
        provenance = provenance["provenance"]
    record = _as_record(provenance, "provenance")
    spec = _lookup(record["op"])
    if inputs is None:
        raise ValueError(
            "reproject: the record carries only input HASHES — pass the "
            "carry() result (which carries the pinned inputs) or an "
            "explicit inputs= dict to re-run the operation")
    canon_inputs: Dict[str, Any] = {}
    for k in sorted(inputs):
        canon_inputs[k], _ = _canon(inputs[k])
    rehashed = [
        sha256_bytes(_canon_bytes([k, canon_inputs[k]]))
        for k in sorted(canon_inputs)
    ]
    if rehashed != list(record["input_sha256"]):
        raise ValueError(
            "reproject: the supplied inputs do NOT re-verify against the "
            "record's input_sha256 — a provenance that can't be re-verified "
            "is broken (or these are different inputs)")
    merged_over = dict(overrides or {})
    merged_over.update(rung_override)
    bad = [k for k in merged_over if k not in spec.rung_keys]
    if bad:
        raise ValueError(
            f"reproject: {sorted(bad)} are not rung (precision) params of "
            f"{record['op']} (rung: {list(spec.rung_keys)}); overriding a "
            "non-rung param changes the target — that is a different "
            "operation, not a re-projection")
    params = _decanon(record["params"])
    params.update(merged_over)
    fam = record.get("family")
    fam_override = (
        {"target_id": fam["target_id"]} if isinstance(fam, dict) else None
    )
    return carry(record["op"], _decanon(canon_inputs), params,
                 family=fam_override)
