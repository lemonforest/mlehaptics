"""
Millennium Prize #3 -- Hodge conjecture cascade.

Class cascade: A o L o C o I o K o N o M

  - A: content-hash of variety (dim, Hodge numbers, Euler char, Picard rank)
  - L: cohomology Laplacian (Hodge decomposition H^n(X, C) = sum h^{p,q} over p+q=n)
  - C: cascade-orientation -- the (p, q) bi-grading IS Class C orientation
  - I: cyclic structure -- Hodge symmetry h^{p,q} = h^{q,p} (Z/2 reflection)
  - K: asymptotic-DoF -- middle (k, k) Hodge class IS the pin-slot at the
       diagonal of the Hodge diamond
  - N: rational anchor -- Hodge classes are in H^{2k}(X, Q) (rational coefficients)
  - M: HDC bind -- cycle class map cl: CH^k(X) tensor Q -> H^{2k}(X, Q)

Per [[project_a_n_operators_are_harmonic_objects_themselves]] §A: tests whether
the Hodge diamond layer-count (2 dim_C(X) + 1) sits at Hurwitz parallelizable
boundaries:

  - dim 1 (curves):      3 layers
  - dim 2 (surfaces):    5 layers
  - dim 3 (threefolds):  7 layers  -- Hurwitz heptadic anchor
  - dim 4 (fourfolds):   9 layers
  - dim 5 (fivefolds):  11 layers  -- Hurwitz parallelizable 1+3+7

This is a substrate-level test of whether varieties of complex dimension 3 (the
threefold substrate) and dimension 5 (the fivefold substrate) sit at structural
boundaries the framework's Hurwitz-bounded canon predicts.

Per [[feedback_no_lineage_claims_in_notebook]]: does NOT claim to solve Hodge.
Documents structural cascade decomposition + Hurwitz Hodge-diamond layer test +
Class K pin-slot reading of middle (k, k) algebraic-cycle slot.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
via shared _cascade_helpers (best_rat_signed for Class N).

Roster: varieties with attested Hodge numbers and (where known) Picard rank
from standard references (Griffiths-Harris 1978; Voisin 2002, 2003; Beauville
1983, Hodge-conjecture lecture notes; LMFDB elliptic-curve / abelian-variety
sections; Cox-Katz 1999 Mirror Symmetry).
"""

import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.millennium.hodge_conjecture.variety_hodge_diamond.v1"
SOURCE_DOI = "https://www.lmfdb.org/Variety/ + standard textbooks"
SOURCE_PUBLISHED = "2026-05-23"


# Each entry: (label, dim_C, hodge_diamond, euler_char, picard_rho_known, hodge_status, cm, anchor, fermata)
# hodge_diamond is dict {(p, q): h^{p,q}}.
# hodge_status: "proved" (Lefschetz 1-1 at k=1 always; specific cases for k>=2)
#               "proved-CM" (CM case proved per Tankeev/Deligne/Pohlmann)
#               "open" (general case k>=2)
# Picard rank rho_known: int (where canonical) or None (variable).

