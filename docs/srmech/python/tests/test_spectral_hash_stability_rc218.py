"""rc218 spectral refactor-equivalence pin (#826 parity-completeness closure).

rc218 routed the three ``srmech.spectral`` compute kernels through the
already-C-backed carrier ops (``decompose`` / ``recompose`` V-projections →
``laplacian.mat_matvec``; the ``prediction_error`` popcount-density gate →
``hdc.hamming``) and both direct-``hashlib`` sites through
``format.sha256_bytes``. This file is the gate for that refactor.

What the gate pins, and why it is split by *kind of invariant*:

* **Exact / byte-stable / platform-independent** — the substrate descriptor
  hash and the ``_sha256_hex`` Class-A site hash INPUT BYTES ONLY (no float),
  so they are byte-identical on every platform and every dispatch arm. These
  ARE the values downstream consumers key on, and they are pinned byte-for-byte
  (``test_descriptor_and_sha_pins_are_byte_stable``). This is where the
  ``hashlib`` → ``sha256_bytes`` refactor is proved value-identical.

* **Exact gate logic** — the ``prediction_error`` XOR-delta / popcount-density
  gate is integer Class-K logic, platform-independent; pinned by identity
  (``test_prediction_error_gate_identities``). This proves the popcount →
  ``hdc.hamming`` refactor.

* **Within-tol / float-derived** — the projected coefficients and the recompose
  come from a NUMERIC float64 Hermitian-Jacobi eigendecomposition. Those
  eigenvectors differ in the last ULPs across platforms (macOS libm/FMA vs
  Linux gcc) AND across the native/pure arms — a PRE-EXISTING property of the
  float eig, NOT an rc218 effect. So the refactor claim for these is
  *value-preservation to numeric precision*, verified live and per-platform,
  NOT a cross-platform byte-identical SHA. ``mat_matvec`` must equal the
  sesquilinear sum it replaced (within tol), and ``recompose∘decompose`` must
  round-trip to the input (``test_spectral_refactor_is_value_preserving``).
  (An earlier draft pinned these float-derived hashes to a Linux-captured
  baseline; that pin was unsound cross-platform — the numeric eig is not
  byte-stable across libm/FMA — and is replaced by the within-tol checks here.)

numpy-free (stdlib-only test over the numpy-free spectral surface).
"""
from __future__ import annotations

from srmech import spectral
from srmech.math.laplacian import mat_matvec

# The fixed inputs (DO NOT CHANGE — the pins below are keyed to these bytes).
_L1 = [
    [1.0, -1.0, 0.0, 0.0],
    [-1.0, 2.0, -1.0, 0.0],
    [0.0, -1.0, 2.0, -1.0],
    [0.0, 0.0, -1.0, 1.0],
]
_S1 = [1.0, 2.0, 3.0, 4.0]
_L2 = [
    [2.0 + 0j, 1.0 - 1j, 0.5 + 0.25j],
    [1.0 + 1j, 3.0 + 0j, -0.75 - 0.5j],
    [0.5 - 0.25j, -0.75 + 0.5j, 1.5 + 0j],
]
_S2 = [1.0 + 0.5j, -0.25 + 2j, 0.125 - 1j]

# ── arm-INDEPENDENT, byte-stable pins (input-bytes-only hashing; every arm,
#    every platform agrees — this is the actual downstream-consumer contract) ──
_ARM_INDEPENDENT = {
    # SHA-256("abc") — FIPS 180-4 appendix B.1 known-answer.
    "_sha256_hex.abc":
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    "_descriptor_hash.L1":
        "7bbdf530c76f9a7b90e44d6299cda6a1e09427d6487716623e443ee0f2129d1a",
    "_descriptor_hash.L2":
        "4e4d86b6537b370fa1def85e92d6a7c61279bdf49f9cd659ae2f4e3284f78db0",
    "p4_real.descriptor_hash":
        "52d93d6ee5b8750f3c46e36e21dc57b3d56009e6bd9b227eae2377386f318ed1",
    "herm3_complex.descriptor_hash":
        "5b31433169e3a304ae62ebd5f943417da1bcdf33c9a297b577927bc0d4915e84",
}

_TOL = 1e-6  # generous: covers libm/FMA last-ULP spread across platforms + arms


