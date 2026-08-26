r"""R-RBS-LM-1306VERIFY — the committed generating code for F1306's §0 table.

Re-runs all TEN load-bearing DEMONSTRABLE numbers behind F1306 / the klein4-package +
rich-Laplacian + curvature-block plan, against the LIVE package. Every number in the
finding and the plan doc came from THIS script (main-loop re-run), not from the drafting
workflow on trust — the workflow ran partly on a stale rc107 worktree and its own
adversarial-verify pass flagged the one dishonest item ("V4 NOT shipped"), which is FALSE
at rc299 and is asserted-dead here.

Per `[[feedback_computational_provenance_discipline]]`: load-bearing numerical results must
have generating code committed. This is that code. Exit non-zero if ANY number drifts.

srmech 0.9.0rc299. No numpy, no fractions (the import guard forbids both). No abs() in a
cascade sense (magnitude/tuple compares only; the tolerance guards here are test-harness
thresholds, not cascade math — see F1284).
Run:  /tmp/srmech_new/bin/python3 R-RBS-LM-1306VERIFY_*.py
Composes F1301/F1302/F1211/F1255/F1213/F1259/F1300/F1216/F1304/F1305.
"""
import sys

from srmech.amsc import laplacian as L, hdc as H, rational as R, cascade as CAS


def f(v):
    return float(v.as_float()) if hasattr(v, "as_float") else float(v)


def rvals(mat):
    r = L.symmetric_eigendecompose(mat)
    vals = r[0] if isinstance(r, tuple) else r
    return sorted(round(f(v), 4) for v in vals)


def hvals(mat):
    r = L.hermitian_eigendecompose(mat)
    vals = r[0] if isinstance(r, tuple) else r
    return sorted(round(f(v), 4) for v in vals)


def mult_seq(vals, tol=1e-3):
    seq, i = [], 0
    while i < len(vals):
        j = i
        while j < len(vals) and (vals[j] - vals[i]) < tol:  # sorted; no abs (F1284)
            j += 1
        seq.append(j - i)
        i = j
    return seq


# The beat-WSD friendship graph F3: hub 0; arms (0-1-2),(0-3-4),(0-5-6). 9 edges.
BEAT = [(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0), (0, 5), (5, 6), (6, 0)]


def check(label, got, want):
    ok = got == want
    print("  [%s] %s\n        got  %r\n        want %r" % ("OK" if ok else "**DRIFT**", label, got, want))
    return ok


def main():
    import srmech
    print("=== F1306 §0 verification (srmech %s) ===" % srmech.__version__)
    ok = True

    # 1 — flat conflates
    fv = rvals(L.dense_laplacian(7, BEAT))
    ok &= check("1 flat dense_laplacian", (fv, mult_seq(fv)),
                ([-0.0, 1.0, 1.0, 3.0, 3.0, 3.0, 7.0], [1, 2, 3, 1]))

    # 2 — curved separates (per-arm holonomy on the closing edge: 0, 1/3, 2/3)
    ch = [0, 0, 0.0, 0, 0, 1 / 3, 0, 0, 2 / 3]
    mv = hvals(L.magnetic_laplacian(7, BEAT, charges=ch))
    ok &= check("2 curved magnetic (lambda0 lift + 1+2 split)", (mv, mult_seq(mv)),
                ([0.1692, 0.5, 0.5, 1.2315, 1.5, 1.5, 3.5993], [1, 2, 1, 2, 1]))

    # 3 — q=0 control returns to flat pattern
    cv = hvals(L.magnetic_laplacian(7, BEAT, q=0.0))
    ok &= check("3 q=0 control == flat multiplicity", mult_seq(cv), [1, 2, 3, 1])

    # 4 — C 2-perspective ceiling: +/-1/3 isospectral
    T = [(0, 1), (1, 2), (2, 0)]
    p = hvals(L.magnetic_laplacian(3, T, charges=[0, 0, 1 / 3]))
    m = hvals(L.magnetic_laplacian(3, T, charges=[0, 0, -1 / 3]))
    ok &= check("4 +1/3 == -1/3 (isospectral)", (p, p == m), ([0.234, 0.8264, 1.9397], True))

    # 5 — two regimes on one carrier
    D = 1024
    addr = round(f(H.klein4_similarity(H.klein4_address(D, "cat"), H.klein4_address(D, "cats"))), 4)
    rep = round(f(H.klein4_similarity(H.klein4_encode_bytes(b"cat", D), H.klein4_encode_bytes(b"cats", D))), 4)
    ok &= check("5 address(floor) vs encode_bytes(representation)", (addr, rep), (0.248, 0.6748))

    # 6 — Laplacian = projection: octonion associator is a nonzero 3-index object
    def unit(i, dim=8):
        v = [0.0] * dim
        v[i] = 1.0
        return v
    def mul(a, b):
        return [f(x) for x in CAS.cd_mult(a, b)]
    e1, e2, e4 = unit(1), unit(2), unit(4)
    assoc = [round(a - b, 4) for a, b in zip(mul(mul(e1, e2), e4), mul(e1, mul(e2, e4)))]
    ok &= check("6 associator (e1e2)e4-e1(e2e4) = 2*e7", assoc, [0, 0, 0, 0, 0, 0, 0, 2.0])

    # 7 — multi-seam rational is scale-dependent (q=7 joint for pi & e; q=113 splits)
    PI, EE = (3141592653589793, 10 ** 15), (2718281828459045, 10 ** 15)
    r7 = (R.best_rational(*PI, 7), R.best_rational(*EE, 7))
    r113 = (R.best_rational(*PI, 113), R.best_rational(*EE, 113))
    ok &= check("7 best_rational q=7 joint / q=113 splits", (r7, r113),
                (((22, 7), (19, 7)), ((355, 113), (193, 71))))

    # 8 — V4-gain resolves beyond C (frustrated K4, one non-identity gain)
    K4 = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
    gl = L.klein4_gain_laplacian(4, K4, gains=[0, 0, 0, 0, 0, 1])
    sect = {k: rvals(gl[k]) for k in ("chi00", "chi01", "chi10", "chi11")}
    ok &= check("8 V4-gain frustrated K4 sector spectra",
                (sect["chi01"], sect["chi10"]),
                ([0.0, 4.0, 4.0, 4.0], [0.7639, 2.0, 4.0, 5.2361]))  # 3-dp prose form: [0.764,2,4,5.236]

    # 9 — the Class-K sector-asymmetry meter
    rs = L.klein4_relational_structure(edges=K4, gains=[0, 0, 0, 0, 0, 1], n=4)
    ok &= check("9 sector_asymmetry", round(f(rs["sector_asymmetry"]), 4), 0.7639)

    # 10 — the ops that a stale rc107 agent wrongly called unbuilt ARE shipped
    shipped = {n: hasattr(L, n) for n in ("klein4_gain_laplacian", "klein4_relational_structure", "cycle_holonomy")}
    ok &= check("10 V4 + odd-channel ops shipped (stale-rc107 claim is DEAD)", shipped,
                {"klein4_gain_laplacian": True, "klein4_relational_structure": True, "cycle_holonomy": True})

    print("\n=== %s ===" % ("ALL TEN REPRODUCE — F1306 §0 table is honest." if ok
                             else "DRIFT — a number moved; do not trust the finding until reconciled."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
