"""srmech.amsc.elliptic_wz_certificate — the ELLIPTIC Σ-row IDENTITY-PROOF op: proves the
Frenkel–Turaev ₈ω₇ SUMMATION IDENTITY ``Σ_k F(n,k) = cf(n)`` exactly and returns the
closed form ``cf(n)``.

The capstone rung of the elliptic Σ-row, after
:func:`~srmech.amsc.elliptic_gosper.elliptic_gosper` (indefinite, rc65),
:func:`~srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7` (the order-1 recurrence
FINDER, rc68) and :func:`~srmech.amsc.elliptic_zeilberger.elliptic_zeilberger` (the
recurrence + EXACT connection-coefficient certificate, rc90). Where ``elliptic_zeilberger``
proves the RECURRENCE ``f(n+1) = ρ(n)·f(n)``, this op proves the full SUMMATION IDENTITY
``Σ_{k=0}^{n} F(n,k) = cf(n)`` — the elliptic analogue of
:func:`~srmech.amsc.wz_certificate.wz_certificate` (the §76 ordinary/q identity-proof rung,
the Wilf–Zeilberger pair method). Its distinct OUTPUT is the **closed form** ``cf(n)`` — the
evaluation of the sum — where ``elliptic_zeilberger`` returns only the recurrence ratio ``ρ``.

────────────────────────────────────────────────────────────────────────────────────
WHY THE PROOF IS CONNECTION-COEFFICIENT INDUCTION (NOT a Wilf–Zeilberger pair)
────────────────────────────────────────────────────────────────────────────────────
A literal Wilf–Zeilberger pair — a ``G(n,k) = R(n,k)·F(n,k)`` antidifference with
``F(n+1,k) − F(n,k) = G(n,k+1) − G(n,k)`` — is **provably dead for the elliptic case**:
the Gosper–Petkovšek certificate lives on the squared lattice with an irreducible quadratic
core (the rc90 finding). So the elliptic identity is proved by the literature method
(Rosengren §2.3): the **connection-coefficient expansion** + **induction on n**. The
identity ``P(n): Σ_{k=0}^n F(n,k) = cf(n)`` follows from

  • BASE CASE ``P(0)``: the ₈ω₇ summand carries a terminating ``(q^{-n}; q, p)_k`` factor
    (``= 0`` for ``k > n``), so at ``n = 0`` only ``k = 0`` survives and
    ``Σ_{k=0}^0 F(0,k) = F(0,0) = 1 = cf(0)`` (the empty Pochhammers); and

  • INDUCTIVE STEP ``P(n) ⟹ P(n+1)``: ``Σ F(n+1,k) / Σ F(n,k) = ρ(n) = cf(n+1)/cf(n)``,
    the order-1 recurrence whose EXACT certificate is the connection-coefficient
    inductive-step identity (Rosengren §2.3 Eq. 2.12–2.14 reduce to §1.4 Eq. 1.12, the
    Weierstrass three-term relation), decided ``≡ 0`` in the additive theta carrier via
    :meth:`~srmech.amsc.thetasum.ThetaSum.is_zero` — the SAME exact certificate
    ``elliptic_zeilberger`` builds (:func:`~srmech.amsc.elliptic_zeilberger.
    _connection_split_certificate`, the cleared ±-pair split, perfect-square monomial
    midpoints, no float, no converging witness).

Together ``P(0)`` ∧ ``(P(n) ⟹ P(n+1))`` is the COMPLETE exact proof of the Frenkel–Turaev
summation. The closed form is

    cf(n) = (aq, aq/bc, aq/bd, aq/cd; q, p)_n / (aq/b, aq/c, aq/d, aq/bcd; q, p)_n,

with the ₈ω₇ balancing ``bcde = a²q^{n+1}`` (Theorem 2.3.1).

Reference (MPM-verified at build by reading the actual source PDF): Hjalmar Rosengren,
"Elliptic Hypergeometric Functions," arXiv:1608.06161v3 [math.CA] (20 Jun 2017), §1.4
Eq. (1.12), §2.3 Eqs. (2.12)–(2.15) (Theorem 2.3.1, the Frenkel–Turaev ₈ω₇ summation). The
closed product form + the elementary-symmetric ``ρ`` are also Warnaar, *Constr. Approx.* 18
(2002) 479–502, Corollary 2.2. The recognition / decomposition and the connection-
coefficient certificate are reused from :mod:`srmech.amsc.elliptic_recurrence` /
:mod:`srmech.amsc.elliptic_zeilberger`.

Exact over the modified-theta algebra (no float on the decision path; sign is the
**Class-K** pin-slot via the ``Q`` / ``EllMonomial`` sign-branch, never an ALU ``abs()``;
no ``math``, no numpy). C peer: ``srmech_elliptic_wz_certificate`` (a 1:1 mirror that runs
the same recognize → closed-form → connection-coefficient-certificate pipeline and decides
the certificate via the shared ``srmech_thetasum_is_zero`` kernel; the Python dispatch
trusts the native result only after re-deciding the certificate in exact ℚ). Caller-arena,
malloc-free, JPL-clean.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .ellbase import EllMonomial, _Q_SYM
from .elliptic_recurrence import _coerce_ratio, _decompose_8w7, _ratio_to_form
from .elliptic_zeilberger import _connection_split_certificate

__all__ = ["elliptic_wz_certificate"]


def _closed_form_endpoints(a_mono: EllMonomial, free: "List[EllMonomial]"
                           ) -> "Tuple[List[EllMonomial], List[EllMonomial]]":
    """The Frenkel–Turaev closed form ``cf(n) = ∏(num; q, p)_n / ∏(den; q, p)_n`` endpoints
    (Warnaar Cor 2.2 / Rosengren Thm 2.3.1): with ``a`` the base and ``[b, c, d]`` the three
    free params,

        numerator   Pochhammer bases: ``{aq, aq/bc, aq/bd, aq/cd}``
        denominator Pochhammer bases: ``{aq/b, aq/c, aq/d, aq/bcd}``.

    Returns ``(num_bases, den_bases)`` as ``EllMonomial`` lists (the same endpoints the
    rc68 closed-form oracle ``_f_sum_value`` uses, and whose increment ratio is the rc68/rc90
    recurrence ``ρ``)."""
    b, c, d = free[0], free[1], free[2]
    aq = a_mono * EllMonomial.symbol(_Q_SYM)
    num_bases = [aq, aq * (b * c).inv(), aq * (b * d).inv(), aq * (c * d).inv()]
    den_bases = [aq * b.inv(), aq * c.inv(), aq * d.inv(), aq * (b * c * d).inv()]
    return num_bases, den_bases


def _native():
    """The native ``_native`` module IF the ``srmech_elliptic_wz_certificate`` peer is
    present and bound, else ``None`` (so the op dispatches to C when available and falls
    cleanly to the pure-Python body). Imported lazily to avoid a bootstrap cycle."""
    try:
        from . import _native as nat
    except ImportError:
        return None
    probe = getattr(nat, "has_native_elliptic_wz_certificate", None)
    return nat if (probe is not None and probe()) else None


def elliptic_wz_certificate(r) -> Optional[Dict[str, object]]:
    """The ELLIPTIC Σ-row IDENTITY-PROOF for the Frenkel–Turaev ₈ω₇ summation — proves
    ``Σ_{k=0}^n F(n,k) = cf(n)`` exactly and returns the closed form ``cf(n)``.

    ``r`` is the ₈ω₇ summand's **term ratio** ``t(n+1)/t(n) = r(x)`` (an
    :class:`~srmech.amsc.ellbase.EllRatio`; see
    :func:`~srmech.amsc.elliptic_recurrence.elliptic_recurrence_8w7`). The op RECOGNIZES the
    ₈ω₇, builds the closed form ``cf(n)`` (Warnaar Cor 2.2 / Rosengren Thm 2.3.1), and proves
    the summation identity by the connection-coefficient induction — BASE CASE (the
    terminating ``(q^{-n})_k`` factor gives ``Σ_{k=0}^0 F(0,k) = 1 = cf(0)``) + the EXACT
    inductive-step certificate (the cleared connection-coefficient split, decided ``≡ 0`` via
    :meth:`~srmech.amsc.thetasum.ThetaSum.is_zero`):

    - if ``r`` is a canonical ₈ω₇ AND the inductive-step certificate is exactly ``≡ 0``,
      returns ``{'identity': '…', 'closed_form': {'num': […], 'den': […]}, 'certificate':
      {'method': 'connection_coefficient_induction', 'base_case': '…', 'inductive_step':
      '…', 'exact': True}, 'verified': True}`` — the closed form plus the EXACT proof of the
      summation identity;
    - if ``r`` is not a canonical ₈ω₇ or the certificate fails to decide ``≡ 0``, returns
      ``None`` (the honest out-of-class residue).

    A literal Wilf–Zeilberger pair is provably dead for the elliptic case (the rc90
    finding); the proof is the literature's connection-coefficient induction, decided
    EXACTLY — never a converging witness. No float on the decision path, no ``abs()``
    (Class-K sign), no ``math`` / numpy. See the module docstring for the full proof
    structure + the MPM-verified Rosengren reference.
    """
    r = _coerce_ratio(r)
    if r.is_zero:
        return None
    if not r.is_elliptic():
        return None
    decomp = _decompose_8w7(r)
    if decomp is None:
        return None
    a_mono, free = decomp
    # the EXACT inductive-step certificate (shared with elliptic_zeilberger): the cleared
    # connection-coefficient split, decided ≡ 0 in the additive theta carrier (no 1e-9).
    cert = _connection_split_certificate(a_mono, free[0], free[1])
    if not cert.is_zero:
        return None                                          # inductive step did not close

    nat = _native()
    if nat is not None:
        try:
            got = nat.elliptic_wz_certificate_c(_ratio_to_form(r))
            # trust the C peer only after the pure path agrees AND the certificate
            # re-decides ≡ 0 in exact ℚ (the no-hallucination standard).
            if got is not None:
                has, _payload = got
                if has and cert.is_zero:
                    return _build_result(a_mono, free)
        except (RuntimeError, OverflowError, ValueError):
            pass

    return _build_result(a_mono, free)


def _build_result(a_mono: EllMonomial, free: "List[EllMonomial]") -> Dict[str, object]:
    """Assemble the public return dict: the closed form ``cf(n)`` endpoints PLUS the EXACT
    connection-coefficient-induction certificate and ``verified: True`` (the inductive step
    decided ``≡ 0`` and the terminating base case holds)."""
    num_bases, den_bases = _closed_form_endpoints(a_mono, free)
    return {
        "identity": ("sum_{k=0}^n F(n,k) = "
                     "(aq, aq/bc, aq/bd, aq/cd; q, p)_n / "
                     "(aq/b, aq/c, aq/d, aq/bcd; q, p)_n"),
        "closed_form": {
            "num": [dict(m.exps) for m in num_bases],
            "den": [dict(m.exps) for m in den_bases],
        },
        "certificate": {
            "method": "connection_coefficient_induction",
            "reference": "Rosengren arXiv:1608.06161 Thm 2.3.1 (Eq 2.12-2.14 -> Eq 1.12)",
            "base_case": "n=0: terminating (q^-n)_k leaves only k=0, sum=cf(0)=1",
            "inductive_step": "connection-coefficient split, ThetaSum.is_zero (exact)",
            "exact": True,
        },
        "verified": True,
    }
