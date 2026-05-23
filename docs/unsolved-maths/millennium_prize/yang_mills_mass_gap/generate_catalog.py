"""
Millennium Prize #6 -- Yang-Mills Existence and Mass Gap cascade.

Class cascade: A o M o I o C o K o L (Spike #58 chain)

  - A: content-hash of (gauge group spec, dimension, mass-gap value, ratio)
  - M: HDC bundle of gauge-field-configuration substrate (per Spike #58.G SM gauge group)
  - I: cyclic structure of center Z(SU(N)) = Z/N
  - C: cascade-orientation -- chirality / parity / charge-conjugation
  - K: asymptotic-DoF -- mass gap IS pin-slot at zero of the mass spectrum
  - L: Yang-Mills Laplacian -- covariant derivative squared

Per [[project_a_n_operators_are_harmonic_objects_themselves]]: tests whether
m(0++)/sqrt(sigma) and N/7 sit at small-denominator rational anchors. The
Hurwitz heptadic prediction per partition 5 of PR #677 (Hilbert 16 found n/7
EXACT for polynomial vector fields) applied here to SU(N) gauge groups.

Closes the Hilbert 6 PARTIAL coverage on Yang-Mills (Wightman QFT axioms row
of partition 6: 'A o M o L o I o C; constructive QFT in 4D open').

Per [[feedback_no_lineage_claims_in_notebook]]: does NOT claim to solve the
Yang-Mills mass gap problem. Documents structural cascade decomposition +
cross-substrate Hurwitz anchors.

Per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]: cascade-honesty
via shared _cascade_helpers (best_rat_signed for Class N).

Per [[feedback_pdf_extraction_citation_discipline]] + arxiv-only-citation:
mass-gap values are extrapolations from published lattice-QCD literature
(Lucini-Teper 2001, 2004; Morningstar-Peardon 1999; Chen et al. 2006; Teper
1998). All anchor arxiv IDs in descriptor.toml.
"""

import datetime
import json
import pathlib
import sys

# Cascade-honesty per [[feedback_sign_handling_is_class_k_pin_slot_not_alu_abs]]:
# shared A-N cascade helpers (precursor of srmech.amsc.cascade.* primitives).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from _cascade_helpers import magnitude, cyclic_gcd, best_rat_signed

from srmech.amsc.format import sha256_bytes

SCHEMA_ID = "srmech.millennium.yang_mills.gauge_group_mass_gap.v1"
SOURCE_DOI = "10.48550/arXiv.hep-lat/0103027"     # Lucini-Teper 2001
SOURCE_PUBLISHED = "2001-01-01"


# Gauge group roster.
# Each row: (gauge_group, N, spacetime_dim, lightest_glueball_J_PC,
#            mass_gap_over_sqrt_sigma, ratio_2pp_to_0pp, anchor, fermata).
#
# Mass-gap values are dimensionless m(0++) / sqrt(sigma) from Teper / Lucini-Teper
# extrapolations:
#   SU(2):  3.78 (Teper 1998, Lucini-Teper 2001)
#   SU(3):  3.55 (Morningstar-Peardon 1999, Chen 2006, Lucini-Teper 2001)
#   SU(4):  3.36 (Lucini-Teper 2001)
#   SU(5):  3.36 (Lucini-Teper 2001)
#   SU(6):  3.31 (Lucini-Teper-Wenger 2004)
#   N=inf:  3.31 (large-N limit, Lucini-Teper extrapolation)
#
# Ratio m(2++)/m(0++) is approximately 1.40 across SU(N) (Lucini-Teper-Wenger 2004).

ROSTER = [
    dict(label="U(1)", N=1, dim=4, jpc="N/A", m=0.0, r2p0p=0.0,
         anchor="Spike #58.I: U(1)_Y = 1D_t x 1D_circle Class I x Class C",
         fermata="abelian; no confinement, no mass gap from gauge dynamics alone"),
    dict(label="SU(2)", N=2, dim=4, jpc="0++", m=3.78, r2p0p=1.44,
         anchor="Spike #58.H: SU(2)_L from H subalg of O (quaternion subalgebra)",
         fermata=""),
    dict(label="SU(3)", N=3, dim=4, jpc="0++", m=3.55, r2p0p=1.39,
         anchor="Spike #58.G + #58.O Dirac index: SM SU(3) color sector",
         fermata=""),
    dict(label="SU(4)", N=4, dim=4, jpc="0++", m=3.36, r2p0p=1.40,
         anchor="Spike #58 chain extension; Lucini-Teper 2001 lattice",
         fermata=""),
    dict(label="SU(5)", N=5, dim=4, jpc="0++", m=3.36, r2p0p=1.40,
         anchor="Lucini-Teper 2001 lattice; large-N extrapolation",
         fermata="GUT-relevant; SU(5) Georgi-Glashow union"),
    dict(label="SU(6)", N=6, dim=4, jpc="0++", m=3.31, r2p0p=1.40,
         anchor="Lucini-Teper-Wenger 2004 lattice",
         fermata=""),
    dict(label="SU(7)", N=7, dim=4, jpc="0++", m=3.30, r2p0p=1.40,
         anchor="Lucini-Teper large-N extrapolation",
         fermata="Hurwitz-heptadic-anchor test gauge group"),
    dict(label="SU(8)", N=8, dim=4, jpc="0++", m=3.30, r2p0p=1.40,
         anchor="Lucini-Teper large-N extrapolation",
         fermata=""),
    dict(label="SU(inf)", N=999, dim=4, jpc="0++", m=3.31, r2p0p=1.40,
         anchor="Lucini-Teper large-N limit; 't Hooft 1974",
         fermata="N -> infinity 't Hooft limit; cascade-asymptote"),
    # 2+1D toy for comparison
    dict(label="SU(2)_2plus1D", N=2, dim=3, jpc="0++", m=4.72, r2p0p=1.59,
         anchor="Teper 1998 SU(N) 2+1D lattice",
         fermata="2+1D toy; not the Millennium target dimensionality"),
    dict(label="SU(3)_2plus1D", N=3, dim=3, jpc="0++", m=4.32, r2p0p=1.55,
         anchor="Teper 1998 SU(N) 2+1D",
         fermata=""),
]