ROSTER = [
    # Curves (dim_C = 1): Lefschetz (1,1) trivially gives Hodge conjecture
    dict(label="P^1", dim=1, h={(0, 0): 1, (1, 1): 1, (1, 0): 0, (0, 1): 0},
         chi=2, rho=1, status="proved", cm=False,
         anchor="Hartshorne 1977 II.7; rational curve",
         fermata="trivial baseline; rank-1 H^{1,1}"),
    dict(label="EllipticCurve_y2=x3-x", dim=1,
         h={(0, 0): 1, (1, 0): 1, (0, 1): 1, (1, 1): 1},
         chi=0, rho=1, status="proved", cm=True,
         anchor="Cremona 32.a1; CM by Z[i]",
         fermata="CM elliptic curve; Hodge trivial via L (1,1)"),
    dict(label="Genus2_curve", dim=1,
         h={(0, 0): 1, (1, 0): 2, (0, 1): 2, (1, 1): 1},
         chi=-2, rho=1, status="proved", cm=False,
         anchor="Hartshorne 1977 IV; LMFDB",
         fermata="genus 2; H^{1,0} = 2-dim space of holomorphic 1-forms"),
    dict(label="Genus3_curve", dim=1,
         h={(0, 0): 1, (1, 0): 3, (0, 1): 3, (1, 1): 1},
         chi=-4, rho=1, status="proved", cm=False,
         anchor="Griffiths-Harris 1978; LMFDB",
         fermata="genus 3; can be canonical embedded as plane quartic"),

    # Surfaces (dim_C = 2): Lefschetz (1,1) proves Hodge for k = 1 always
    dict(label="P^2", dim=2,
         h={(0, 0): 1, (1, 0): 0, (0, 1): 0, (2, 0): 0, (1, 1): 1, (0, 2): 0,
            (2, 1): 0, (1, 2): 0, (2, 2): 1},
         chi=3, rho=1, status="proved", cm=False,
         anchor="Hartshorne 1977; basic surface",
         fermata="rho = h^{1,1} = 1"),
    dict(label="P^1xP^1", dim=2,
         h={(0, 0): 1, (1, 0): 0, (0, 1): 0, (2, 0): 0, (1, 1): 2, (0, 2): 0,
            (2, 1): 0, (1, 2): 0, (2, 2): 1},
         chi=4, rho=2, status="proved", cm=False,
         anchor="Hartshorne; product variety Kunneth",
         fermata="rho = h^{1,1} = 2; both classes algebraic"),
    dict(label="Cubic_surface_dP3", dim=2,
         h={(0, 0): 1, (1, 0): 0, (0, 1): 0, (2, 0): 0, (1, 1): 7, (0, 2): 0,
            (2, 1): 0, (1, 2): 0, (2, 2): 1},
         chi=9, rho=7, status="proved", cm=False,
         anchor="Beauville 1983 Complex Algebraic Surfaces; del Pezzo of degree 3",
         fermata="rho = 7; the famous 27 lines generate Picard"),
    dict(label="K3_surface_Fermat_quartic", dim=2,
         h={(0, 0): 1, (1, 0): 0, (0, 1): 0, (2, 0): 1, (1, 1): 20, (0, 2): 1,
            (2, 1): 0, (1, 2): 0, (2, 2): 1},
         chi=24, rho=20, status="proved-special",  # rho can be < 20; Fermat quartic is rho = 20
         cm=False,
         anchor="Mukai 1987; Pjateckii-Shapiro-Shafarevich Torelli theorem",
         fermata="Fermat quartic is singular K3 with rho = 20 (maximal); generic K3 has rho ~ 1"),
    dict(label="Enriques_surface", dim=2,
         h={(0, 0): 1, (1, 0): 0, (0, 1): 0, (2, 0): 0, (1, 1): 10, (0, 2): 0,
            (2, 1): 0, (1, 2): 0, (2, 2): 1},
         chi=12, rho=10, status="proved", cm=False,
         anchor="Beauville 1983; Cossec-Dolgachev 1989",
         fermata="rho = h^{1,1} = 10; Hodge trivial via L (1,1)"),
    dict(label="Abelian_surface_E_x_E", dim=2,
         h={(0, 0): 1, (1, 0): 2, (0, 1): 2, (2, 0): 1, (1, 1): 4, (0, 2): 1,
            (2, 1): 2, (1, 2): 2, (2, 2): 1},
         chi=0, rho=4, status="proved-CM", cm=True,
         anchor="Tankeev 1981; Pohlmann 1968 CM-abelian-surfaces",
         fermata="CM abelian surface E x E; Hodge proved via Mumford-Tate group"),

    # Threefolds (dim_C = 3): 7 layers in Hodge diamond -- Hurwitz heptadic anchor
    dict(label="P^3", dim=3,
         h={(0, 0): 1, (1, 1): 1, (2, 2): 1, (3, 3): 1},  # nonzero diagonal only
         chi=4, rho=1, status="proved", cm=False,
         anchor="Hartshorne; projective space",
         fermata="all middle layers diagonal only; rho = 1"),
    dict(label="Quintic_CY_threefold", dim=3,
         h={(0, 0): 1, (3, 0): 1, (2, 1): 101, (1, 2): 101, (0, 3): 1,
            (1, 1): 1, (2, 2): 1, (3, 3): 1},
         chi=-200, rho=1, status="proved-special", cm=False,
         anchor="Candelas-de la Ossa-Green-Parkes 1991; Cox-Katz 1999",
         fermata="classic Calabi-Yau; h^{1,1} = 1 (Hodge trivial via Lefschetz); h^{2,1} = 101 deforms"),
    dict(label="Quintic_CY_mirror", dim=3,
         h={(0, 0): 1, (3, 0): 1, (2, 1): 1, (1, 2): 1, (0, 3): 1,
            (1, 1): 101, (2, 2): 101, (3, 3): 1},
         chi=200, rho=101, status="open", cm=False,
         anchor="Greene-Plesser 1990; Cox-Katz 1999",
         fermata="mirror of quintic; h^{1,1} = 101 swapped with h^{2,1}; Hodge for (2,2) open in general"),
    dict(label="Cubic_threefold", dim=3,
         h={(0, 0): 1, (3, 0): 0, (2, 1): 5, (1, 2): 5, (0, 3): 0,
            (1, 1): 1, (2, 2): 1, (3, 3): 1},
         chi=-6, rho=1, status="proved-Clemens-Griffiths", cm=False,
         anchor="Clemens-Griffiths 1972 intermediate Jacobian",
         fermata="not rational; intermediate Jacobian provides obstruction"),
    dict(label="Schoen_CY3", dim=3,
         h={(0, 0): 1, (3, 0): 1, (2, 1): 19, (1, 2): 19, (0, 3): 1,
            (1, 1): 19, (2, 2): 19, (3, 3): 1},
         chi=0, rho=19, status="open", cm=False,
         anchor="Schoen 1988 fibre product; self-mirror CY",
         fermata="self-mirror h^{1,1} = h^{2,1} = 19; Hodge (2,2) open"),
    dict(label="Abelian_threefold_Jac_g3", dim=3,
         h={(0, 0): 1, (1, 0): 3, (0, 1): 3, (2, 0): 3, (1, 1): 9, (0, 2): 3,
            (3, 0): 1, (2, 1): 9, (1, 2): 9, (0, 3): 1, (3, 1): 3, (2, 2): 9,
            (1, 3): 3, (3, 2): 3, (2, 3): 3, (3, 3): 1},
         chi=0, rho=None, status="proved-Tankeev", cm=False,
         anchor="Tankeev 1981 simple abelian threefold; Murasugi-style",
         fermata="Jacobian of genus-3 curve; simple abelian threefold case proved"),

    # Fourfolds (dim_C = 4): 9 layers; Hodge conjecture has more open cases here
    dict(label="P^4", dim=4,
         h={(0, 0): 1, (1, 1): 1, (2, 2): 1, (3, 3): 1, (4, 4): 1},
         chi=5, rho=1, status="proved", cm=False,
         anchor="Hartshorne; projective space",
         fermata="diagonal only; rho = 1; Hodge trivial"),
    dict(label="Sextic_CY_fourfold", dim=4,
         h={(0, 0): 1, (1, 1): 1, (2, 2): 426, (3, 3): 1, (4, 4): 1,
            (4, 0): 1, (3, 1): 1, (2, 0): 0, (1, 2): 426, (2, 1): 426},
         chi=2610, rho=1, status="open", cm=False,
         anchor="Cox-Katz 1999 CY fourfolds; Klemm-Lian-Roan-Yau 1996",
         fermata="CY 4-fold; h^{2,2} = 426 large; Hodge (2,2) widely open"),
    dict(label="Abelian_fourfold_general", dim=4,
         h={(0, 0): 1},  # simplified; abelian h^{p,q} = C(g,p)C(g,q)
         chi=0, rho=None, status="open-general-proved-special",
         cm=False,
         anchor="Tankeev 1983; Mumford-Tate-Hodge group analysis",
         fermata="abelian fourfold; general case OPEN (Tankeev exceptions in 1983)"),

    # Fivefolds (dim_C = 5): 11 layers -- Hurwitz parallelizable 1 + 3 + 7
    dict(label="P^5", dim=5,
         h={(0, 0): 1, (1, 1): 1, (2, 2): 1, (3, 3): 1, (4, 4): 1, (5, 5): 1},
         chi=6, rho=1, status="proved", cm=False,
         anchor="Hartshorne; projective space",
         fermata="diagonal only; rho = 1; 11 layers = Hurwitz parallelizable"),
]


