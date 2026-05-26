"""Round 25.A -- Reading-D 12th scale-ladder anchor: galactic / large-scale-structure
multipoles. Sits BETWEEN the planetary rung (~1e7 m, Round 21.A) and the
cosmological/CMB rung (observable universe, Round 6.A) on the scale-ladder.

Two pieces:

(1) SPINE CONTINUITY -- the galaxy angular power spectrum. The projected galaxy
    overdensity is expanded delta(n) = sum a_lm Y_lm(n) with C_l = <|a_lm|^2>
    (averaged over the 2l+1 m-modes): the SAME S^2 Class-L 2l+1 Born-rule
    Hopf-base measure (Round 4.A) as the CMB (Round 6.A) and planetary
    magnetics (Round 21.A). The galaxy survey's "translation fingerprint."

(2) BIT-EXACT CORE -- the Kaiser linear redshift-space-distortion multipoles.
    P^s(k,mu) = (1 + beta mu^2)^2 P_real(k)  (Kaiser MNRAS 227:1 1987; beta=f/b).
    Decomposed in Legendre multipoles P_l = (2l+1)/2 \\int_{-1}^{1} P^s L_l dmu,
    ONLY l = 0, 2, 4 survive (monopole / quadrupole / hexadecapole), with EXACT
    rational coefficients. This script PROVES those coefficients with exact
    Fraction arithmetic (exact Legendre recurrence + exact \\int mu^n dmu), then
    routes them through srmech best_rational.

    - Class-K PARITY selection: odd-l vanish (kernel even in mu, line-of-sight
      reflection mu -> -mu) -- the LSS analogue of the planetary "no l=0
      monopole" (Round 21.A) and the substrate selection rules.
    - degree-4 kernel truncates above l=4 -> exactly THREE surviving multipoles
      = a k=3 triad (monopole/quadrupole/hexadecapole).
    - Class-N anchors: the Kaiser coefficients are small-denominator rationals
      {2/3, 1/5} (P0), {4/3, 4/7} (P2), {8/35} (P4).

Cascade: A o L (S^2 / Legendre 2l+1 multipoles) o K (line-of-sight parity, even-l-only)
         o N (exact rational Kaiser coefficients) o C (RSD anisotropy axis = line of sight).

Facts verified (Explore, attested): Kaiser MNRAS 227:1 (1987); Hamilton review
astro-ph/9708102 (1998); Cole-Fisher-Weinberg MNRAS 267:785 (1994); BAO ~150 Mpc
Eisenstein ApJ 633:560 (2005); n_s = 0.9649 +/- 0.0042 Planck 2018 (A&A 641:A6 2020).

Routed through srmech 0.4.2 (Class-N best_rational). Deterministic; no network.
ASCII-safe prints.
"""

import json
import sys
from datetime import datetime, timezone
from fractions import Fraction as Fr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # docs/unsolved-maths
import _cascade_helpers as ch  # noqa: F401

from srmech.amsc.rational import best_rational  # Class N

OUT = Path(__file__).with_suffix(".ndjson")
RECORDS = []


def emit(kind, **fields):
    RECORDS.append({"record": kind, **fields})


# ---------------------------------------------------------------------------
# exact Legendre polynomials L_l(mu) as lists of Fraction coeffs [c0, c1, ...]
# via the recurrence (n+1) L_{n+1} = (2n+1) mu L_n - n L_{n-1}
# ---------------------------------------------------------------------------
def legendre(lmax):
    polys = [[Fr(1)], [Fr(0), Fr(1)]]            # L0 = 1, L1 = mu
    for n in range(1, lmax):
        Ln, Lnm1 = polys[n], polys[n - 1]
        # (2n+1) mu L_n  -> shift up by one power
        term1 = [Fr(0)] + [(2 * n + 1) * c for c in Ln]
        term2 = [-n * c for c in Lnm1]
        size = max(len(term1), len(term2))
        term1 += [Fr(0)] * (size - len(term1))
        term2 += [Fr(0)] * (size - len(term2))
        nxt = [(term1[i] + term2[i]) / (n + 1) for i in range(size)]
        polys.append(nxt)
    return polys