def casimir_2_fundamental(N):
    """Quadratic Casimir of the fundamental representation of SU(N): C_2(F) = (N^2 - 1) / (2N)."""
    if N <= 0:
        return 0.0
    return (N * N - 1) / (2.0 * N)


def main():
    out_path = pathlib.Path(__file__).parent / "gauge_group_mass_gap.ndjson"
    now_iso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    records = []
    diag = []

    for entry in ROSTER:
        label = entry["label"]
        N = entry["N"]
        dim = entry["dim"]
        m = entry["m"]
        r2p0p = entry["r2p0p"]
        jpc = entry["jpc"]
        anchor = entry["anchor"]
        fermata = entry["fermata"]

        casimir = casimir_2_fundamental(N)

        # Class N best-rational of m(0++) / sqrt(sigma)
        m_num, m_den = best_rat_signed(m, max_d=20)

        # Class N best-rational of N / 7 (Hurwitz heptadic anchor)
        n_over_7 = N / 7.0
        n7_num, n7_den = best_rat_signed(n_over_7, max_d=20)

        # Class N best-rational of m(2++) / m(0++)
        r_num, r_den = best_rat_signed(r2p0p, max_d=20)

        payload = json.dumps({"label": label, "N": N, "dim": dim, "m": m}, sort_keys=True).encode()
        chash = sha256_bytes(payload)

        rec = {
            "gauge_group":                       label,
            "rank_N":                            N,
            "rank_N_minus_1":                    max(0, N - 1),
            "dim_generators_N2_minus_1":         max(0, N * N - 1),
            "spacetime_dim":                     dim,
            "casimir_2_fundamental":             round(casimir, 6),
            "lightest_glueball_J_PC":            jpc,
            "mass_gap_over_sqrt_string_tension": round(m, 6),
            "mass_gap_rational_num":             int(m_num),
            "mass_gap_rational_den":             int(m_den),
            "N_over_7":                          round(n_over_7, 6),
            "N_over_7_rational_num":             int(n7_num),
            "N_over_7_rational_den":             int(n7_den),
            "ratio_2pp_to_0pp":                  round(r2p0p, 6),
            "ratio_2pp_to_0pp_rational_num":     int(r_num),
            "ratio_2pp_to_0pp_rational_den":     int(r_den),
            "class_cascade":                     "A-compose-M-compose-I-compose-C-compose-K-compose-L",
            "spike_58_chain_anchor":             anchor,
            "open_fermata":                      fermata,
            "computation_hash":                  chash,
            "source_doi":                        SOURCE_DOI,
            "source_published_date":             SOURCE_PUBLISHED,
            "entered_locally_at":                now_iso[:10],
        }
        records.append(rec)
        diag.append((label, N, dim, m, m_num, m_den, n_over_7, n7_num, n7_den, r2p0p, r_num, r_den))

    with open(out_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Wrote {len(records)} records to {out_path}")
    print()

    print(f"{'gauge':<18} {'N':>4} {'dim':>4} {'m/sqrt(sigma)':>14} {'Class-N anchor':>14} {'N/7':>10} {'N/7 best-rat':>12} {'m(2++)/m(0++)':>14} {'ratio anchor':>12}")
    for d in diag:
        label, N, dim, m, mn, md, n7, n7n, n7d, r, rn, rd = d
        print(f"  {label:<16} {N:>4} {dim:>4} {m:>14.4f} {mn:>6}/{md:<6} {n7:>10.4f} {n7n:>4}/{n7d:<6} {r:>14.4f} {rn:>4}/{rd:<6}")

    print()
    print("Hurwitz heptadic anchor at SU(7) (specific test per [[project_a_n_operators_are_harmonic_objects_themselves]]):")
    for d in diag:
        label, N, dim, m, mn, md, n7, n7n, n7d, r, rn, rd = d
        if N == 7 and dim == 4:
            print(f"  SU(7) 4D: m/sqrt(sigma) = {m:.4f} = {mn}/{md}; N/7 = {n7:.4f} = {n7n}/{n7d}")

    print()
    print("m(2++)/m(0++) Hurwitz prediction (candidate 3/2 = 1.5):")
    rs = [(d[0], d[9], d[10], d[11]) for d in diag if d[0] not in ("U(1)",)]
    print(f"  {'gauge':<20} {'r':>8} {'best-rat':>10}")
    for label, r, rn, rd in rs:
        print(f"  {label:<18} {r:>8.4f} {rn:>4}/{rd:<6}")

    print()
    print("4D large-N convergence of m(0++)/sqrt(sigma):")
    for d in diag:
        label, N, dim, m, mn, md, n7, n7n, n7d, r, rn, rd = d
        if dim == 4 and label not in ("U(1)",):
            print(f"  N={N:>3} -- {m:>6.3f}  Class N: {mn}/{md}")


if __name__ == "__main__":
    main()