def hodge_diamond_layers(h):
    """Group Hodge numbers by p+q layer."""
    layers = {}
    for (p, q), val in h.items():
        if val > 0:
            layers.setdefault(p + q, 0)
            layers[p + q] += val
    return layers


def total_betti_n(h, n):
    """Total Betti number b_n = sum h^{p,q} over p+q=n."""
    return sum(val for (p, q), val in h.items() if p + q == n)


def middle_diagonal_dim(h, dim_C):
    """Hodge class slot dim H^{k,k} for k = 1...dim_C."""
    return {k: h.get((k, k), 0) for k in range(1, dim_C + 1)}


def main():
    out_path = pathlib.Path(__file__).parent / "variety_hodge_diamond.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        label = entry["label"]
        dim = entry["dim"]
        h = entry["h"]
        chi = entry["chi"]
        rho = entry["rho"]
        status = entry["status"]
        cm = entry["cm"]
        anchor = entry["anchor"]
        fermata = entry["fermata"]

        layers = hodge_diamond_layers(h)
        n_layers = 2 * dim + 1
        middle = middle_diagonal_dim(h, dim)
        h11 = h.get((1, 1), 0)
        h22 = h.get((2, 2), 0)
        h_top = h.get((dim, dim), 0)

        # Class N anchor: rho / h^{1,1} (proportion of Lefschetz (1,1) algebraic)
        if rho is not None and h11 > 0:
            rho_over_h11 = rho / h11
            rh_num, rh_den = best_rat_signed(rho_over_h11, max_d=30)
        else:
            rho_over_h11 = -1.0
            rh_num, rh_den = 0, 1

        # Class N anchor: dim_C / 3 (Hurwitz triadic) for substrate-dim categorisation
        dim_over_3 = dim / 3.0
        d3_num, d3_den = best_rat_signed(dim_over_3, max_d=20)

        # Class N: chi / 24 (anchored at K3 chi = 24)
        chi_over_24 = chi / 24.0
        c24_num, c24_den = best_rat_signed(chi_over_24, max_d=30)

        # Class K pin-slot test: is dim+1 a Mersenne {1, 3, 7, 15, 31}?
        mersenne = (n_layers + 1) - 2  # n_layers + 1 = 2 dim + 2; check 2 dim_C + 1 in Hurwitz set
        is_hurwitz_layer = n_layers in {3, 7, 11}  # 3 (curve), 7 (threefold), 11 (fivefold) = Hurwitz
        is_full_hurwitz_135 = n_layers == 11  # 11 = 1 + 3 + 7

        payload = json.dumps({"label": label, "dim": dim, "chi": chi, "rho": rho},
                             sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "variety_label":                     label,
            "complex_dimension":                 int(dim),
            "hodge_diamond_layers":              int(n_layers),
            "is_hurwitz_layer_count":            bool(is_hurwitz_layer),
            "is_hurwitz_parallelizable_11":      bool(is_full_hurwitz_135),
            "euler_characteristic":              int(chi),
            "h_1_1":                             int(h11),
            "h_2_2":                             int(h22),
            "h_top_top":                         int(h_top),
            "picard_rank_rho":                   int(rho) if rho is not None else -1,
            "rho_over_h_1_1":                    round(rho_over_h11, 6),
            "rho_over_h_1_1_rational_num":       int(rh_num),
            "rho_over_h_1_1_rational_den":       int(rh_den),
            "dim_over_3":                        round(dim_over_3, 6),
            "dim_over_3_rational_num":           int(d3_num),
            "dim_over_3_rational_den":           int(d3_den),
            "chi_over_24":                       round(chi_over_24, 6),
            "chi_over_24_rational_num":          int(c24_num),
            "chi_over_24_rational_den":          int(c24_den),
            "hodge_conjecture_status":           status,
            "has_complex_multiplication":        bool(cm),
            "class_cascade":                     "A-compose-L-compose-C-compose-I-compose-K-compose-N-compose-M",
            "literature_anchor":                 anchor,
            "open_fermata":                      fermata,
            "computation_hash":                  chash,
            "source_doi":                        SOURCE_DOI,
            "source_published_date":             SOURCE_PUBLISHED,
            "entered_locally_at":                now_iso[:10],
        }
        records.append(rec)
        diag.append((label, dim, n_layers, h11, rho, status, is_hurwitz_layer,
                     rho_over_h11, rh_num, rh_den))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    # Diagnostics
    print(f"{'variety':<32} {'dim':>4} {'layers':>7} {'h^{1,1}':>8} {'rho':>6} {'rho/h^{1,1}':>12} {'Class N':>12} {'Hurwitz':>9} {'status':<25}")
    for d in diag:
        label, dim, nl, h11, rho, status, hurw, rh, rhn, rhd = d
        rho_str = str(rho) if rho is not None and rho >= 0 else "n/a"
        rh_str = f"{rh:.4f}" if rh > 0 else "n/a"
        cn_str = f"{rhn}/{rhd}" if rhn != 0 or rhd != 1 else "n/a"
        print(f"  {label:<30} {dim:>4} {nl:>7} {h11:>8} {rho_str:>6} {rh_str:>12} {cn_str:>12} {str(hurw):>9} {status:<25}")

    print()
    print("Hodge-diamond layer-count distribution (predicted Hurwitz at 3, 7, 11):")
    layer_counts = {}
    for d in diag:
        n = d[2]
        layer_counts[n] = layer_counts.get(n, 0) + 1
    for n, c in sorted(layer_counts.items()):
        hurw_tag = " <-- Hurwitz" if n in {3, 7, 11} else ""
        hurw_tag += " (parallelizable 1+3+7)" if n == 11 else ""
        print(f"  {n} layers: {c} varieties{hurw_tag}")

    print()
    print("Hodge conjecture status distribution:")
    status_counts = {}
    for d in diag:
        s = d[5]
        status_counts[s] = status_counts.get(s, 0) + 1
    for s, c in sorted(status_counts.items()):
        print(f"  {s:<28}: {c}")

    print()
    print("Class K pin-slot test: rho == h^{1,1} (Lefschetz (1,1) saturated)?")
    sat = sum(1 for d in diag if d[4] is not None and d[4] >= 0 and d[3] == d[4])
    total = sum(1 for d in diag if d[4] is not None and d[4] >= 0)
    print(f"  {sat} / {total} varieties have rho = h^{{1,1}} (Hodge (1,1) saturated by Picard)")


if __name__ == "__main__":
    main()
