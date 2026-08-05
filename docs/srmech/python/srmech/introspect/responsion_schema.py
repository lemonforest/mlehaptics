"""srmech.introspect.responsion_schema — the RESPONSION (relationship) introspection
surface (rc225; user design 2026-07-12) — the k=3 completion of the
introspection triad.

srmech is the **Stored-RELATIONSHIP Mechanism** — yet until rc225 only two of
its three faces were introspectable: :mod:`srmech.introspect.tool_schema` exposes
the OPS (the verbs — the A–N operator vocabulary) and
:mod:`srmech.introspect.carrier_schema` (rc205) exposes the OPERANDS (the nouns —
the carrier vocabulary). The relationships — the thing the mechanism is named
for — had no introspection face. ``responsion_schema`` is that face.

It is the k=3 completion NOT because it is a third peer-list, but because
ops + operands are the k=2 pair of NODES you can point at, and the responsion
is the **EDGE** that binds them: *this op, on this operand, answers THIS way*
(op⊗operand⊗responsion — the correcting/binding third; F1131/F1186).

The shape (the key IS the edge)
-------------------------------
Every entry is an EDGE keyed by the ``(operator, carrier)`` pair — the key
string is ``"<operator>|<carrier>"`` where ``<operator>`` is a real
``tool_schema`` key and ``<carrier>`` is a real ``carrier_schema()`` key
(validated at derivation time; a dangling ref raises). A flat noun-registry
(bare-name key) would flatten the one thing that is definitionally an edge —
the rc224 flatten-trap, one algebra up — so the value ALSO carries the two
refs first-class. One ``(operator, carrier)`` edge can carry MULTIPLE
responsions (e.g. ``laplacian.responsion`` on ``Mat`` carries BOTH the
propagator AND its Laplace-dual resolvent), so the value is a LIST::

    {
      "<operator>|<carrier>": [
        {
          "operator":     "<a valid tool_schema key>",
          "carrier":      "<a valid carrier_schema() key>",
          "kind":         "propagator" | "resolvent" | "closed_form"
                          | "open_sustain" | "trace" | "response_curve",
          "regime":       "continuous_spectral" | "discrete_algebraic",
          "answers_with": "<the response form>",
          "status":       "verified" | "open",
          "curvature":    "flat" | "curved",
        },
        ...
      ],
      ...
    }

The CURVATURE property (rc237, F3 — the schema lift of rc236's ``is_flat``)
----------------------------------------------------------------------------
``tool_schema : carrier_schema : responsion_schema :: connection : sections :
CURVATURE``. Per responsion, ``curvature`` records whether the op reads
frame-INDEPENDENTLY on that carrier (``"flat"`` — the curvature ``½[A,B]``
PROVABLY vanishes) or CAN carry a frame-dependent holonomy (``"curved"``). It
is DERIVED (never authored) via :func:`_curvature_class` and is SOUND: it says
``"flat"`` ONLY on the two airtight certificates — a COMMUTATIVE carrier
(``[A,B] ≡ 0`` by the ring axiom) or a ``kind == "trace"`` read (``Tr[A,B] ≡
0`` by cyclicity) — and defaults to the conservative ``"curved"`` everywhere
else (never a FALSE flat). The single ``Mat`` FLAT edge is ``heat_trace`` (the
trace invariant); ``the_one|One`` is CURVED — the winding holonomy F2
decomposes.

Two regimes of ONE responsion (hold the unity)
----------------------------------------------
The schema's whole job is to hold that the reduce-back and the
response-function are the discrete and continuous faces of ONE responsion:

* ``discrete_algebraic`` — the **F929 reduce-back rows**
  (:mod:`srmech.math.dispatch`): each row is a responsion (operand → verified
  closed form, or diverge = OPEN). The verified edges map each shipped
  reducer to its operand carrier (gosper⊗Poly, zeilberger/wz_certificate⊗
  BiPoly, apagodu_zeilberger⊗TriPoly, q_gosper⊗QPoly, q_zeilberger/
  q_wz_certificate⊗QBiPoly, elliptic_wz_certificate⊗EllRatio,
  multivariate_elliptic_jackson⊗EllMonomial,
  multivariate_elliptic_jackson_an⊗EllMonomial (rc227), resonant_spectrum⊗Mat,
  the_one⊗One). The OPEN edges are the rows' honest residues: the ``infer``
  router on each row's operand carrier, ``answers_with`` taken VERBATIM from
  :data:`srmech.math.dispatch._OPEN_HINTS` (the router's own
  candidate-next-theory hint — the F934 honest sustain; never a fabricated
  reduction). Editing a hint Python-side changes the canonical payload, so
  the hash-ratchet forces the C table to follow — the schema stays pinned to
  the dispatch SSoT.
* ``continuous_spectral`` — the **response-function ops** on a generator L
  excited by u0: ``laplacian.responsion`` (kind='propagator' ``e^{−zL}·u0``
  ⊗ kind='resolvent' ``(zI−L)^{-1}·u0`` — the LAPLACE-TRANSFORM DUAL PAIR on
  ONE edge), ``laplacian.propagate`` (the named EPH time-domain surface),
  ``laplacian.heat_trace`` (Θ(t) = Tr e^{−tL}, the read-independent
  summary), and ``laplacian.ground_state_flux_response`` (λ_min(Φ), the
  F1007 flux shadow — its Mat generator is the magnetic Laplacian built
  internally from the edge list).

The genome tie-back: storage = the carrier (the generator L holds the stored
relationship), query = the op (excite it), response = the responsion (how the
stored relationship answers). That is the mechanism the package name states.

Native dispatch: when the rc225 C peer is loaded (``srmech_responsion_schema``
over the compiled-in ``srmech_responsion_registry`` const table — GENERATED
by ``c/tools/gen_responsion_registry.py``, the rc205 carrier-registry codegen
model) and no profile tools are registered, :func:`responsion_schema` parses
the C canonical JSON — BYTE-IDENTICAL to ``json.dumps(<pure>,
sort_keys=True, separators=(",", ":"))`` (the sha256 hash-ratchet contract
locking the C table to this Python SSoT). A profile tool, a stale/absent
lib, or a non-OK status falls back to the pure path (never a wrong answer).

Pure data + a derivation over the dispatch/tool/carrier SSoTs — no numerical
kernel; no float math, no numpy, no ``abs()``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from srmech import _json as _srmech_json

__all__ = ["responsion_schema"]


# ── the authored VERIFIED discrete edges (the F929 reduce-back rows) ─────────
#
# (row, operator, carrier, answers_with) per shipped verified reducer. The
# row names must be keys of dispatch._OPEN_HINTS (validated); operator /
# carrier refs are validated against the live tool_schema / carrier registry.

_DISCRETE_VERIFIED: Tuple[Tuple[str, str, str, str], ...] = (
    ("cyclic",
     "srmech.cascade.the_one", "One",
     "the One S(σ,θ) — the (1,3,7,3)-partition Klein-4 generator, verified "
     "by its own structural invariants (partition + plane-counts + "
     "n1_is_sigma_only)"),
    ("spectral",
     "srmech.biology.coupling.resonant_spectrum", "Mat",
     "the resonant eigenspectrum payload of the coupling Laplacian — the "
     "reduction EXISTS iff L is bit-exact real-symmetric (the spectral "
     "theorem's own hypothesis, rc224); the eigenvalues are the operand, "
     "never the verdict"),
    ("sigma",
     "srmech.apokatastasis.gosper.gosper", "Poly",
     "the Gosper rational-certificate antidifference — the indefinite "
     "hypergeometric closed form (a non-None certificate IS the "
     "verification)"),
    ("sigma",
     "srmech.apokatastasis.zeilberger.zeilberger", "BiPoly",
     "the minimal-order creative-telescoping recurrence annihilating "
     "Σ_k F(n,k)"),
    ("sigma",
     "srmech.apokatastasis.wz_certificate.wz_certificate", "BiPoly",
     "the WZ identity PROOF certificate R(n,k) (accepted only when its own "
     "verified flag is True)"),
    ("sigma_multivar",
     "srmech.apokatastasis.apagodu_zeilberger.apagodu_zeilberger", "TriPoly",
     "the minimal-order annihilating recurrence for the 'sums of sums' "
     "Σ_{j,k} F(n,j,k) (Apagodu–Zeilberger creative telescoping)"),
    ("sigma_q",
     "srmech.apokatastasis.q_gosper.q_gosper", "QPoly",
     "the q-Gosper rational q-antidifference certificate — the indefinite "
     "q-hypergeometric closed form"),
    ("sigma_q",
     "srmech.apokatastasis.q_zeilberger.q_zeilberger", "QBiPoly",
     "the minimal-order q-creative-telescoping recurrence annihilating the "
     "definite q-sum"),
    ("sigma_q",
     "srmech.apokatastasis.q_wz_certificate.q_wz_certificate", "QBiPoly",
     "the q-WZ identity PROOF certificate (accepted only when its own "
     "verified flag is True)"),
    ("sigma_elliptic",
     "srmech.apokatastasis.elliptic_wz_certificate.elliptic_wz_certificate",
     "EllRatio",
     "the elliptic-WZ connection-coefficient PROOF of the very-well-poised "
     "₈ω₇ / ₁₀E₉ Frenkel–Turaev summation, closed form cf(n) (verified via "
     "the exact ThetaSum.is_zero decision)"),
    ("sigma_elliptic_multivar",
     "srmech.apokatastasis.elliptic_jackson.multivariate_elliptic_jackson",
     "EllMonomial",
     "the closed-form theta-quotient product of the balanced Cₙ elliptic "
     "Jackson n-fold sum (Rosengren Thm 2.1; per-call proof when in-budget, "
     "build-verified constructive form beyond the feasibility cap)"),
    ("sigma_elliptic_an",
     "srmech.apokatastasis.elliptic_jackson_an.multivariate_elliptic_jackson_an",
     "EllMonomial",
     "the closed-form theta-quotient of the Aₙ (type-A / Milne) elliptic "
     "Jackson simplex sum (Rosengren math/0305379 Eq. 6; per-call proof when "
     "in-budget, build-verified constructive form beyond the feasibility cap)"),
)

# ── the row → operand-carrier map for the honest-OPEN edges ──────────────────
#
# Each F929 row's OPEN residue is a responsion of the SAME regime on the
# infer router: infer on that row's operand carrier answers
# {"reducible": False, "candidate_next_theory": _OPEN_HINTS[row]} for shapes
# beyond the shipped reducer's reach. answers_with is taken VERBATIM from
# dispatch._OPEN_HINTS at derivation time (the dispatch SSoT). The un-keyed
# _OPEN_HINTS[None] residue ("no row matched") has no operand carrier and so
# no edge — it stays the router's own return, documented here honestly.

_INFER_OP = "srmech.math.dispatch.infer"

_ROW_OPEN_CARRIER: Tuple[Tuple[str, str], ...] = (
    ("cyclic", "One"),
    ("spectral", "Mat"),
    ("sigma", "BiPoly"),
    ("sigma_multivar", "TriPoly"),
    ("sigma_q", "QBiPoly"),
    ("sigma_elliptic", "EllRatio"),
    ("sigma_elliptic_multivar", "EllMonomial"),
    ("sigma_elliptic_an", "EllMonomial"),
)

# ── the authored CONTINUOUS response-function edges ──────────────────────────
#
# (operator, carrier, kind, answers_with). The generator L is the Mat carrier
# the response family acts on (ground_state_flux_response builds its magnetic
# Laplacian Mat internally from the edge list); the excitation u0 / the flux
# dial is the query. The responsion⊗Mat edge carries BOTH Laplace-dual
# members — the propagator (time domain) and the resolvent (frequency/energy
# domain) — on the ONE edge: the two-regimes-of-one-responsion unity, held.

_CONTINUOUS_VERIFIED: Tuple[Tuple[str, str, str, str], ...] = (
    ("srmech.math.laplacian.responsion", "Mat", "propagator",
     "e^{−zL}·u0 — the time-domain member (arg(z) the coherence dial: real "
     "→ thermal, imaginary → coherent, between → partial)"),
    ("srmech.math.laplacian.responsion", "Mat", "resolvent",
     "(zI−L)^{-1}·u0 — the frequency/energy-domain Green's function, the "
     "LAPLACE TRANSFORM of the propagator (per eigenmode e^{−z·λ} ⟷ "
     "1/(z−λ)); poles at spec(L)"),
    ("srmech.math.laplacian.propagate", "Mat", "propagator",
     "e^{−zL}·u0 — the named EPH surface (responsion kind='propagator' "
     "subsumes it as its time-domain member)"),
    ("srmech.math.laplacian.heat_trace", "Mat", "trace",
     "Θ(t) = Tr(e^{−tL}) = Σₖ e^{−t·λₖ} — the read-independent spectral "
     "summary (the trace of the propagator)"),
    ("srmech.math.laplacian.ground_state_flux_response", "Mat",
     "response_curve",
     "λ_min(Φ) — the magnetic ground state as a function of flux (the F1007 "
     "flux shadow), over the magnetic-Laplacian Mat built internally from "
     "the edge list"),
)

_REGIMES = ("continuous_spectral", "discrete_algebraic")
_STATUSES = ("verified", "open")


def _edge_key(operator: str, carrier: str) -> str:
    """The canonical edge key ``"<operator>|<carrier>"`` — pure ASCII (both
    refs are dotted/plain identifiers), so the C table's raw-name emission is
    byte-identical to the ensure_ascii canonical JSON key."""
    assert "|" not in operator and "|" not in carrier
    return operator + "|" + carrier


# ── the CURVATURE classification (rc237, F3) — the schema lift of rc236's
#    separate_frame_curvature `is_flat` (`tool_schema : carrier_schema :
#    responsion_schema :: connection : sections : CURVATURE`). Per (op, carrier)
#    edge, is the responsion FLAT (curvature PROVABLY vanishes → the op reads
#    frame-INDEPENDENTLY) or CURVED (it CAN carry a frame-dependent holonomy)? ─

#: Carriers whose algebra is COMMUTATIVE — every element commutes, so
#: ``[A, B] ≡ 0`` by the ring axiom → the rc236 curvature ``½[A,B]`` vanishes
#: IDENTICALLY → any responsion computed within them is FLAT. Poly / BiPoly /
#: TriPoly / QPoly / QBiPoly are commutative (q-)polynomial rings; EllRatio /
#: EllMonomial are commutative theta-quotient / monomial rings. (Mat is the
#: NON-commutative operator algebra; One carries the winding holonomy — neither
#: is here, so their non-trace responsions default to CURVED.)
_COMMUTATIVE_CARRIERS = frozenset({
    "Poly", "BiPoly", "TriPoly", "QPoly", "QBiPoly", "EllRatio", "EllMonomial",
})


def _curvature_class(carrier: str, kind: str) -> str:
    """FLAT vs CURVED for one (carrier, kind) responsion — SOUND (``"flat"``
    ONLY when the curvature PROVABLY always vanishes; ``"curved"`` is the
    conservative default, never a FALSE flat on a genuinely-curved pairing).

    Two airtight flat certificates (the schema lift of rc236's ``is_flat``):

    * **commutative carrier** — ``[A, B] ≡ 0`` by the ring axiom, so the rc236
      curvature ``½[A,B]`` vanishes IDENTICALLY: the responsion reads
      frame-INDEPENDENTLY → ``"flat"``.
    * **``kind == "trace"``** — the trace annihilates every commutator
      (``Tr[A,B] ≡ 0`` by cyclicity), so a trace responsion cannot EXPOSE
      curvature even on the non-commutative ``Mat`` operator carrier (the
      ``heat_trace`` Θ(t)=Tr e^{−tL} "read-independent" invariant) → ``"flat"``.

    Otherwise — a non-commutative operator carrier (``Mat`` / ``One``) read
    non-tracewise CAN carry a frame-dependent holonomy (the propagator's
    coherence-dial phase, the flux gauge, the ``One`` winding grading that F2
    decomposes) → ``"curved"`` (conservative; we do not certify frame-
    independence we cannot prove).
    """
    if carrier in _COMMUTATIVE_CARRIERS or kind == "trace":
        return "flat"
    return "curved"


def _entry(operator: str, carrier: str, kind: str, regime: str,
           answers_with: str, status: str) -> Dict[str, Any]:
    """One responsion dict (the edge payload's element shape). ``curvature``
    (rc237, F3) is the SOUND FLAT-vs-CURVED classification of this responsion —
    the schema lift of rc236's ``separate_frame_curvature`` ``is_flat`` — derived
    (never authored) from ``(carrier, kind)`` via :func:`_curvature_class`."""
    return {
        "operator": operator,
        "carrier": carrier,
        "kind": kind,
        "regime": regime,
        "answers_with": answers_with,
        "status": status,
        "curvature": _curvature_class(carrier, kind),
    }


def _validate_refs(edges: Dict[str, List[Dict[str, Any]]]) -> None:
    """Every responsion's ``operator`` must be a registered tool_schema key
    and its ``carrier`` a carrier registry key — the k=3 edge binds the k=2
    nodes; a dangling ref is a bug and raises (never ships silently)."""
    from ..introspect.carrier_schema import _CARRIERS
    from ..introspect.tool_schema import get_tool_schema, warmup_all

    warmup_all()
    tools = {t.name for t in get_tool_schema().tools}
    for key, responsions in edges.items():
        for r in responsions:
            if r["operator"] not in tools:
                raise RuntimeError(
                    f"responsion edge {key!r} references unregistered "
                    f"operator {r['operator']!r} (not a tool_schema key)")
            if r["carrier"] not in _CARRIERS:
                raise RuntimeError(
                    f"responsion edge {key!r} references unknown carrier "
                    f"{r['carrier']!r} (not a carrier_schema key)")
            if key != _edge_key(r["operator"], r["carrier"]):
                raise RuntimeError(
                    f"responsion edge key {key!r} does not match its "
                    f"(operator, carrier) refs — the key IS the edge")


def _pure_responsion_schema() -> Dict[str, List[Dict[str, Any]]]:
    """The pure-Python responsion schema (the SSoT the C const table is
    generated from and hash-ratcheted against): the (operator ⊗ carrier) →
    responsion relation derived from the F929 dispatch rows (verified
    reducers + the VERBATIM _OPEN_HINTS residues) and the response-function
    ops. Fresh (mutation-safe) structures each call; refs validated."""
    from ..math.dispatch import _OPEN_HINTS

    edges: Dict[str, List[Dict[str, Any]]] = {}

    def _add(operator: str, carrier: str, kind: str, regime: str,
             answers_with: str, status: str) -> None:
        edges.setdefault(_edge_key(operator, carrier), []).append(
            _entry(operator, carrier, kind, regime, answers_with, status))

    for row, operator, carrier, answers_with in _DISCRETE_VERIFIED:
        if row not in _OPEN_HINTS:
            raise RuntimeError(
                f"discrete responsion row {row!r} is not an F929 dispatch "
                f"row (not an _OPEN_HINTS key)")
        _add(operator, carrier, "closed_form", "discrete_algebraic",
             answers_with, "verified")

    for row, carrier in _ROW_OPEN_CARRIER:
        if row not in _OPEN_HINTS:
            raise RuntimeError(
                f"open responsion row {row!r} is not an F929 dispatch row "
                f"(not an _OPEN_HINTS key)")
        _add(_INFER_OP, carrier, "open_sustain", "discrete_algebraic",
             _OPEN_HINTS[row], "open")

    for operator, carrier, kind, answers_with in _CONTINUOUS_VERIFIED:
        _add(operator, carrier, kind, "continuous_spectral",
             answers_with, "verified")

    # Deterministic within-edge order (kind, then status, then text) so the
    # canonical payload — and the generated C table — never depend on
    # authored-tuple ordering.
    for responsions in edges.values():
        responsions.sort(
            key=lambda r: (r["kind"], r["status"], r["answers_with"]))

    _validate_refs(edges)
    return edges


def _native_responsion_schema() -> Optional[Dict[str, List[Dict[str, Any]]]]:
    """The rc225 C ``srmech_responsion_schema`` canonical JSON parsed to a
    dict, or ``None`` when the native peer is unavailable / returns non-OK
    (caller falls back to the pure path)."""
    try:
        from .. import _native
    except Exception:  # pragma: no cover — defensive; _native always imports
        return None
    raw = _native.responsion_schema_json_c()
    if raw is None:
        return None
    return _srmech_json.loads(raw.decode("utf-8"))


def responsion_schema() -> Dict[str, List[Dict[str, Any]]]:
    """The RESPONSION (stored-relationship) introspection registry (rc225;
    user design 2026-07-12) — the (operator ⊗ carrier) → responsion EDGE
    relation, keyed ``"<operator>|<carrier>"`` with both refs first-class in
    every entry; the k=3 completion binding tool_schema (verbs) and
    carrier_schema (nouns). See the module docstring for the full shape, the
    two regimes of one responsion, and the honest-OPEN derivation.

    Native-dispatched: when the rc225 C peer is loaded AND no profile tools
    are registered (the carrier_schema dispatch-gate pattern), the payload
    comes from the bare-C-host ``srmech_responsion_schema`` over the
    ``srmech_responsion_registry`` const table — VALUE-identical to the pure
    path (byte-identical in canonical form; the sha256 hash-ratchet in tests
    locks the two). Otherwise the pure path derives it live."""
    from ..introspect.tool_schema import _REGISTRY

    if not any(e.owner != "srmech" for e in _REGISTRY.values()):
        native = _native_responsion_schema()
        if native is not None:
            return native
    return _pure_responsion_schema()
