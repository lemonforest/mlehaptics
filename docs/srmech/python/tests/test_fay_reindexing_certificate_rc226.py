"""rc226 — the genus-2 Fay/KP RE-INDEXING CERTIFICATE
(``RiemannTheta.fay_reindexing_certificate``): the rc73 ``addition_holds``
safe-region boolean upgraded to an EXPLICIT, EVERY-ORDER, INSPECTABLE witness.

WHAT IS PROVEN HERE (the anti-shell contract):

* CONSISTENCY — on the same ``(a, b, box)`` the certificate's verdict agrees
  with the EXISTING machinery on the region it DOES resolve: the dense
  ``addition_lhs == addition_rhs`` compare restricted to the safe region
  ``A, B, |C| ≤ 2·box²`` (byte-exact, recomputed here through the untouched
  public dense surfaces) AND the ``addition_holds`` gate itself.
* STRENGTHENING — the certificate resolves a CONCRETE monomial the old gate
  cannot see: the ``beyond_safe_region_witness`` has diagonal exponent
  strictly beyond ``2·box²`` (so the restricted dense compare contains no such
  key), yet its FULL exact coefficient is computed on BOTH sides and agrees
  (nonzero for the pinned pairs). The ``a=(1,0), b=(0,0), box=8`` worked
  example — monomial ``(1090, 0, 0)``, coefficient 8 from the two
  essentially-different representations ``545 = 17²+16² = 23²+4²`` × 4 sign
  combinations — is pinned exactly.
* EVERY-ORDER — ``every_order=True`` for every genuine ``a ≠ b`` pair (and
  the ``a = b`` duplication collapse), with the quadratic-form
  (parallelogram) identity verified EXACTLY in canonical polynomial form
  (``quadratic_form_identity_exact``) — the closed-form proof, not a region
  check: the pure verifier is exercised directly on the free-variable
  polynomial ring (a perturbed identity FAILS, so the verifier genuinely
  decides canonical-form equality).
* HONEST SCOPE — the ``scope`` string names the genus ≥ 5 Schottky OPEN and
  explicitly does NOT claim is-Jacobian / trisecant-decided.
* NATIVE — runs with the native library present (``_native.HAS_NATIVE``); the
  C peer's five outputs are parity-checked against the pure bodies (the
  parity oracle), and the certificate is asserts-live safe (no assert may
  fire in a NO-``NDEBUG`` build — CI runs this file under both).
"""

from __future__ import annotations

import pytest

from srmech.amsc import _native
from srmech.amsc import riemann_theta as rt
from srmech.amsc.riemann_theta import RiemannTheta

# the addition_holds pair roster (the rc73 gate's own list): the duplication
# collapse plus the genuine a != b pairs
PAIRS = [((0, 0), (0, 0)),                       # duplication collapse
         ((1, 0), (0, 0)), ((1, 1), (0, 0)),     # genuine a != b
         ((1, 0), (0, 1)), ((1, 1), (1, 0)),
         ((0, 1), (1, 1))]

GENUINE = [(a, b) for (a, b) in PAIRS if a != b]

BOX = 6                                          # fast CI box (>= 2)


def _cut(lat, safe):
    """The safe-region restriction the addition_holds gate compares on:
    A, B <= safe and |C| <= safe (Class-K magnitude branch, no abs())."""
    out = {}
    for k, v in lat.items():
        mag_c = k[2] if k[2] >= 0 else -k[2]
        if k[0] <= safe and k[1] <= safe and mag_c <= safe:
            out[k] = v
    return out


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="native lib absent — this C symbol-presence / single-call check needs the built libsrmech (#843)")
def test_native_is_present():
    """The rc226 gate runs against the freshly built native library."""
    assert _native.HAS_NATIVE, f"native lib not loaded: {_native.LOAD_ERROR}"


@pytest.mark.skipif(not _native.HAS_NATIVE,
                    reason="native lib absent — this C symbol-presence / single-call check needs the built libsrmech (#843)")
def test_native_fay_symbol_is_bound():
    """The rc226 C peer is loaded and bound (same-rc 1:1 mirror)."""
    assert _native.has_native_riemann_theta_fay()


@pytest.mark.parametrize("a,b", PAIRS)
def test_every_order_certificate(a, b):
    """every_order=True with the exact (closed-form) quadratic-form verdict,
    for every pair — including every genuine a != b pair."""
    cert = RiemannTheta.fay_reindexing_certificate(a, b, box=BOX)
    assert cert["quadratic_form_identity_exact"] is True
    assert cert["bijection_exact"] is True
    assert cert["coeff_preserved"] is True
    assert cert["every_order"] is True
    assert cert["a"] == a and cert["b"] == b
    assert cert["window_bijection_ok"] is True
    assert cert["window_tuples_checked"] == (2 * BOX + 1) ** 4


