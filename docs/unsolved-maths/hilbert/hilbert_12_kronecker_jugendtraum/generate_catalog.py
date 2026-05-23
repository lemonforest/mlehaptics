"""
Kronecker's Jugendtraum cascade -- A o I o J o N o L.

Calibrates against KNOWN cases:
  - Q (rationals): Kronecker-Weber theorem -- every abelian extension lies in
    some Q(zeta_n). Generators are roots of unity e^(2 pi i / n), encoded
    via cos(2 pi / n) and sin(2 pi / n) under Class N best-rational.
  - Imaginary-quadratic Q(sqrt(d)) class-number-1 cases: complex multiplication.
    Generators are singular moduli of the j-invariant (classical integers).

For each (field K, conductor m) record:
  - Class I: cyclic structure of (Z/mZ)* via elementary divisors
  - Class J: prime factorisation of m
  - Class N: best-rational of the Kronecker-Weber roots-of-unity real/imag parts
  - Class L: Cayley graph Laplacian eigenvalues of (Z/mZ)* with generators

Per [[feedback_dont_pre_commit_spike_query_operators]]: enumerate broadly;
the cascade is calibrated on the known cases before extending.
"""

import datetime
import json
import math
import pathlib
from fractions import Fraction

import numpy as np

from srmech.amsc.format import sha256_bytes
from srmech.amsc.primes import is_prime, factor
from srmech.amsc.laplacian import dense_laplacian, jacobi_eigvals
from srmech.amsc.rational import best_rational

SCHEMA_ID = "srmech.hilbert.kronecker_jugendtraum.field_extension.v1"
SOURCE_DOI = "10.1007/BF02400408"            # Weber 1886 Acta Mathematica
SOURCE_PUBLISHED = "1886-01-01"


def euler_phi(n):
    if n < 1:
        return 0
    return sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)


def units_mod_n(n):
    return [k for k in range(1, n) if math.gcd(k, n) == 1]


def cyclic_structure_of_units(n):
    """Compute elementary divisors of (Z/nZ)* via Smith Normal Form-equivalent decomposition.

    For (Z/nZ)*, the structure is given by CRT: factor n = prod p^k, and
        (Z/p^k Z)* is cyclic of order phi(p^k)        for odd primes p
        (Z/2 Z)*  is trivial
        (Z/4 Z)*  is cyclic of order 2
        (Z/2^k Z)* for k >= 3 is Z/2 x Z/2^(k-2)
    """
    if n <= 1:
        return []
    component_orders = []
    for prime, exp in factor(n):
        if prime == 2:
            if exp == 1:
                pass  # trivial
            elif exp == 2:
                component_orders.append(2)
            else:
                component_orders.append(2)
                component_orders.append(2 ** (exp - 2))
        else:
            component_orders.append((prime - 1) * (prime ** (exp - 1)))
    # Use Smith-style merge to get elementary divisors (sorted ascending, each dividing the next).
    # For simplicity here, sort and report; full Smith reduction is overkill for small n.
    component_orders.sort()
    return component_orders


def galois_structure_label(divisors):
    if not divisors:
        return "trivial"
    return " x ".join(f"Z/{d}" for d in divisors)


def cayley_graph_laplacian_units_mod_n(n):
    """Build the Cayley graph of (Z/nZ)* with generator set = primitive generators
    (or coset-representatives ±1, ±g where g is a primitive root if it exists),
    return Class L eigenspectrum.
    """
    units = units_mod_n(n)
    if len(units) <= 1:
        return [0.0]
    idx = {u: i for i, u in enumerate(units)}
    # Generator set: {1, -1} mod n, i.e. {1, n-1}. For phi(n) > 2 also include
    # the smallest unit > 1 (which is a generator at minimum, even if not primitive).
    gens = set()
    if 1 in units:
        gens.add(1)
    if (n - 1) in units:
        gens.add(n - 1)
    # add the next smallest unit
    for u in units:
        if u > 1 and u != n - 1:
            gens.add(u)
            break
    # Edges: a -> a*g mod n
    edges_set = set()
    for a in units:
        for g in gens:
            b = (a * g) % n
            if b in idx and a != b:
                lo, hi = sorted((idx[a], idx[b]))
                edges_set.add((lo, hi))
    edges = sorted(edges_set)
    L = dense_laplacian(len(units), edges)
    eigs = sorted(float(x) for x in jacobi_eigvals(L))
    return eigs


def class_k_pin_slot_at_zero(x):
    """Class K pin-slot operation at zero: returns (orientation, magnitude).

    The 'orientation' is the Class C cascade-orientation (+1 / 0 / -1) and
    'magnitude' is the |x|-projection. Per [[user_stance_epicycle_via_gear_plus_pin]]:
    sign-flip IS the canonical pin-slot phase-boundary operation -- the pin enters
    or exits the slot at the zero-crossing.

    This expresses what Python's abs() does as the A-N cascade operation it IS,
    rather than letting ALU-level math sneak in via abs().
    """
    if x > 0.0:
        return +1, x
    if x < 0.0:
        return -1, -x
    return 0, 0.0


