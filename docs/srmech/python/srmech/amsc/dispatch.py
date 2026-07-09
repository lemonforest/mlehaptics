"""Class D — late-binding / dispatch primitive (Task #217 Phase C1).

Single operation: :func:`match` — given an input byte sequence and an
ordered list of (pattern, tag) rules, find the first rule whose pattern
occurs in the input and return its tag. Multi-needle byte-pattern
dispatcher; the "select an implementation at runtime" primitive
expressed as a flat operation on bytes.

Class D is universal across srmech's Spike #24 cross-substrate audit
(instantiated at five of six bonus substrates). The C path
(``srmech_dispatch_match``) builds on Class G's byte search; the
pure-Python fallback uses ``bytes.find``.

API
---

- :func:`match(input, rules)` — ``rules`` is an iterable of
  ``(pattern_bytes, tag_int)`` pairs. Returns ``(matched: bool,
  tag: int)``. ``matched`` is False iff none of the patterns
  occurs in ``input``.
"""

from __future__ import annotations

import ctypes
import json
from typing import Any, Dict, Iterable, Optional, Tuple

from . import _native

__all__ = ["match", "mirror_pattern", "infer"]


def mirror_pattern(pattern: bytes) -> bytes:
    """Harmonic-2 chiral mirror of a dispatch pattern (F150): the byte-reversed
    needle. Class D is harmonic-2 (chiral inverse / self-inverse) per F150 §6.1
    — ``mirror_pattern(mirror_pattern(p)) == p`` (period 2). Matching a
    mirror-reversed input against the mirrored pattern yields the mirror match;
    the chirality-aware companion to :func:`match`. ``pattern`` is bytes-like.
    """
    if not isinstance(pattern, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"pattern must be bytes-like; got {type(pattern).__name__}"
        )
    p = bytes(pattern)
    if len(p) == 0:
        return b""
    if (
        _native.HAS_NATIVE
        and _native.LIB is not None
        and hasattr(_native.LIB, "srmech_mirror_pattern")
        and len(p) <= 0xFFFF_FFFF
    ):
        in_ptr = (ctypes.c_uint8 * len(p)).from_buffer_copy(p)
        out_buf = (ctypes.c_uint8 * len(p))()
        rc = _native.LIB.srmech_mirror_pattern(
            in_ptr,
            ctypes.c_uint32(len(p)),
            out_buf,
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(
                f"srmech_mirror_pattern returned non-OK status {rc}"
            )
        return bytes(out_buf)
    return p[::-1]


def match(input_bytes: bytes,
          rules: Iterable[Tuple[bytes, int]]) -> Tuple[bool, int]:
    """First-match dispatcher: return the tag of the first rule whose
    pattern occurs in ``input_bytes``.

    Both C and Python paths produce byte-exact identical results;
    pinned by ``tests/test_def_parity.py``.
    """
    if not isinstance(input_bytes, (bytes, bytearray, memoryview)):
        raise TypeError(
            f"input must be bytes-like; got {type(input_bytes).__name__}"
        )
    rule_list = [(bytes(p), int(t)) for (p, t) in rules]
    n_rules = len(rule_list)
    input_b = bytes(input_bytes)
    if _native.HAS_NATIVE and _native.LIB is not None:
        # Pack patterns into a contiguous buffer + parallel arrays.
        patterns_buf = bytearray()
        offsets = (ctypes.c_uint32 * max(n_rules, 1))()
        lengths = (ctypes.c_uint32 * max(n_rules, 1))()
        tags = (ctypes.c_uint32 * max(n_rules, 1))()
        for i, (p, t) in enumerate(rule_list):
            offsets[i] = len(patterns_buf)
            lengths[i] = len(p)
            tags[i] = t
            patterns_buf.extend(p)
        pat_buf_c = (
            (ctypes.c_uint8 * len(patterns_buf)).from_buffer_copy(bytes(patterns_buf))
            if len(patterns_buf) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        input_c = (
            (ctypes.c_uint8 * len(input_b)).from_buffer_copy(input_b)
            if len(input_b) > 0
            else ctypes.cast(None, ctypes.POINTER(ctypes.c_uint8))
        )
        out_matched = ctypes.c_bool(False)
        out_tag = ctypes.c_uint32(0)
        rc = _native.LIB.srmech_dispatch_match(
            input_c, ctypes.c_uint32(len(input_b)),
            pat_buf_c, offsets, lengths, tags,
            ctypes.c_uint32(n_rules),
            ctypes.byref(out_matched), ctypes.byref(out_tag),
        )
        if rc != _native.SRMECH_OK:
            raise RuntimeError(f"srmech_dispatch_match returned {rc}")
        return bool(out_matched.value), int(out_tag.value)
    # Pure-Python fallback: bytes.find iteration.
    for p, t in rule_list:
        if len(p) == 0:
            return True, t  # empty pattern matches at 0
        if input_b.find(p) >= 0:
            return True, t
    return False, 0


# =====================================================================
# §76+ — the F929 OPEN/infer router: ONE dispatch table over the three
# shipped closed-form reduction-theory rows (cyclic / spectral / Σ).
# =====================================================================
#
# F929 frame: the 14 A–N classes ARE a DISPATCH TABLE over closed-form
# reduction theories humans already built, each recognised as a cascade.
# Three reducer rows already ship in srmech:
#
#   * cyclic   row → ``cascade.the_one`` (the S(σ,θ) Klein-4 generator),
#   * spectral row → ``coupling.resonant_spectrum`` (Laplacian eigensolve),
#   * Σ        row → ``telescope`` = gosper / zeilberger / wz_certificate.
#
# ``infer`` is the META-dispatcher (a Class-D late-binding op, one rung up
# from :func:`match`) that makes the three rows ONE callable: it DETECTS
# which row a stored relationship matches, TRIES the matching reducer AND
# VERIFIES it actually reduced (reads the reducer's OWN verification — the
# wz_certificate ``verified`` flag, the resonant_spectrum force-orders
# Λ²≈L·L, the One ``(1,3,7,3)`` partition + ``n1_is_sigma_only`` invariant),
# and returns the verified closed form — else an honest ``OPEN``.
#
# It composes the EXISTING verified reducers — NO NEW MATH. ``infer`` runs
# no arithmetic of its own; every computation happens inside a reducer that
# already has its 1:1 C peer (srmech_resonant_spectrum / srmech_gosper /
# srmech_zeilberger / srmech_wz_verify). So this op is **non_compute**
# orchestration (the from_bodies / cooccurrence_edges precedent) — there is
# no ``srmech_infer`` C symbol and the #928 python_only_debt debt
# ceiling is untouched.
#
# The OPEN residue is the POINT: it makes the no-magic-numbers /
# no-hallucination discipline EXECUTABLE — ``infer`` NEVER returns
# ``reducible: True`` for a reduction it did not VERIFY. A relationship the
# current vocabulary cannot close comes back ``{reducible: False, …}`` with
# an honest candidate next-theory hint (the residue srmech is honest about,
# never fabricates a reduction for).

# The honest candidate-next-theory hints (kept SMALL + truthful — these name
# the documented next reduction-theory rows the framework has flagged but
# NOT yet shipped, per the post-§76 roadmap, NOT a fabricated promise).
_OPEN_HINTS: Dict[str, str] = {
    "sigma": "a definite/indefinite hypergeometric sum the telescope reducers "
             "did not close — try the multivariate (sums-of-sums) or "
             "q-hypergeometric Σ sub-rows, or a higher-order creative-telescoping",
    "sigma_multivar": "multivariate 'sums of sums' beyond the (n,j,k) Apagodu–"
                      "Zeilberger reach — a higher-arity TriPoly⁺ creative-"
                      "telescoping or a multibasic-q multisum reducer",
    "sigma_q": "a q-hypergeometric sum beyond the q-Gosper / q-WZ reach — the "
               "elliptic-hypergeometric (₈ω₇ / ₁₀E₉) sub-row (now shipped) or a "
               "multibasic q-multisum reducer",
    "sigma_elliptic": "an elliptic-hypergeometric sum beyond the very-well-poised "
                      "₈ω₇ / ₁₀E₉ Frenkel–Turaev reach — the multivariate Cₙ elliptic "
                      "Jackson row (now shipped — tag row='sigma_elliptic_multivar') or "
                      "a higher-genus theta reduction row",
    "sigma_elliptic_multivar": "a root-system elliptic multisum beyond the Cₙ elliptic "
                      "Jackson reach — an Aₙ (or other root-system) elliptic multisum or a "
                      "higher-genus theta multisum. (The exact per-call PROOF of the Cₙ "
                      "reduction now ships, rc101: the constructive closed form is verified "
                      "via the rc98/rc99 complete multi-variable elliptic is_zero, up to a "
                      "term-count feasibility cap; larger sums return the build-verified "
                      "constructive form with verified=None.)",
    "spectral": "directed / signed (magnetic) Laplacian spectral row, or a "
                "non-self-adjoint pencil generalized-eigenproblem reducer",
    "cyclic": "a higher Cayley–Dickson rung (sedenion S(σ,θ)) or a "
              "non-division-algebra cyclic-group reduction",
    None: "no row matched; candidate = a NEW reduction-theory row (the F929 "
          "dispatch table is extensible — add the matching reducer)",
}

# The structural-sniff keys for each untagged row (checked in this order;
# Σ before spectral before cyclic so the most specific payload wins).
_SIGMA_KEYS = ("rn_num", "rn_den", "rk_num", "rk_den")
_SIGMA_GOSPER_KEYS = ("term_ratio_num", "term_ratio_den")
# the two post-§76 Σ sub-rows. The multivariate "sums of sums" row
# Σ_{j,k} F(n,j,k) carries the SIX (n,j,k) TriPoly term-ratios — it shares the
# rn_*/rk_* pair with the ordinary Σ row but ADDS the rj_* pair, so this 6-key
# set is the most specific and is checked FIRST. The q-hypergeometric row uses
# q-prefixed keys (QBiPoly / QPoly q-ratios) that never collide with the others.
_SIGMA_MULTIVAR_KEYS = ("rn_num", "rn_den", "rj_num", "rj_den", "rk_num", "rk_den")
_SIGMA_Q_KEYS = ("qrn_num", "qrn_den", "qrk_num", "qrk_den")
_SIGMA_Q_GOSPER_KEYS = ("q_term_ratio_num", "q_term_ratio_den")
# the elliptic-hypergeometric Σ sub-row (₈ω₇ / ₁₀E₉). Its operand is the elliptic
# term-ratio as an EllRatio carrier under a single distinct key (theta-quotients
# have no simpler coefficient-list form) — never colliding with the other rows.
_SIGMA_ELLIPTIC_KEYS = ("elliptic_term_ratio",)
# the multivariate (root-system Cₙ) elliptic Jackson Σ sub-row. Its operand is NOT a
# single term-ratio but the eight balanced Cₙ VWP parameters (a,b,c,d,x,q + the partition
# ceiling N + the rank n) — e is fixed by the balancing bcde·x^{n-1}=a²q^{N+1}. The full
# 8-key set is distinctive (no other row carries all of a,b,c,d,x,q,N,n).
_SIGMA_ELLIPTIC_MULTIVAR_KEYS = ("a", "b", "c", "d", "x", "q", "N", "n")
_SPECTRAL_KEYS = ("laplacian", "adjacency", "edges", "matrix")
_CYCLIC_KEYS = ("sigma", "theta_num", "generator", "period")


def _detect_row(rel: Dict[str, Any]) -> Optional[str]:
    """Structural row-detector: read which reduction-theory row a stored
    relationship matches. An explicit ``row`` / ``kind`` tag wins; otherwise
    sniff the payload keys (Σ → spectral → cyclic, most-specific first).

    Returns ``"sigma"`` / ``"spectral"`` / ``"cyclic"``, or ``None`` (no row).
    """
    tag = rel.get("row", rel.get("kind"))
    if tag is not None:
        t = str(tag).strip().lower()
        if t in ("sigma_multivar", "multivar", "apagodu", "sums_of_sums"):
            return "sigma_multivar"
        if t in ("sigma_q", "q", "q_sigma", "q_hypergeometric", "qsum"):
            return "sigma_q"
        if t in ("sigma_elliptic_multivar", "elliptic_multivar", "cn_jackson",
                 "cn_elliptic_jackson", "multivariate_elliptic", "an_cn"):
            return "sigma_elliptic_multivar"
        if t in ("sigma_elliptic", "elliptic", "8w7", "10e9",
                 "elliptic_hypergeometric", "frenkel_turaev"):
            return "sigma_elliptic"
        if t in ("sigma", "Σ", "telescope", "sum"):
            return "sigma"
        if t in ("spectral", "laplacian", "coupling"):
            return "spectral"
        if t in ("cyclic", "klein4", "the_one", "modular"):
            return "cyclic"
        return None  # an explicit but unknown tag → honest OPEN
    # Untagged: sniff structure. Σ (a definite/indefinite hypergeometric sum)
    # is the most specific (named term-ratio operands). The two post-§76 Σ
    # sub-rows are MORE specific than the ordinary Σ row (multivar shares the
    # rn_*/rk_* pair but adds rj_*; q uses q-prefixed keys), so they win first.
    if all(k in rel for k in _SIGMA_MULTIVAR_KEYS):
        return "sigma_multivar"
    if (all(k in rel for k in _SIGMA_Q_KEYS)
            or all(k in rel for k in _SIGMA_Q_GOSPER_KEYS)):
        return "sigma_q"
    if all(k in rel for k in _SIGMA_ELLIPTIC_MULTIVAR_KEYS):
        return "sigma_elliptic_multivar"
    if all(k in rel for k in _SIGMA_ELLIPTIC_KEYS):
        return "sigma_elliptic"
    if all(k in rel for k in _SIGMA_KEYS) or all(k in rel for k in _SIGMA_GOSPER_KEYS):
        return "sigma"
    if any(k in rel for k in _SPECTRAL_KEYS):
        return "spectral"
    if any(k in rel for k in _CYCLIC_KEYS):
        return "cyclic"
    return None


def _reduced(row: str, reducer: str, closed_form: Any) -> Dict[str, Any]:
    """The VERIFIED-reduction return shape (the only path to ``reducible: True``)."""
    return {
        "reducible": True,
        "row": row,
        "reducer": reducer,
        "closed_form": closed_form,
        "verified": True,
    }


def _open(row: Optional[str], reason: str) -> Dict[str, Any]:
    """The honest OPEN return shape — a relationship the current vocabulary
    cannot CLOSE-and-VERIFY. Carries a truthful candidate next-theory hint."""
    return {
        "reducible": False,
        "row": None,
        "reason": reason,
        "candidate_next_theory": _OPEN_HINTS.get(row, _OPEN_HINTS[None]),
    }


def _try_sigma(rel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The Σ row — try the telescope reducers and VERIFY. A definite-sum
    relationship (the four (n,k) term-ratios) routes to ``wz_certificate``
    (the identity PROOF) and is accepted ONLY when its own ``verified`` flag
    is True; an indefinite term-ratio (single-variable) routes to ``gosper``
    and is accepted only when it returns a (non-None) rational certificate.
    Returns the reduced dict, or ``None`` to fall through to OPEN."""
    if all(k in rel for k in _SIGMA_KEYS):
        from . import wz_certificate as _wz  # lazy: avoids import cycle
        cert = _wz.wz_certificate(rel["rn_num"], rel["rn_den"],
                                  rel["rk_num"], rel["rk_den"])
        # VERIFY: trust ONLY the reducer's own verification flag (anti-
        # hallucination — never claim a reduction wz_certificate didn't prove).
        if cert is not None and cert.get("verified") is True:
            return _reduced("sigma", "wz_certificate", cert)
        return None  # not WZ-summable / not verified → honest OPEN
    # Indefinite hypergeometric summation (Gosper) — a single term-ratio.
    if all(k in rel for k in _SIGMA_GOSPER_KEYS):
        from . import gosper as _g  # lazy
        r = _g.gosper(rel["term_ratio_num"], rel["term_ratio_den"])
        if r is not None:  # a (non-None) certificate IS the verification here
            return _reduced("sigma", "gosper", r)
        return None
    return None


def _try_sigma_multivar(rel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The multivariate Σ sub-row — the (n,j,k) 'sums of sums' creative
    telescoping. Routes the six TriPoly term-ratios to ``apagodu_zeilberger``;
    a non-None minimal-order recurrence IS the verification (the op constructs
    it to annihilate ``Σ_{j,k} F(n,j,k)`` via the exact-ℚ QMat solve — the same
    'a (non-None) certificate is the proof' contract as gosper/zeilberger).
    Returns the reduced dict, or ``None`` to fall through to OPEN."""
    from . import apagodu_zeilberger as _az  # lazy: avoids import cycle
    rec = _az.apagodu_zeilberger(rel["rn_num"], rel["rn_den"],
                                 rel["rj_num"], rel["rj_den"],
                                 rel["rk_num"], rel["rk_den"])
    if rec is not None:
        return _reduced("sigma_multivar", "apagodu_zeilberger", rec)
    return None


def _try_sigma_q(rel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The q-hypergeometric Σ sub-row. A definite q-sum's four QBiPoly q-term-
    ratios route to ``q_wz_certificate`` (the q-identity PROOF; accepted ONLY
    when its own ``verified`` flag is True — the same anti-hallucination gate as
    the ordinary wz_certificate). An indefinite QPoly q-term-ratio routes to
    ``q_gosper`` (accepted iff it returns a rational q-antidifference cert).
    Returns the reduced dict, or ``None`` to fall through to OPEN."""
    if all(k in rel for k in _SIGMA_Q_KEYS):
        from . import q_wz_certificate as _qwz  # lazy
        cert = _qwz.q_wz_certificate(rel["qrn_num"], rel["qrn_den"],
                                     rel["qrk_num"], rel["qrk_den"])
        if cert is not None and cert.get("verified") is True:
            return _reduced("sigma_q", "q_wz_certificate", cert)
        return None  # not q-WZ / not verified → honest OPEN
    if all(k in rel for k in _SIGMA_Q_GOSPER_KEYS):
        from . import q_gosper as _qg  # lazy
        r = _qg.q_gosper(rel["q_term_ratio_num"], rel["q_term_ratio_den"])
        if r is not None:  # a (non-None) q-certificate IS the verification here
            return _reduced("sigma_q", "q_gosper", r)
        return None
    return None


def _try_sigma_elliptic(rel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The elliptic-hypergeometric Σ sub-row — the Frenkel–Turaev ₈ω₇ / ₁₀E₉
    very-well-poised summation (the TOP of the base-axis degeneration tower
    ordinary → q → elliptic). The ₈ω₇ term-ratio (an ``EllRatio``) under
    ``elliptic_term_ratio`` routes to ``elliptic_wz_certificate`` (the identity
    PROOF; accepted ONLY when its own ``verified`` flag is True — the same
    anti-hallucination gate as the ordinary / q ``wz_certificate``). The reduced
    payload carries the closed form ``cf(n)``. Returns the reduced dict, or
    ``None`` to fall through to OPEN."""
    from . import elliptic_wz_certificate as _ewz  # lazy: avoids import cycle
    cert = _ewz.elliptic_wz_certificate(rel["elliptic_term_ratio"])
    # VERIFY: trust ONLY the reducer's own verification flag (anti-hallucination —
    # the connection-coefficient induction certificate's ``verified`` is True only
    # when the inductive-step ThetaSum.is_zero decided ≡0 exactly).
    if cert is not None and cert.get("verified") is True:
        return _reduced("sigma_elliptic", "elliptic_wz_certificate", cert)
    return None  # not a canonical ₈ω₇ / not verified → honest OPEN


def _try_sigma_elliptic_multivar(rel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The multivariate (root-system Cₙ) elliptic Jackson Σ sub-row — the capstone one
    root-system rank above the ₈ω₇. The eight balanced Cₙ VWP parameters
    ``a, b, c, d, x, q`` (:class:`EllMonomial` or a symbol-name string) + the partition
    ceiling ``N`` + the rank ``n`` route to
    :func:`~srmech.amsc.elliptic_jackson.multivariate_elliptic_jackson`, which reduces the
    n-fold Cₙ sum to its closed-form theta-quotient product (Rosengren Thm 2.1).

    rc101 — a CONSTRUCTIVE→VERIFIED reducer: the router calls the op's ``verify=True`` path,
    which PROVES the reduction per call (builds the symbolic LHS n-fold sum and decides
    ``(LHS − closed).is_zero`` via the rc98/rc99 COMPLETE multi-variable elliptic decision),
    and SURFACES the ``verified`` status (``True`` / ``False`` / ``None``) in the returned
    dict. A ``True`` is a genuine per-call proof; ``None`` is the HONEST "sum too large to
    decide in-budget" (the term-count exceeded the op's feasibility cap — the closed form is
    still the MPM-verified Thm 2.1 RHS, so the reduction stands, it just was not re-proven
    per call). A ``False`` (the closed form provably does NOT equal the sum) is NOT a
    reduction — it routes to OPEN. Malformed params (``N < 1`` / ``n < 1`` / non-coercible)
    raise, and the caller routes to OPEN. The F929 anti-hallucination discipline: the router
    never claims ``reducible: True`` without either a per-call proof (``verified=True``) or the
    build-verified constructive closed form (``verified=None``)."""
    from . import elliptic_jackson as _ej  # lazy: avoids import cycle
    from .ellbase import EllMonomial as _M

    def _mono(v: Any) -> "Any":
        if isinstance(v, _M):
            return v
        if isinstance(v, str):
            return _M.symbol(v)             # the natural symbol-name operand
        if isinstance(v, int):
            from .q import Q
            return _M.scalar(Q(v, 1))       # a constant parameter
        raise TypeError("Cₙ Jackson parameter must be an EllMonomial / symbol name / int")

    result = _ej.multivariate_elliptic_jackson(
        _mono(rel["a"]), _mono(rel["b"]), _mono(rel["c"]), _mono(rel["d"]),
        _mono(rel["x"]), _mono(rel["q"]), int(rel["N"]), int(rel["n"]), verify=True)
    cf = result["closed_form"]
    verified = result["verified"]
    if verified is False:
        return None                         # provably NOT the sum → honest OPEN
    reduced = _reduced("sigma_elliptic_multivar", "multivariate_elliptic_jackson", cf)
    reduced["verified"] = verified          # surface the REAL status (True per-call proof,
    return reduced                          # or None = build-verified constructive, unproven)


def _try_spectral(rel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The spectral row — build the coupling Laplacian and run
    ``resonant_spectrum``, then VERIFY the reducer's own internal check:
    the force-orders satisfy Λ² ≈ L·L (the L² == V·diag(Λ²)·Vᵀ
    reconstruction the §75 op guarantees). Accept only when that holds."""
    from . import coupling as _c  # lazy
    from . import laplacian as _L
    from .mat import Mat

    L = _build_laplacian(rel, _L, Mat)
    if L is None:
        return None
    spec = _c.resonant_spectrum(L, orders=2)
    # VERIFY: the resonant_spectrum CONTRACT is force_orders[1] == L·L (the
    # biharmonic L² reconstructed from the ONE eigensolve). Re-derive L·L by
    # the Class-L matmul and compare — the reducer's own verification.
    fo = spec.get("force_orders") or []
    if len(fo) < 2:
        return None
    l1 = fo[0]                       # L¹  (= V·diag(Λ)·Vᵀ ≈ L)
    l2 = fo[1]                       # L²  (= V·diag(Λ²)·Vᵀ)
    if not _matrices_close(l2, _L.mat_matmul(l1, l1)):
        return None                 # the Λ² == L·L contract failed → OPEN
    return _reduced("spectral", "resonant_spectrum", spec)


def _try_cyclic(rel: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """The cyclic row — build ``the_one`` S(σ,θ) and VERIFY its structural
    invariants: the (1,3,7,3) A–N partition, the (0,1,3) plane-counts, and
    the n=1-is-σ-only prediction (θ inert at the ℂ rung). Accept only when
    all hold (the One's own self-consistency check)."""
    from .cascade import one as _one  # lazy

    sigma = int(rel.get("sigma", 1))
    theta_num = int(rel.get("theta_num", rel.get("period", 0)))
    theta_den = int(rel.get("theta_den", 1))
    if sigma not in (1, -1) or theta_den <= 0:
        return None
    one = _one.the_one(sigma, theta_num, theta_den)
    # VERIFY: the One's structural invariants (the cyclic-row's closed form is
    # the 14-D generator; its verification is the 1:3:7:3 substrate identity).
    if (one.partition == (1, 3, 7, 3)
            and one.plane_counts == (0, 1, 3)
            and one.n1_is_sigma_only):
        return _reduced("cyclic", "the_one", one)
    return None


def _build_laplacian(rel: Dict[str, Any], _L, Mat):
    """Coerce a spectral relationship's payload into a real-symmetric coupling
    Laplacian :class:`Mat` (or ``None`` if it can't be built). Accepts an
    explicit ``laplacian`` / ``matrix`` (square grid), an ``adjacency``
    (degree − A), or an ``edges`` list (with optional ``weights`` + ``n``)."""
    if "laplacian" in rel or "matrix" in rel:
        grid = rel.get("laplacian", rel.get("matrix"))
        rows = grid.tolist() if hasattr(grid, "tolist") else [list(r) for r in grid]
        n = len(rows)
        if n == 0 or any(len(r) != n for r in rows):
            return None
        return Mat.from_rows([[float(x) for x in r] for r in rows], is_complex=False)
    if "edges" in rel:
        edges = [(int(a), int(b)) for (a, b) in rel["edges"]]
        weights = rel.get("weights")
        n = rel.get("n")
        if n is None:
            n = 1 + max((max(a, b) for a, b in edges), default=-1)
        if weights is not None:
            return _L.dense_laplacian(int(n), edges, [float(w) for w in weights])
        return _L.dense_laplacian(int(n), edges)
    if "adjacency" in rel:
        a = rel["adjacency"]
        rows = a.tolist() if hasattr(a, "tolist") else [list(r) for r in a]
        n = len(rows)
        if n == 0 or any(len(r) != n for r in rows):
            return None
        # L = D − A (Class-L: degree on the diagonal, minus the adjacency).
        lap = [[0.0] * n for _ in range(n)]
        for i in range(n):
            deg = 0.0
            for j in range(n):
                deg += float(rows[i][j])
                lap[i][j] = -float(rows[i][j])
            lap[i][i] = deg + lap[i][i]
        return Mat.from_rows(lap, is_complex=False)
    return None


def _matrices_close(a, b, *, rel_tol: float = 1e-6) -> bool:
    """True iff two real :class:`Mat` agree entrywise to a relative tolerance —
    the resonant_spectrum Λ² == L·L verification (a float eigensolve compare,
    so a tolerance is correct here; the magnitude is read by Class-K comparison,
    never abs()). Shapes must match."""
    if a.shape != b.shape:
        return False
    n_rows, n_cols = a.shape
    for i in range(n_rows):
        for j in range(n_cols):
            av, bv = float(a[i, j]), float(b[i, j])
            diff = av - bv
            # |diff| by Class-K comparison (no abs()): the sign-folded magnitude.
            mag = diff if diff >= 0.0 else -diff
            scale = av if av >= 0.0 else -av
            bscale = bv if bv >= 0.0 else -bv
            if bscale > scale:
                scale = bscale
            if mag > rel_tol * (scale if scale > 1.0 else 1.0):
                return False
    return True


# ── rc176/rc192: the srmech_infer C-router dispatch (the ORCHESTRATION→C spine) ─
# ``infer`` routes the EXACT-SYMBOLIC bignum-carrier rows through the
# ``srmech_infer`` C peer when it is loaded: cyclic / sigma-gosper (rc176) and the
# sigma-DEFINITE wz_certificate row (rc192, the #796 payoff — the four (n,k)
# BiPoly term-ratios → zeilberger @order-1 FIND + wz_verify PROVE in the
# zeilberger-scale infer arena, over the rc191 srmech_carrier_read_bipoly reader).
# The C peer DETECTS + DISPATCHES + VERIFIES in C and returns the DECISION; the
# Python side reconstructs the closed_form via the SAME reducer the C peer
# verified (so native == pure, byte-identical). The remaining heavier-carrier rows
# (spectral / multivariate / q / elliptic → rc193+) are NOT marshalled, so the
# pure body runs (the rc103 inform-don't-limit pattern). The C router NEVER
# returns a false reducible — the honest OPEN residue is the no-hallucination
# discipline.

_SIGMA_GOSPER_ROW_KEYS = ("term_ratio_num", "term_ratio_den")


def _native_infer():
    """The native ``_native`` module IF the rc176 ``srmech_infer`` peer is present
    and bound, else ``None`` (so ``infer`` dispatches to C when available and falls
    cleanly to the pure-Python body — the complete alternative + the parity
    oracle). Honours the ``HAS_NATIVE`` toggle the parity tests flip."""
    probe = getattr(_native, "has_native_infer", None)
    return _native if (probe is not None and probe()) else None


def _marshal_relationship(rel: Dict[str, Any]) -> Optional[Tuple[str, int]]:
    """Marshal ``rel`` into ``(srmech_infer JSON, max_terms)`` IFF it is one of
    the two rc176 clean carrier-FFI rows (cyclic / sigma-gosper); else ``None`` (a
    heavier carrier deferred to rc177+ → the pure path). ``max_terms`` is the
    largest operand's coefficient count (the arena sizer). Bignums ride as decimal
    strings (the srmech_chain_run precedent). Reuses ``_detect_row`` for the
    correct most-specific-first row priority so a heavier row never misroutes."""
    row = _detect_row(rel)
    if row == "cyclic":
        sigma = int(rel.get("sigma", 1))
        theta_num = int(rel.get("theta_num", rel.get("period", 0)))
        theta_den = int(rel.get("theta_den", 1))
        return (json.dumps({"row": "cyclic", "sigma": sigma,
                            "theta_num": str(theta_num),
                            "theta_den": str(theta_den)}), 1)
    if row == "sigma" and all(k in rel for k in _SIGMA_GOSPER_ROW_KEYS):
        from .poly import Poly

        def _pairs(v: Any) -> "list":
            p = v if isinstance(v, Poly) else Poly.from_coeffs(v)
            return [[str(c.numerator), str(c.denominator)] for c in p.coeffs]

        num, den = _pairs(rel["term_ratio_num"]), _pairs(rel["term_ratio_den"])
        return (json.dumps({"row": "sigma", "term_ratio_num": num,
                            "term_ratio_den": den}), max(len(num), len(den), 1))
    # rc192 (#796 payoff): the SIGMA-DEFINITE (wz_certificate) row — the four
    # (n,k) BiPoly term-ratios, marshalled as k-ascending lists of Poly-in-n
    # coefficient lists (bignum-safe decimal strings). max_terms is the max
    # k-degree (the zeilberger degree). The C router runs zeilberger @order-1 +
    # wz_verify in its zeilberger-scale arena; _finish_native rebuilds via
    # _try_sigma (which routes the 4-key case to wz_certificate).
    if row == "sigma" and all(k in rel for k in _SIGMA_KEYS):
        from .zeilberger import BiPoly

        def _bp(v: Any) -> "list":
            b = BiPoly.coerce(v)
            return [[[str(c.numerator), str(c.denominator)] for c in kp.coeffs]
                    for kp in b.terms]

        rn_num, rn_den = _bp(rel["rn_num"]), _bp(rel["rn_den"])
        rk_num, rk_den = _bp(rel["rk_num"]), _bp(rel["rk_den"])
        deg = max(len(rn_num), len(rn_den), len(rk_num), len(rk_den), 1)
        return (json.dumps({"row": "sigma", "rn_num": rn_num, "rn_den": rn_den,
                            "rk_num": rk_num, "rk_den": rk_den}), deg)
    return None


def _finish_native(rel: Dict[str, Any], decision: Dict[str, Any]) -> Dict[str, Any]:
    """Build the ``infer`` return dict from the C router's DECISION. On
    ``reducible`` the closed_form OBJECT is materialised by re-running the SAME
    verified reducer (``_try_cyclic`` for the cyclic row / ``_try_sigma`` for BOTH
    the sigma-gosper indefinite AND the sigma-definite wz_certificate rows) —
    byte-identical to the pure path — so the C router acts as the routing brain a
    bare-C host uses while Python reconstructs the object. A defensive
    disagreement (native said reducible but the reducer rebuild returned None)
    routes to the honest OPEN."""
    row = decision.get("row")
    if decision.get("reducible") is True:
        res = _try_cyclic(rel) if row == "cyclic" else _try_sigma(rel)
        if res is not None:
            return res
    return _open(row, "not reducible in current vocabulary")


def infer(relationship: Dict[str, Any]) -> Dict[str, Any]:
    """The F929 OPEN/infer router — the meta-dispatcher over srmech's three
    shipped closed-form reduction-theory rows (cyclic / spectral / Σ).

    Given an arbitrary *stored relationship* (a descriptor dict), DETECT which
    reduction-theory row its structure matches, TRY the matching shipped
    reducer, VERIFY that the reducer actually reduced (read the reducer's OWN
    verification), and return the verified closed form — else return an honest
    ``OPEN``. ``infer`` composes the EXISTING verified reducers and runs NO new
    arithmetic; it NEVER returns ``reducible: True`` for a reduction it did not
    verify (the executable no-hallucination discipline, F929).

    Row detection (an explicit ``row`` / ``kind`` tag wins; else structural):

    * **Σ** (``row="sigma"`` / a hypergeometric sum) — the four bivariate
      term-ratios ``rn_num`` / ``rn_den`` / ``rk_num`` / ``rk_den`` of a definite
      sum ``Σ_k F(n,k)`` route to :func:`~srmech.amsc.wz_certificate.wz_certificate`
      (the identity PROOF; accepted iff its ``verified`` flag is True). A single
      indefinite term-ratio ``term_ratio_num`` / ``term_ratio_den`` routes to
      :func:`~srmech.amsc.gosper.gosper` (accepted iff it returns a certificate).
    * **Σ multivariate** (``row="sigma_multivar"``) — the SIX ``(n,j,k)`` TriPoly
      term-ratios (``rn_*`` / ``rj_*`` / ``rk_*``) of a "sums of sums"
      ``Σ_{j,k} F(n,j,k)`` route to
      :func:`~srmech.amsc.apagodu_zeilberger.apagodu_zeilberger` (accepted iff it
      finds a minimal-order annihilating recurrence).
    * **Σ q-hypergeometric** (``row="sigma_q"``) — a definite q-sum's four
      QBiPoly q-term-ratios (``qrn_*`` / ``qrk_*``) route to
      :func:`~srmech.amsc.q_wz_certificate.q_wz_certificate` (accepted iff its
      ``verified`` flag is True); an indefinite QPoly q-term-ratio
      (``q_term_ratio_*``) routes to :func:`~srmech.amsc.q_gosper.q_gosper`.
    * **Σ elliptic-hypergeometric** (``row="sigma_elliptic"``) — the top of the
      base-axis tower (ordinary → q → elliptic). The Frenkel–Turaev ₈ω₇ / ₁₀E₉
      term-ratio (an ``EllRatio`` under ``elliptic_term_ratio``) routes to
      :func:`~srmech.amsc.elliptic_wz_certificate.elliptic_wz_certificate` (the
      identity PROOF; accepted iff its ``verified`` flag is True, and the reduced
      payload carries the closed form ``cf(n)``).
    * **Σ multivariate elliptic** (``row="sigma_elliptic_multivar"`` / the eight
      ``a`` / ``b`` / ``c`` / ``d`` / ``x`` / ``q`` / ``N`` / ``n`` keys) — the
      capstone one root-system rank above the ₈ω₇: the balanced Cₙ elliptic Jackson
      summation routes to
      :func:`~srmech.amsc.elliptic_jackson.multivariate_elliptic_jackson` with
      ``verify=True``, which CONSTRUCTS the closed-form theta-quotient product (Rosengren
      Thm 2.1) AND (rc101) PROVES it per call — building the symbolic LHS n-fold sum and
      deciding ``(LHS − closed).is_zero`` via the rc98/rc99 complete multi-variable elliptic
      decision. The reduced dict SURFACES ``verified`` (``True`` = per-call proof, ``None`` =
      build-verified constructive form beyond the feasibility cap); a ``False`` (closed form
      provably ≠ the sum) routes to OPEN.
    * **spectral** (``row="spectral"`` / a graph payload) — an ``edges`` list
      (with optional ``weights`` + ``n``), an ``adjacency`` grid, or an explicit
      ``laplacian`` / ``matrix`` build a coupling Laplacian and route to
      :func:`~srmech.amsc.coupling.resonant_spectrum`; accepted iff the
      force-orders satisfy the ``L² == L·L`` contract (the reducer's own check).
    * **cyclic** (``row="cyclic"`` / a ``sigma`` / ``theta_num`` / ``period`` /
      ``generator`` payload) — builds the One ``S(σ,θ)`` via
      :func:`~srmech.amsc.cascade.one.the_one`; accepted iff the ``(1,3,7,3)``
      partition + ``(0,1,3)`` plane-counts + ``n1_is_sigma_only`` invariants hold.

    Args:
        relationship: a descriptor dict. May carry an explicit ``row`` / ``kind``
            tag, plus the row-specific payload keys above.

    Returns:
        On a VERIFIED reduction::

            {"reducible": True, "row": "<row>", "reducer": "<name>",
             "closed_form": <reducer output>, "verified": True}

        On no match / no verified reduction (the honest OPEN residue)::

            {"reducible": False, "row": None,
             "reason": "not reducible in current vocabulary",
             "candidate_next_theory": "<short honest hint>"}

    This is a Class-D late-binding op (one rung above :func:`match`): pure
    orchestration over the already-C-mirrored reducers, so it ships **without**
    a dedicated C peer (the from_bodies / cooccurrence_edges ``non_compute``
    precedent). numpy-free; no ``abs()`` (the spectral Λ² verify reads the
    magnitude by Class-K comparison). Cites F929 (the dispatch-table-of-
    reduction-theories frame).
    """
    if not isinstance(relationship, dict):
        raise TypeError(
            f"infer expects a relationship descriptor dict; got "
            f"{type(relationship).__name__}")

    # rc176: dispatch the two clean carrier-FFI rows through the srmech_infer C
    # peer (detect + dispatch + verify in C); fall to the pure body on any
    # non-marshallable row / C non-OK (inform-don't-limit; never a false result).
    nat = _native_infer()
    if nat is not None:
        try:
            marshalled = _marshal_relationship(relationship)
        except (ValueError, TypeError, IndexError, KeyError, ZeroDivisionError,
                OverflowError, RuntimeError):
            marshalled = None
        if marshalled is not None:
            rel_json, max_terms = marshalled
            try:
                decision = nat.infer_c(rel_json, max_terms)
            except (RuntimeError, OverflowError, ValueError):
                decision = None
            if decision is not None:
                return _finish_native(relationship, decision)

    row = _detect_row(relationship)
    if row is None:
        return _open(None, "not reducible in current vocabulary")

    # Dispatch + VERIFY. Each ``_try_*`` runs the matching reducer and returns a
    # reduced dict ONLY when the reducer's OWN verification passed; a None falls
    # through to the honest OPEN (with the row-appropriate candidate hint). Any
    # reducer-internal contract error (a malformed payload) is caught and routed
    # to OPEN too — never a spurious ``reducible: True``.
    _TRY = {"sigma": _try_sigma, "sigma_multivar": _try_sigma_multivar,
            "sigma_q": _try_sigma_q, "sigma_elliptic": _try_sigma_elliptic,
            "sigma_elliptic_multivar": _try_sigma_elliptic_multivar,
            "spectral": _try_spectral, "cyclic": _try_cyclic}
    try:
        result = _TRY[row](relationship)
    except (ValueError, TypeError, IndexError, KeyError, ZeroDivisionError,
            OverflowError, RuntimeError):
        result = None
    if result is not None:
        return result
    return _open(row, "not reducible in current vocabulary")