@pytest.mark.parametrize("a,b", PAIRS)
def test_consistency_with_safe_region_gate(a, b):
    """The certificate's verdict agrees byte-exactly with the EXISTING dense
    addition_lhs == addition_rhs compare on the region they DO resolve."""
    cert = RiemannTheta.fay_reindexing_certificate(a, b, box=BOX)
    assert cert["consistent_with_safe_region_gate"] is True
    safe = 2 * BOX * BOX
    assert cert["safe_region_bound"] == safe
    lhs = _cut(RiemannTheta.addition_lhs(a, b, BOX), safe)
    rhs = _cut(RiemannTheta.addition_rhs(a, b, BOX), safe)
    assert lhs == rhs                            # the old gate's own verdict
    assert lhs                                   # non-trivially populated


def test_consistency_with_addition_holds_gate():
    """The gate the certificate strengthens still holds (the rc73 build gate),
    and the certificate agrees with it on every pair it decides."""
    assert RiemannTheta.addition_holds(box=BOX) is True
    for (a, b) in PAIRS:
        cert = RiemannTheta.fay_reindexing_certificate(a, b, box=BOX)
        assert cert["consistent_with_safe_region_gate"] is True


@pytest.mark.parametrize("a,b", PAIRS)
def test_beyond_safe_region_witness_strengthens(a, b):
    """The witness monomial sits STRICTLY beyond the old safe region (so the
    restricted dense compare contains no such key — the old gate is blind to
    it), yet the certificate resolves its FULL exact coefficient on both
    sides, equal and (for these pairs) nonzero."""
    cert = RiemannTheta.fay_reindexing_certificate(a, b, box=BOX)
    w = cert["beyond_safe_region_witness"]
    safe = cert["safe_region_bound"]
    assert w["strictly_beyond"] is True
    assert w["diag_exponent"] > safe
    assert w["resolved"] is True
    assert w["lhs_coeff"] == w["rhs_coeff"]
    assert w["lhs_coeff"] > 0                    # a genuinely populated monomial
    # the old gate is blind to the witness: no restricted dense key reaches it
    lhs = _cut(RiemannTheta.addition_lhs(a, b, BOX), safe)
    assert w["monomial"] not in lhs
    assert all(k[0] <= safe for k in lhs)        # the region cannot contain it


def test_witness_worked_example_box8():
    """The pinned worked example: a=(1,0), b=(0,0), box=8 → witness monomial
    (1090, 0, 0) (A = 2·17² + 2·16² = 1090 > safe = 128) with FULL exact
    coefficient 8 on both sides — the two essentially-different
    representations 545 = 17² + 16² = 23² + 4² (u₁ odd, u₁' even), four sign
    combinations each, redistributed by φ across the r-sectors as
    33² + 1² = 27² + 19² = 1090."""
    cert = RiemannTheta.fay_reindexing_certificate((1, 0), (0, 0), box=8)
    w = cert["beyond_safe_region_witness"]
    assert w["monomial"] == (1090, 0, 0)
    assert cert["safe_region_bound"] == 128
    assert w["lhs_coeff"] == 8
    assert w["rhs_coeff"] == 8
    assert cert["every_order"] is True


def test_parity_sectors_are_the_rhs_r_sum():
    """The four parity sectors carry exactly the RHS characteristics
    (2r+a+b, 2r+a−b) — the r-sum of the shipped _spec_addition, with the mod-4
    index classes attached."""
    a, b = (1, 0), (0, 1)
    cert = RiemannTheta.fay_reindexing_certificate(a, b, box=BOX)
    sectors = cert["parity_sectors"]
    assert len(sectors) == 4
    seen = set()
    for s in sectors:
        r1, r2 = s["r"]
        assert s["char_plus"] == (2 * r1 + a[0] + b[0], 2 * r2 + a[1] + b[1])
        assert s["char_minus"] == (2 * r1 + a[0] - b[0], 2 * r2 + a[1] - b[1])
        assert s["sum_index_class_mod4"] == s["char_plus"]
        assert s["diff_index_class_mod4"] == s["char_minus"]
        seen.add((r1, r2))
    assert seen == {(0, 0), (0, 1), (1, 0), (1, 1)}
    # the sector data equals the shipped gate spec's r-enumeration (one SSOT)
    _lhs, rhs = rt._spec_addition(2, a, b)
    spec_chars = {(tuple(f1[2]), tuple(f2[2])) for (_s, (f1, f2)) in rhs}
    cert_chars = {(s["char_plus"], s["char_minus"]) for s in sectors}
    assert spec_chars == cert_chars


def test_closed_form_verifier_genuinely_decides():
    """The pure closed-form machinery is a real canonical-form decision, not a
    rubber stamp: the true parallelogram identities pass, a PERTURBED identity
    fails, and the linear-identity checker rejects a nonzero form."""
    assert RiemannTheta._fay_parallelogram_exact() is True
    assert RiemannTheta._fay_bijection_exact() is True
    e0 = (1, 0, 0, 0)
    s1, d1 = (1, 0, 1, 0), (1, 0, -1, 0)
    good_l = rt._fay_expand_quadratic([(2, e0, e0), (2, (0, 0, 1, 0),
                                                    (0, 0, 1, 0))], 4)
    good_r = rt._fay_expand_quadratic([(1, s1, s1), (1, d1, d1)], 4)
    assert good_l == good_r
    bad_r = rt._fay_expand_quadratic([(1, s1, s1), (2, d1, d1)], 4)
    assert good_l != bad_r                       # a perturbed identity FAILS
    assert rt._fay_linear_zero([(1, (1, 1, 0)), (-1, (1, 1, 0))], 3) is True
    assert rt._fay_linear_zero([(1, (1, 1, 0)), (-1, (1, 0, 0))], 3) is False