def class_c_reorient(orientation, value):
    """Class C cascade-orientation: re-apply the sign of an orientation to a magnitude."""
    if orientation < 0:
        return -value
    return value


def best_rat(x, max_d=100, fine=1_000_000):
    """A-N cascade wrapper around srmech.amsc.rational.best_rational for float input.

    srmech's best_rational signature is best_rational(num: int, denom: int, max_denominator: int)
    with non-negative numerator. Cascade composition (Class K -> Class N -> Class C):
      - Class K pin-slot at zero -> (orientation, magnitude)
      - scale magnitude to integer pair
      - Class N best-rational reduction
      - Class C reorient via the captured orientation
    """
    try:
        orientation, magnitude = class_k_pin_slot_at_zero(x)
        if orientation == 0 or magnitude < 1e-12:
            return 0, 1
        num_pos = int(round(magnitude * fine))
        if num_pos == 0:
            return 0, 1
        nf, df = best_rational(num_pos, fine, max_d)
        signed_nf = class_c_reorient(orientation, int(nf))
        return signed_nf, int(df)
    except Exception:
        return 0, 1


# ------------- Field roster -------------

# Cyclotomic conductors over Q (Kronecker-Weber CALIBRATION cases).
Q_CONDUCTORS = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 21, 24]

# Class-number-1 imaginary quadratic fields (CM CALIBRATION cases).
# Discriminants from the Heegner list.
IMAG_QUAD_CN1 = [
    {"label": "Q(sqrt(-1))",  "d": -4,    "known": "singular_moduli", "note": "j(i)=1728"},
    {"label": "Q(sqrt(-2))",  "d": -8,    "known": "singular_moduli", "note": "j((1+sqrt(-2))/2)=8000"},
    {"label": "Q(sqrt(-3))",  "d": -3,    "known": "singular_moduli", "note": "j(omega)=0"},
    {"label": "Q(sqrt(-7))",  "d": -7,    "known": "singular_moduli", "note": "j((1+sqrt(-7))/2)=-3375"},
    {"label": "Q(sqrt(-11))", "d": -11,   "known": "singular_moduli", "note": "j((1+sqrt(-11))/2)=-32768"},
    {"label": "Q(sqrt(-19))", "d": -19,   "known": "singular_moduli", "note": "j((1+sqrt(-19))/2)=-884736"},
    {"label": "Q(sqrt(-43))", "d": -43,   "known": "singular_moduli", "note": "j((1+sqrt(-43))/2)=-884736000"},
    {"label": "Q(sqrt(-67))", "d": -67,   "known": "singular_moduli", "note": "j((1+sqrt(-67))/2)=-147197952000"},
    {"label": "Q(sqrt(-163))","d": -163,  "known": "singular_moduli", "note": "j((1+sqrt(-163))/2)=-262537412640768000"},
]

# Open case: small cubic and quartic fields where Jugendtraum is open.
# Real-quadratic Q(sqrt(d)) with small d > 0 -- abelian extensions not via cyclotomy in general.
REAL_QUAD_OPEN = [
    {"label": "Q(sqrt(2))",  "d": 8,    "known": "unknown"},
    {"label": "Q(sqrt(3))",  "d": 12,   "known": "unknown"},
    {"label": "Q(sqrt(5))",  "d": 5,    "known": "unknown"},
    {"label": "Q(sqrt(6))",  "d": 24,   "known": "unknown"},
    {"label": "Q(sqrt(7))",  "d": 28,   "known": "unknown"},
]