def integ_mu_pow(n):
    """exact \\int_{-1}^{1} mu^n dmu = 0 (n odd) or 2/(n+1) (n even)."""
    return Fr(0) if n % 2 else Fr(2, n + 1)


# Kaiser kernel (1+beta mu^2)^2 = 1 + 2 beta mu^2 + beta^2 mu^4
# represented as {power_of_beta: {power_of_mu: coeff}}
KERNEL = {0: {0: Fr(1)}, 1: {2: Fr(2)}, 2: {4: Fr(1)}}

LMAX = 6
L = legendre(LMAX)


def multipole_coeffs(l):
    """P_l / P_real as {beta_power: Fraction}, = (2l+1)/2 \\int (kernel) L_l dmu."""
    out = {0: Fr(0), 1: Fr(0), 2: Fr(0)}
    Ll = L[l]
    pref = Fr(2 * l + 1, 2)
    for bpow, muterms in KERNEL.items():
        for mupow, kc in muterms.items():
            # \\int mu^mupow * L_l(mu) dmu  = sum_j Ll[j] * \\int mu^(mupow+j) dmu
            s = Fr(0)
            for j, lc in enumerate(Ll):
                s += lc * integ_mu_pow(mupow + j)
            out[bpow] += pref * kc * s
    return out


# ---------------------------------------------------------------------------
# 1. compute all multipoles l=0..6, prove even-l<=4 truncation + exact coeffs
# ---------------------------------------------------------------------------
EXPECTED = {
    0: {0: Fr(1), 1: Fr(2, 3), 2: Fr(1, 5)},
    1: {0: Fr(0), 1: Fr(0), 2: Fr(0)},
    2: {0: Fr(0), 1: Fr(4, 3), 2: Fr(4, 7)},
    3: {0: Fr(0), 1: Fr(0), 2: Fr(0)},
    4: {0: Fr(0), 1: Fr(0), 2: Fr(8, 35)},
    5: {0: Fr(0), 1: Fr(0), 2: Fr(0)},
    6: {0: Fr(0), 1: Fr(0), 2: Fr(0)},
}

surviving = []
print("Kaiser RSD multipoles P_l / P_real  (coeff of beta^0, beta^1, beta^2):")
for l in range(LMAX + 1):
    c = multipole_coeffs(l)
    assert c == EXPECTED[l], (l, c, EXPECTED[l])
    nonzero = any(v != 0 for v in c.values())
    tag = ""
    if nonzero:
        surviving.append(l)
        tag = "  <- SURVIVES"
    label = {0: "monopole", 2: "quadrupole", 4: "hexadecapole"}.get(l, "")
    print(f"  l={l} {label:12s}: "
          f"b0={c[0]}  b1={c[1]}  b2={c[2]}{tag}")
print("surviving multipoles:", surviving, "(even-l, l<=4) -- a k=3 triad")
assert surviving == [0, 2, 4]
emit("kaiser_multipoles_exact",
     coeffs={l: {f"beta^{p}": str(multipole_coeffs(l)[p]) for p in (0, 1, 2)}
             for l in range(LMAX + 1)},
     surviving=surviving,
     selection_rule=("odd-l vanish (Class-K parity: kernel even in mu, line-of-sight "
                     "reflection mu->-mu); l>4 vanish (degree-4 kernel) -> exactly 3 "
                     "surviving multipoles = k=3 triad monopole/quadrupole/hexadecapole"))

# ---------------------------------------------------------------------------
# 2. Class-N anchors: route each exact coefficient through srmech best_rational
# ---------------------------------------------------------------------------
anchors = {}
for name, fr in [("P0_beta1", Fr(2, 3)), ("P0_beta2", Fr(1, 5)),
                 ("P2_beta1", Fr(4, 3)), ("P2_beta2", Fr(4, 7)),
                 ("P4_beta2", Fr(8, 35))]:
    r = best_rational(fr.numerator, fr.denominator, 100)
    anchors[name] = list(r)
    assert r == (fr.numerator, fr.denominator), (name, r, fr)