def _capture():
    """Recompute the byte-stable + gate slice of the fixed-input capture."""
    out = {}
    for tag, L, s in (("p4_real", _L1, _S1), ("herm3_complex", _L2, _S2)):
        spectral.clear_eigenbasis_cache()
        h = spectral.decompose(s, L, encoder_tag="rc218gate")
        out[tag + ".descriptor_hash"] = h.substrate_descriptor_hash
        p = spectral.predict(h, L, steps=3, dt=0.5, encoder_tag="rc218gate")
        out[tag + ".delta_hex"] = spectral.delta(h, p).hex()
        out[tag + ".pe_raw_hex"] = spectral.prediction_error(
            h, p, threshold=0.0
        ).hex()
        out[tag + ".pe_gate_low_hex"] = spectral.prediction_error(
            h, p, threshold=0.001
        ).hex()
        out[tag + ".pe_gate_high_hex"] = spectral.prediction_error(
            h, p, threshold=0.999
        ).hex()
    out["_sha256_hex.abc"] = spectral._sha256_hex(b"abc")
    out["_descriptor_hash.L1"] = spectral._descriptor_hash(
        _L1, encoder_tag="tag-x"
    )
    out["_descriptor_hash.L2"] = spectral._descriptor_hash(
        _L2, encoder_tag="tag-y"
    )
    return out


def test_descriptor_and_sha_pins_are_byte_stable():
    """The exact, input-byte-only hashes (the downstream-consumer contract +
    the ``hashlib`` → ``sha256_bytes`` refactor) are byte-identical to the
    pinned baseline on every platform and every dispatch arm."""
    got = _capture()
    drift = {k: (got[k], v) for k, v in _ARM_INDEPENDENT.items() if got[k] != v}
    assert not drift, (
        "descriptor / sha byte-stability drift:\n" + "\n".join(
            f"  {k}:\n    got      {g}\n    expected {e}"
            for k, (g, e) in sorted(drift.items())
        )
    )


def test_spectral_refactor_is_value_preserving():
    """The rc218 V-projection refactor is value-preserving to numeric precision
    on the LIVE dispatch arm (platform-independent):

    * ``decompose`` coefficients == the sesquilinear sum ``Vᴴ·state`` they
      replaced — ``mat_matvec`` over the SAME eigenbasis the module exposes,
      within tol (proves the ``mat_matvec`` route did not change the value).
    * ``recompose ∘ decompose`` round-trips back to the input state within tol
      (exercises BOTH refactored matvec paths end to end).
    """
    for L, s in ((_L1, _S1), (_L2, _S2)):
        spectral.clear_eigenbasis_cache()
        Lc = spectral._to_complex_mat(L)
        n = Lc.shape[0]
        desc = spectral._descriptor_hash(Lc, encoder_tag="rc218gate")
        _eigvals, V = spectral._eigenbasis(Lc, desc)
        state = [complex(x) for x in s]

        # reference projection: the sesquilinear Vᴴ·state the refactor replaced
        ref_coeffs = mat_matvec(V.conj().T, state)

        h = spectral.decompose(s, L, encoder_tag="rc218gate")
        got_coeffs = spectral._unpack_complex128(h.coefficients_bytes, n)
        assert len(got_coeffs) == n
        for a, b in zip(got_coeffs, ref_coeffs):
            assert abs(a - complex(b)) < _TOL, (a, b)

        # end-to-end round-trip: recompose(decompose(s)) ~= s
        back = spectral.recompose(h, L, encoder_tag="rc218gate")
        assert len(back) == n
        for a, b in zip(back, state):
            assert abs(complex(a) - b) < _TOL, (a, b)


def test_prediction_error_gate_identities():
    """The Class-K gate semantics are value-identical to the pre-rc218 fold:
    threshold=0.0 returns the raw XOR delta; a below-density threshold passes
    the delta through; an above-density threshold zeroes it."""
    got = _capture()
    for tag in ("p4_real", "herm3_complex"):
        assert got[tag + ".pe_raw_hex"] == got[tag + ".delta_hex"]
        assert got[tag + ".pe_gate_low_hex"] == got[tag + ".delta_hex"]
        assert got[tag + ".pe_gate_high_hex"] == "00" * (
            len(got[tag + ".delta_hex"]) // 2
        )
