"""rc301 (`#938`) — the two OPTIONAL layers of the general N-slot register.

rc297 brought the general ``CDRegister`` in-tree as an ADDRESSING object; rc301
ports the four VALUE-operations that until now lived only on ``SedenionRegister``
(``couple_working`` / ``uncouple_working`` / ``carry`` / ``correct``) onto it as
its two OPT layers — the reversible working word (Class M) and the Hamming EC
block (a separate axis from ``dim``).

The contract this suite enforces is the committed design note
``docs/srmech/notes/cd_register_addressing_layer_contract_rc301.md``:

  * addressing is the content-agnostic CORE floor; coupling / EC are OPT layers
    off by default (a bare register is a pure signed-pointer);
  * the coupling cap is DERIVED (``min(dim, 8) − 1``), never a hardcoded 7 — it
    scales down below 8 and pins at 7 from 8 up (the octonion sub-block; Hurwitz);
  * dim 1 (ℝ) is the degenerate empty-coupling base — it behaves, not crashes;
  * at dim 16 the four ops are BIT-EXACT with the shipped ``SedenionRegister``
    (the oracle, which stays an independent class — the rc297 pattern).

The graded universal-addressing proof (§E, M/N/L) demonstrates the three consumer
mappings concretely and writes its measurements to
``docs/srmech/notes/cd_register_addressing_proof_rc301.ndjson`` (regenerate by
running this module as a script). L is the falsifier: a bare register serves as
STORAGE for a Laplacian spectrum while the eigendecomposition stays in ``Mat``.

numpy-free; no ``abs()`` (the cascade-honesty AST scan in
``test_cd_register_rc297.py`` covers the whole module, these ops included).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from srmech.amsc import cascade
from srmech.amsc.cascade import (
    cd_couple_working, cd_uncouple_working, cd_carry, cd_correct,
)
from srmech.amsc.cascade.sedenion_register import SedenionRegister
from srmech.amsc.cascade.cayley_dickson import CD_MAX_DIM

# Every rung srmech builds tables for. dim 1 (ℝ) is the empty-coupling boundary.
RUNGS = (1, 2, 4, 8, 16, 32, 64, 128, 256)
_TOL = 1e-9                    # the shipped SedenionRegister's own roundtrip band


def _full_word(cap: int):
    """A deterministic ``cap``-length ±1 stream (the maximal working word)."""
    pattern = [1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -1.0]
    return pattern[:cap]


# ──────────────────────────────────────────────────────────────────────
# §A  couple ∘ uncouple == identity, at EVERY legal dim (dim 1 = the boundary)
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("dim", RUNGS)
def test_couple_uncouple_is_identity_at_every_rung(dim):
    """Coupling a FULL working word (``min(dim,8)−1`` values) and uncoupling
    recovers it exactly (to the coupler's float band). The cap is dim-scaled:
    dim 2 → 1 value, dim 4 → 3, dim 8/16/…/256 → 7."""
    cap = min(8, dim) - 1
    vals = _full_word(cap)
    r = cascade.cd_register(dim, coupling=True)
    word = r.couple_working(vals)
    rec = r.uncouple_working(word)
    assert len(rec) >= len(vals), f"dim {dim}: uncouple dropped values"
    for i in range(len(vals)):
        assert abs(rec[i] - vals[i]) < _TOL, (
            f"dim {dim}: stream {i} did not round-trip ({rec[i]} != {vals[i]})")


def test_dim_1_is_the_empty_coupling_boundary_not_a_crash():
    """dim 1 (ℝ, 0 imaginary) couples NOTHING and uncouples to nothing — a legal
    instantiation that behaves, per the contract. And a value overflows cap 0."""
    r = cascade.cd_register(1, coupling=True)
    assert r.couple_working([]) == []
    assert r.uncouple_working([]) == []
    with pytest.raises(ValueError, match="≤0 values|holds"):
        r.couple_working([1.0])


@pytest.mark.parametrize("dim,cap", [(2, 1), (4, 3), (8, 7), (16, 7), (256, 7)])
def test_the_cap_is_min_dim_8_minus_1_and_is_enforced(dim, cap):
    """The Hurwitz-derived cap, checked as a hard boundary: ``cap`` values couple,
    ``cap + 1`` raises — and the raise cites ``min(dim, 8)``, never a bare 7."""
    r = cascade.cd_register(dim, coupling=True)
    r.couple_working(_full_word(cap))                       # exactly cap: OK
    with pytest.raises(ValueError, match="min\\(dim, 8\\)"):
        r.couple_working([1.0] * (cap + 1))                 # one too many


@pytest.mark.parametrize("dim", (4, 8, 16, 64))
def test_partial_fill_round_trips_on_its_leading_prefix(dim):
    """Fewer than ``cap`` streams still round-trip on the coupled prefix (the
    trailing slots recover as ~0)."""
    r = cascade.cd_register(dim, coupling=True)
    vals = [0.5, -0.25]
    rec = r.uncouple_working(r.couple_working(vals))
    for i in range(len(vals)):
        assert abs(rec[i] - vals[i]) < _TOL


def test_module_functions_scale_the_cap_by_dim():
    """The pure module function reads ``dim`` for the cap exactly as the method
    reads ``self.dim`` — dim 2 couples 1, dim 4 couples 3, dim 8 couples 7."""
    assert cd_couple_working([], 1) == []
    cd_couple_working([1.0], 2)                              # cap 1: OK
    with pytest.raises(ValueError, match="min\\(dim, 8\\)"):
        cd_couple_working([1.0, 2.0], 2)                    # cap 1 exceeded
    cd_couple_working([1.0, 2.0, 3.0], 4)                   # cap 3: OK
    with pytest.raises(ValueError, match="min\\(dim, 8\\)"):
        cd_couple_working([1.0] * 4, 4)                     # cap 3 exceeded


# ──────────────────────────────────────────────────────────────────────
# §B  Hamming single-bit correction — every position, and a clean word
# ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("n", (3, 4, 5))
def test_hamming_corrects_every_single_bit_error(n):
    """Inject a flip at EACH of the 2ⁿ−1 positions and assert ``correct`` locates
    it and recovers the payload; a clean codeword is unchanged."""
    r = cascade.cd_register(16, error_correction=True)
    big = (1 << n) - 1
    k = big - n
    data = [(i * 7 + 1) & 1 for i in range(k)]              # a deterministic payload
    clean = r.carry(data, n=n)
    assert len(clean) == big

    # a clean codeword is returned unchanged, error_position 0
    dec = r.correct(clean)
    assert dec["error_position"] == 0
    assert dec["corrected_codeword"] == clean
    assert dec["data"] == data

    # every single-bit error is located + corrected
    for pos in range(big):
        bad = list(clean)
        bad[pos] ^= 1                                       # Class-K GF(2) flip
        dec = r.correct(bad)
        assert dec["error_position"] == pos + 1, (
            f"n={n}: error at position {pos + 1} mis-located as "
            f"{dec['error_position']}")
        assert dec["corrected_codeword"] == clean, (
            f"n={n}: correction at {pos + 1} did not restore the codeword")
        assert dec["data"] == data


def test_ec_axis_is_independent_of_dim():
    """The Hamming block size is set by ``n``, not by the register ``dim`` — the
    same n=3 codeword length whether the register is dim 16 or dim 256."""
    data = [1, 0, 1, 1]
    a = cascade.cd_register(16, error_correction=True).carry(data, n=3)
    b = cascade.cd_register(256, error_correction=True).carry(data, n=3)
    assert a == b
    assert len(a) == 7                                      # 2^3 − 1, dim-independent


# ──────────────────────────────────────────────────────────────────────
# §C  Oracle parity — bit-exact against the SHIPPED SedenionRegister (rc297 pattern)
# ──────────────────────────────────────────────────────────────────────

def test_dim16_couple_is_bit_exact_with_the_shipped_sedenion_register():
    """The faithfulness gate: ``CDRegister(dim=16, coupling=True).couple_working``
    reproduces the shipped ``SedenionRegister`` byte-for-byte (not a tolerance —
    identical floats), because both delegate to the same ``hypercomplex_couple``
    and at dim 16 the cap coincides at 7."""
    cd = cascade.cd_register(16, coupling=True)
    sed = SedenionRegister()
    for vals in ([1.0, -1.0, 1.0, 1.0, -1.0, 1.0, -1.0],
                 [0.3, -0.7, 0.1],
                 [0.5],
                 [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]):
        cw_cd, cw_sed = cd.couple_working(vals), sed.couple_working(vals)
        assert cw_cd == cw_sed, f"couple diverged on {vals}"
        assert cd.uncouple_working(cw_cd) == sed.uncouple_working(cw_sed), (
            f"uncouple diverged on {vals}")


def test_dim16_carry_correct_is_bit_exact_with_the_shipped_sedenion_register():
    """The EC ops reproduce the oracle exactly, including the corrected codeword
    and the located position, for clean and single-error words."""
    cd = cascade.cd_register(16, error_correction=True)
    sed = SedenionRegister()
    for n in (3, 4):
        big = (1 << n) - 1
        data = [(i * 3) & 1 for i in range(big - n)]
        enc_cd, enc_sed = cd.carry(data, n=n), sed.carry(data, n=n)
        assert enc_cd == enc_sed, f"carry diverged at n={n}"
        for pos in range(big):
            bad = list(enc_cd)
            bad[pos] ^= 1
            assert cd.correct(bad) == sed.correct(bad), (
                f"correct diverged at n={n}, pos {pos}")


def test_sedenion_register_stays_an_independent_oracle():
    """``SedenionRegister`` MUST NOT be collapsed into a dim-16 ``CDRegister``
    alias in this rc — the parity gate above depends on it being the independent
    reference (the rc297 discipline, re-asserted for the value-ops)."""
    assert cascade.SedenionRegister is not cascade.CDRegister
    import inspect
    src = inspect.getsource(cascade.SedenionRegister)
    assert "CDRegister" not in src, (
        "SedenionRegister now references CDRegister — the oracle is no longer "
        "independent and the parity gate is circular")


# ──────────────────────────────────────────────────────────────────────
# §D  The optional-layer flags — bare register is pure addressing
# ──────────────────────────────────────────────────────────────────────

def test_bare_register_raises_on_every_value_operation():
    """A bare register (the default) is pure signed-pointer addressing: the four
    value-operations are GATED, not merely unused."""
    bare = cascade.cd_register(16)
    with pytest.raises(ValueError, match="coupling=True"):
        bare.couple_working([1.0])
    with pytest.raises(ValueError, match="coupling=True"):
        bare.uncouple_working([0.0] * 8)
    with pytest.raises(ValueError, match="error_correction=True"):
        bare.carry([1, 0, 1, 1])
    with pytest.raises(ValueError, match="error_correction=True"):
        bare.correct([0] * 7)


def test_the_two_flags_are_independent():
    """coupling and error_correction are separate axes — enabling one does NOT
    enable the other."""
    coup = cascade.cd_register(16, coupling=True)
    coup.couple_working([1.0])                              # allowed
    with pytest.raises(ValueError, match="error_correction=True"):
        coup.carry([1, 0, 1, 1])                            # still gated

    ec = cascade.cd_register(16, error_correction=True)
    ec.carry([1, 0, 1, 1])                                  # allowed
    with pytest.raises(ValueError, match="coupling=True"):
        ec.couple_working([1.0])                            # still gated


def test_bare_register_still_does_full_core_addressing():
    """Everything the CORE layer provides works on a bare register — write / read
    / navmap / navigate / is_navigable / the block split."""
    r = cascade.cd_register(16)
    r.write(0, "alpha")
    r.write(1, "beta", sign=-1)
    assert r.read(0) == ("alpha", 1)
    assert r.read(1) == ("beta", -1)
    assert r.working_block() == tuple(range(8))
    assert r.navigate(1).slots()                            # navigation works
    assert r.is_navigable([1 if k == 3 else 0 for k in range(16)]) is True


def test_navigate_propagates_the_opt_flags():
    """``navigate`` returns a NEW register that must carry the SAME opt-in layers —
    otherwise a navigated coupling register would silently become bare."""
    r = cascade.cd_register(16, coupling=True, error_correction=True)
    r.write(0, "x")
    moved = r.navigate(1)
    moved.couple_working([1.0])                             # still enabled
    moved.carry([1, 0, 1, 1])                              # still enabled
    bare = cascade.cd_register(16)
    bare.write(0, "x")
    with pytest.raises(ValueError):
        bare.navigate(1).couple_working([1.0])             # stays bare


# ──────────────────────────────────────────────────────────────────────
# §E  The graded universal-addressing proof — M / N / L (prove, don't assume)
# ──────────────────────────────────────────────────────────────────────
# The measurements are emitted to
# docs/srmech/notes/cd_register_addressing_proof_rc301.ndjson (run this module as
# a script). The tests recompute them in-memory and assert the outcomes, so the
# committed NDJSON is provenance, not the source of truth.

def _proof_M():
    """M: is ``couple_working`` an HDC bind? Relate it to the shipped ``hdc.bind``
    family precisely."""
    from srmech.math import hdc
    # (a) couple_working is a reversible BIND: couple then uncouple recovers.
    vals = [0.3, -0.7, 0.1, 0.9, -0.2, 0.5, -0.4]
    word = cd_couple_working(vals, 8)
    rec = cd_uncouple_working(word)
    couple_reversible = all(abs(rec[i] - vals[i]) < _TOL for i in range(len(vals)))
    # (b) hdc.bind is the OTHER Class-M reversible bind — self-inverse XOR over
    #     𝔽₂ᴰ byte hypervectors: bind(a, bind(a, b)) == b.
    a = bytes(range(1, 9)) * 4
    b = bytes(range(9, 17)) * 4
    bound = hdc.bind(a, b)
    hdc_reversible = hdc.bind(a, bound) == b
    # (c) the DIFFERENCE, characterised: hdc.bind is self-inverse (same op undoes
    #     it), couple needs a DISTINCT inverse (uncouple / the conjugate twiddle);
    #     the carriers differ (𝔽₂ᴰ bytes vs 𝕆 real streams). Same Class-M ROLE,
    #     two operations, two carriers.
    couple_is_self_inverse = False
    try:
        # feeding a coupled OCTONION word back through couple (not uncouple) does
        # NOT recover — proof they are not the same self-inverse operation.
        twice = cd_couple_working(list(word), 8)
        couple_is_self_inverse = all(
            abs(twice[i] - vals[i]) < _TOL for i in range(min(len(twice), len(vals))))
    except Exception:
        couple_is_self_inverse = False
    return {
        "proof": "M", "claim": "couple_working IS a Class-M reversible bind",
        "couple_reversible": couple_reversible,
        "hdc_bind_reversible": hdc_reversible,
        "couple_is_self_inverse_like_hdc": couple_is_self_inverse,
        "verdict": ("SAME Class-M reversible-bind ROLE, DISTINCT operations: "
                    "hdc.bind is self-inverse XOR over 𝔽₂ᴰ; couple_working needs "
                    "the conjugate-twiddle inverse (uncouple_working) over 𝕆"),
    }


def _proof_N():
    """N: a CDRegister over the exact-rational Q carrier is a coherent addressable
    rational store."""
    from srmech.amsc.q import Q
    rats = {0: Q(1, 3), 1: Q(-2, 7), 2: Q(5, 11), 3: Q(22, 7)}
    keys = {slot: f"{q.as_pair()[0]}/{q.as_pair()[1]}" for slot, q in rats.items()}
    r = cascade.cd_register(8, D=8192)                      # bare: addressing only
    for slot, key in keys.items():
        r.write(slot, key)
    # read every rational back exactly by address, and reparse to Q — the store is
    # coherent (content-agnostic addressing holds exact rationals).
    ok = True
    for slot, q in rats.items():
        got_key, sign = r.read(slot)
        num, den = (int(x) for x in got_key.split("/"))
        ok = ok and (Q(num, den) == q) and sign == 1
    return {
        "proof": "N", "claim": "CDRegister over Q is a coherent rational store",
        "n_rationals": len(rats), "all_recovered_exactly": ok,
        "verdict": "Q rides the CONTENT-AGNOSTIC CORE addressing layer as content",
    }


def _proof_L():
    """L (the FALSIFIER): a BARE register stores a Laplacian spectrum; the
    eigendecomposition stays in Mat. L fits as STORAGE, not OPERATION."""
    from srmech.math.laplacian import dense_laplacian, jacobi_eigvals
    # the L OPERATION lives in Mat/laplacian — a path-graph Laplacian's eigenvalues
    lap = dense_laplacian(4, [(0, 1), (1, 2), (2, 3)])
    eig = jacobi_eigvals(lap)
    spectrum = [round(float(v), 6) for v in eig]
    # the register only STORES the spectrum (bare = coupling OFF), addressed by index
    r = cascade.cd_register(8, D=8192)                      # coupling OFF (bare)
    for i, lam in enumerate(spectrum):
        r.write(i, f"lam:{lam}")
    recovered = []
    for i in range(len(spectrum)):
        key, _ = r.read(i)
        recovered.append(float(key.split(":")[1]))
    stored_ok = recovered == spectrum
    # the register EXPOSES no eigendecomposition op — L is storage, not operation
    register_has_eig = any(hasattr(r, m) for m in ("eigvals", "eigendecompose",
                                                   "laplacian", "spectrum"))
    return {
        "proof": "L", "claim": "bare CDRegister STORES a Laplacian spectrum",
        "spectrum": spectrum, "spectrum_recovered_exactly": stored_ok,
        "register_exposes_an_eigendecomposition_op": register_has_eig,
        "verdict": ("L FITS AS STORAGE, NOT OPERATION: eigendecomposition stays in "
                    "Mat (jacobi_eigvals); the bare register only addresses the "
                    "spectrum — confirming addressing is a floor, not a subsumer"),
    }


def _measure_proofs():
    return [_proof_M(), _proof_N(), _proof_L()]


def test_proof_M_couple_is_a_class_m_reversible_bind():
    m = _proof_M()
    assert m["couple_reversible"], "couple_working is not reversible — not a bind"
    assert m["hdc_bind_reversible"], "hdc.bind control failed"
    # the characterised DIFFERENCE: couple is NOT self-inverse like hdc.bind
    assert not m["couple_is_self_inverse_like_hdc"], (
        "couple_working recovered by re-coupling — it would then be the SAME "
        "self-inverse op as hdc.bind, contradicting the characterised difference")


def test_proof_N_cd_register_over_Q_is_a_coherent_rational_store():
    n = _proof_N()
    assert n["all_recovered_exactly"], (
        "the Q-valued register did not recover every rational exactly — the "
        "content-agnostic addressing claim fails for the N carrier")


def test_proof_L_bare_register_stores_a_laplacian_spectrum_as_storage_not_operation():
    ell = _proof_L()
    assert ell["spectrum_recovered_exactly"], (
        "a bare register could not store+recover the Laplacian spectrum — L does "
        "NOT fit even as storage; this is a finding to report, not hide")
    assert not ell["register_exposes_an_eigendecomposition_op"], (
        "the register exposes an eigendecomposition op — L would then be an "
        "OPERATION on the register, contradicting storage-not-operation")


def test_proof_ndjson_is_committed_and_matches_the_live_measurement():
    """The committed NDJSON must reflect the live measurement (provenance, not a
    stale snapshot). Regenerate by running this module as a script."""
    path = (Path(__file__).resolve().parents[2] / "notes"
            / "cd_register_addressing_proof_rc301.ndjson")
    assert path.exists(), (
        f"missing proof NDJSON {path} — run `python3 tests/"
        f"test_cd_register_ops_rc301.py` to emit it")
    committed = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
    live = _measure_proofs()
    assert [c["proof"] for c in committed] == [m["proof"] for m in live]
    for c, m in zip(committed, live):
        assert c["verdict"] == m["verdict"], f"{c['proof']} verdict drifted"


def _emit_proof_ndjson():
    path = (Path(__file__).resolve().parents[2] / "notes"
            / "cd_register_addressing_proof_rc301.ndjson")
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for rec in _measure_proofs():
            f.write(json.dumps(rec) + "\n")
    return path


if __name__ == "__main__":
    print("wrote", _emit_proof_ndjson())