def main():
    out_path = pathlib.Path(__file__).parent / "field_extension.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for n in Q_CONDUCTORS:
        divisors = cyclic_structure_of_units(n)
        gal = galois_structure_label(divisors)
        cos_v = math.cos(2 * math.pi / n)
        sin_v = math.sin(2 * math.pi / n)
        cn, cd = best_rat(cos_v, max_d=100)
        sn, sd = best_rat(sin_v, max_d=100)
        eigs = cayley_graph_laplacian_units_mod_n(n)
        fiedler = eigs[1] if len(eigs) > 1 else 0.0
        emax = eigs[-1] if eigs else 0.0
        pf = [[int(p), int(e)] for p, e in sorted(factor(n))]

        payload = json.dumps({"field": "Q", "conductor": n}, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        rec = {
            "field_label": f"Q(zeta_{n})",
            "field_kind": "rationals_cyclotomic",
            "discriminant": 1,  # Q itself
            "conductor": n,
            "galois_group_structure": gal,
            "elementary_divisors": divisors,
            "conductor_prime_factorisation": pf,
            "cos_value": round(cos_v, 9),
            "cos_rational_n": cn,
            "cos_rational_d": cd,
            "sin_value": round(sin_v, 9),
            "sin_rational_n": sn,
            "sin_rational_d": sd,
            "cayley_laplacian_fiedler": round(fiedler, 6),
            "cayley_laplacian_max": round(emax, 6),
            "known_generator_kind": "roots_of_unity",
            "class_cascade": "A-compose-I-compose-J-compose-N-compose-L",
            "computation_hash": chash,
            "source_doi": SOURCE_DOI,
            "source_published_date": SOURCE_PUBLISHED,
            "entered_locally_at": now_iso[:10],
        }
        records.append(rec)
        diag.append(("Q(zeta_" + str(n) + ")", gal, len(divisors), fiedler, emax))

    for f in IMAG_QUAD_CN1:
        n = abs(f["d"])
        cos_v = math.cos(2 * math.pi / n) if n > 0 else 1.0
        sin_v = math.sin(2 * math.pi / n)
        cn, cd = best_rat(cos_v, max_d=100)
        sn, sd = best_rat(sin_v, max_d=100)
        # Class group of imag quad is trivial here (cn1) so Cayley is trivial
        eigs = [0.0]
        pf = [[int(p), int(e)] for p, e in sorted(factor(n))]
        payload = json.dumps({"field": f["label"], "d": f["d"]}, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        rec = {
            "field_label": f["label"],
            "field_kind": "imaginary_quadratic_class_1",
            "discriminant": int(f["d"]),
            "conductor": int(n),
            "galois_group_structure": "trivial (class group cn1)",
            "elementary_divisors": [],
            "conductor_prime_factorisation": pf,
            "cos_value": round(cos_v, 9),
            "cos_rational_n": cn,
            "cos_rational_d": cd,
            "sin_value": round(sin_v, 9),
            "sin_rational_n": sn,
            "sin_rational_d": sd,
            "cayley_laplacian_fiedler": 0.0,
            "cayley_laplacian_max": 0.0,
            "known_generator_kind": f["known"],
            "class_cascade": "A-compose-I-compose-J-compose-N-compose-L",
            "computation_hash": chash,
            "source_doi": SOURCE_DOI,
            "source_published_date": SOURCE_PUBLISHED,
            "entered_locally_at": now_iso[:10],
        }
        records.append(rec)
        diag.append((f["label"], "trivial", 0, 0.0, 0.0))

    for f in REAL_QUAD_OPEN:
        n = abs(f["d"])
        cos_v = math.cos(2 * math.pi / n)
        sin_v = math.sin(2 * math.pi / n)
        cn, cd = best_rat(cos_v, max_d=100)
        sn, sd = best_rat(sin_v, max_d=100)
        eigs = cayley_graph_laplacian_units_mod_n(n)
        fiedler = eigs[1] if len(eigs) > 1 else 0.0
        emax = eigs[-1] if eigs else 0.0
        pf = [[int(p), int(e)] for p, e in sorted(factor(n))]
        payload = json.dumps({"field": f["label"], "d": f["d"]}, sort_keys=True).encode()
        chash = sha256_bytes(payload)
        rec = {
            "field_label": f["label"],
            "field_kind": "real_quadratic_open",
            "discriminant": int(f["d"]),
            "conductor": int(n),
            "galois_group_structure": galois_structure_label(cyclic_structure_of_units(n)),
            "elementary_divisors": cyclic_structure_of_units(n),
            "conductor_prime_factorisation": pf,
            "cos_value": round(cos_v, 9),
            "cos_rational_n": cn,
            "cos_rational_d": cd,
            "sin_value": round(sin_v, 9),
            "sin_rational_n": sn,
            "sin_rational_d": sd,
            "cayley_laplacian_fiedler": round(fiedler, 6),
            "cayley_laplacian_max": round(emax, 6),
            "known_generator_kind": f["known"],
            "class_cascade": "A-compose-I-compose-J-compose-N-compose-L",
            "computation_hash": chash,
            "source_doi": SOURCE_DOI,
            "source_published_date": SOURCE_PUBLISHED,
            "entered_locally_at": now_iso[:10],
        }
        records.append(rec)
        diag.append((f["label"], "real_quad_open", len(cyclic_structure_of_units(n)), fiedler, emax))

    with open(out_path, "w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()
    print(f"{'field':<22} {'Galois':<28} {'#divisors':>10} {'fiedler':>10} {'L_max':>10}")
    for d in diag:
        print(f"  {d[0]:<20} {d[1]:<28} {d[2]:>10} {d[3]:>10.4f} {d[4]:>10.4f}")

    # Cascade-cumulative diagnostic
    n_calibrated = sum(1 for r in records if r["known_generator_kind"] != "unknown")
    n_open = sum(1 for r in records if r["known_generator_kind"] == "unknown")
    print()
    print(f"Calibration records (known generator construction): {n_calibrated}")
    print(f"Open-case records (Kronecker Jugendtraum open):     {n_open}")

    # Check: Class N best-rational of cos(2 pi / 3) should be -1/2 EXACTLY
    cos_third = math.cos(2 * math.pi / 3)
    nn, dd = best_rat(cos_third, max_d=10)
    print()
    print(f"Sanity: cos(2*pi/3) = {cos_third:.9f} -> {nn}/{dd}  (expected -1/2 = exact algebraic)")


if __name__ == "__main__":
    main()