@pytest.mark.parametrize("a,b", GENUINE[:3])
def test_native_equals_pure(a, b):
    """The C peer's five outputs equal the pure bodies byte-for-byte (the
    parity oracle) — parallelogram verdict, window verdict + tuple count, and
    both FULL witness coefficients."""
    wkey = RiemannTheta._fay_witness_key(a, b, BOX)
    got = _native.riemann_theta_fay_certificate_c(
        a[0], a[1], b[0], b[1], BOX, wkey[0], wkey[1], wkey[2])
    assert got is not None
    (c_par, c_win, c_tuples, c_lhs, c_rhs) = got
    assert c_par is True
    p_win, p_tuples = RiemannTheta._fay_window_check_py(a, b, BOX)
    assert (c_win, c_tuples) == (p_win, p_tuples)
    assert c_lhs == RiemannTheta._fay_witness_lhs_py(a, b, wkey)
    assert c_rhs == RiemannTheta._fay_witness_rhs_py(a, b, wkey)


def test_native_rejects_bad_input():
    """The C peer rejects non-bit characteristics and an out-of-family witness
    key loudly (SRMECH_ERR_BAD_INPUT → RuntimeError), never silently."""
    wkey = RiemannTheta._fay_witness_key((0, 0), (0, 0), BOX)
    with pytest.raises(RuntimeError):
        _native.riemann_theta_fay_certificate_c(
            2, 0, 0, 0, BOX, wkey[0], wkey[1], wkey[2])
    with pytest.raises(RuntimeError):
        _native.riemann_theta_fay_certificate_c(
            0, 0, 0, 0, BOX, -1, wkey[1], wkey[2])


def test_certificate_reports_native_dispatch():
    """With the native lib loaded the certificate reports the native hit (the
    computational parts ran in C; the closed-form proofs always run in
    Python — they ARE the logic)."""
    cert = RiemannTheta.fay_reindexing_certificate((1, 0), (0, 0), box=BOX)
    assert cert["native"] is True


def test_scope_names_the_open_and_never_claims_jacobian():
    """The scope string names the genus ≥ 5 Schottky OPEN (Krichever 2006 /
    Shiota 1986 / Grushevsky–Xie 2504.20243) and explicitly does NOT claim
    is-Jacobian / trisecant-decided."""
    cert = RiemannTheta.fay_reindexing_certificate((1, 0), (0, 0), box=BOX)
    s = cert["scope"]
    assert s == RiemannTheta.fay_trisecant_scope_note()
    assert "Schottky" in s
    assert "genus >= 5" in s
    assert "does NOT decide is-Jacobian" in s
    assert "Krichever 2006" in s
    assert "Shiota 1986" in s
    assert "2504.20243" in s
    assert "OPEN" in s
    # the REPRESENTABLE/OPEN split is explicit
    assert "REPRESENTABLE:" in s and "OPEN (not built):" in s


def test_certificate_shape_is_inspectable():
    """The witness object carries every promised inspectable field."""
    cert = RiemannTheta.fay_reindexing_certificate((1, 1), (1, 0), box=BOX)
    for key in ("identity", "a", "b", "box", "reindex_map", "parity_sectors",
                "quadratic_form_identity", "quadratic_form_identity_exact",
                "bijection_exact", "coeff_preserved", "every_order",
                "window_bijection_ok", "window_tuples_checked",
                "consistent_with_safe_region_gate", "safe_region_bound",
                "beyond_safe_region_witness", "native", "scope"):
        assert key in cert, f"missing certificate field {key!r}"
    assert "DLMF 21.6.8" in cert["identity"]
    assert "(m,m') -> (M,M')=(m+m', m-m')" in cert["reindex_map"]
    w = cert["beyond_safe_region_witness"]
    for key in ("monomial", "diag_exponent", "safe_region_bound",
                "strictly_beyond", "lhs_coeff", "rhs_coeff", "resolved",
                "note"):
        assert key in w, f"missing witness field {key!r}"


def test_box_validation():
    """box < 2 is rejected loudly (the addition_holds contract)."""
    with pytest.raises(ValueError):
        RiemannTheta.fay_reindexing_certificate((0, 0), (0, 0), box=1)
    with pytest.raises(ValueError):
        RiemannTheta.fay_reindexing_certificate((0, 0), (0, 0), box="8")


def test_characteristic_validation():
    """Non-bit characteristics are rejected loudly."""
    with pytest.raises(ValueError):
        RiemannTheta.fay_reindexing_certificate((2, 0), (0, 0), box=BOX)
    with pytest.raises(ValueError):
        RiemannTheta.fay_reindexing_certificate((0, 0), (0, -1), box=BOX)