print("\nClass-N Kaiser coefficient anchors (srmech best_rational):", anchors)
emit("class_n_kaiser_anchors", anchors=anchors,
     note="every Kaiser RSD multipole coefficient is an EXACT small-denominator rational")

# 2l+1 angular mode counts for the three surviving multipoles
mode_counts = {l: 2 * l + 1 for l in surviving}     # 1, 5, 9
print("2l+1 mode counts for surviving l=0,2,4:", mode_counts)
emit("two_l_plus_1_modes", counts=mode_counts,
     note="same S^2 2l+1 Class-L multiplicity as CMB / planetary / atomic / Born")

# ---------------------------------------------------------------------------
# 3. spine continuity + context anchors
# ---------------------------------------------------------------------------
emit("angular_power_spectrum_spine",
     identity="galaxy C_l = <|a_lm|^2> over 2l+1 m-modes",
     note=("the SAME S^2 Born-rule Hopf-base measure (Round 4.A) as the CMB (Round 6.A) "
           "and planetary magnetics (Round 21.A); the galaxy survey's translation fingerprint"))

# context (not load-bearing): BAO standard ruler + scalar spectral index
ns = Fr(9649, 10000)   # Planck 2018 central
ns_anchor = best_rational(ns.numerator, ns.denominator, 60)
emit("context_anchors",
     bao_sound_horizon_Mpc="~150 (== ~100 h^-1 Mpc); same acoustic physics as CMB peaks (Spike #55)",
     bao_detection="Eisenstein et al. ApJ 633:560 (2005)",
     n_s="0.9649 +/- 0.0042 (Planck 2018); near-1 Class-N anchor (Harrison-Zeldovich n_s=1)",
     n_s_best_rational=list(ns_anchor),
     note="context only; the load-bearing bit-exact content is the Kaiser multipole coefficients")

emit("cascade_form",
     lss="A o L (S^2 / Legendre 2l+1 multipoles) o K (line-of-sight parity, even-l-only) o N (exact rational Kaiser coeffs) o C (RSD axis = line of sight)",
     spine_now="quantum -> nuclear -> atomic -> hadron -> planetary -> LSS/galactic -> cosmological/CMB",
     cross_rung=("the even-l-only selection is the LSS analogue of the planetary no-monopole "
                 "rule (Round 21.A); C_l = <|a_lm|^2> is the Born-rule measure (Round 4.A) one "
                 "scale-band inside the CMB"))

# ---------------------------------------------------------------------------
META = {
    "record": "meta",
    "round": "25.A",
    "title": "Reading-D 12th scale-ladder anchor: galactic / large-scale-structure multipoles",
    "scale": "~10-1000 Mpc (galaxy surveys); between the planetary and cosmological/CMB rungs",
    "srmech_version": __import__("srmech").__version__,
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "attestation": {
        "kaiser_rsd": "Kaiser, MNRAS 227, 1 (1987)",
        "multipole_coeffs": "Hamilton review astro-ph/9708102 (1998); Cole-Fisher-Weinberg MNRAS 267:785 (1994)",
        "bao": "Eisenstein et al., ApJ 633, 560 (2005)",
        "n_s": "Planck 2018 results VI, Aghanim et al., A&A 641, A6 (2020)",
        "angular_Cl": "standard (Peebles, Large-Scale Structure of the Universe 1980)",
    },
    "discipline": "framework reading only; Kaiser coefficients proven by exact Fraction arithmetic; deterministic",
}
RECORDS.append(META)

with OUT.open("w", encoding="utf-8") as fh:
    for rec in RECORDS:
        fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

print("\nwrote", len(RECORDS), "records to", OUT.name)
print("VERDICT: 12th rung holds -- LSS angular C_l = Born-rule 2l+1 spine; Kaiser RSD "
      "multipoles even-l<=4 (Class-K parity) with EXACT rational coeffs (Class-N); k=3 triad.")
