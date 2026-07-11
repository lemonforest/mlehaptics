"""rc218 spectral hash-stability pin (#826 parity-completeness closure).

rc218 routed the three ``srmech.spectral`` compute kernels through the
already-C-backed carrier ops (``decompose`` / ``recompose`` V-projections →
``laplacian.mat_matvec``; the ``prediction_error`` popcount-density gate →
``hdc.hamming``) and both direct-``hashlib`` sites through
``format.sha256_bytes``. The GATE for that refactor: the spectral handle's
descriptor / content SHA-256 for a fixed input must be BYTE-IDENTICAL to
rc217 — downstream consumers key on those hashes, so any drift is a shipping
blocker, not a tolerance question.

This file pins the rc217-captured values (captured at 0.9.0rc217 =
207d182e with the SAME fixed inputs, on BOTH dispatch arms — the native
capture with the gcc-13.4 ``libsrmech.so`` loaded, the pure capture with it
absent). rc218 was verified byte-identical on both arms before shipping;
this test keeps every later rc honest against the same baseline.

Two pin dicts because the two arms legitimately differ in eigenBASIS (the
native and pure Hermitian-Jacobi sweeps converge to different — equally
valid — eigenvector phase/order choices, a PRE-EXISTING rc217 property, so
the projected coefficient bytes differ per arm). What is arm-INDEPENDENT and
pinned once: the substrate descriptor hash (input-bytes only) and the
``_sha256_hex`` Class-A site. Within each arm every value is exact/pinned.

numpy-free (stdlib-only test over the numpy-free spectral surface).
"""
from __future__ import annotations

from srmech import spectral
from srmech.amsc import _native

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

# ── arm-INDEPENDENT pins (input-bytes-only hashing; both arms agree) ─────────
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

# ── NATIVE arm (HAS_NATIVE=True; rc217 baseline, gcc-13.4 libsrmech.so) ──────
_NATIVE_PINNED = {
    "p4_real.content_sha":
        "9822c1ec99401c83524ab5c593476072b05ceee46a4688c9a265f16ef282c54a",
    "p4_real.predict_content_sha":
        "c81bff45999162e04c7dd8a6cb5c26a1ffa6a3bca5b2827d54b658d4af3260a6",
    "p4_real.truncate_content_sha":
        "2f4d4cf36b984548c8bf091cd0f6cf1640816abf3c9aea6934a1628e07d620cd",
    "p4_real.coefficients_hex":
        "00000000000014400000000000000000d11b6f3cf2d70140000000000000000000000000"
        "0000d0bc0000000000000000988f0fa2244ac43f0000000000000000",
    "p4_real.recompose_repr":
        "[(0.9999999999999998+0j), (2.000000000000001+0j), (3+0j), "
        "(4.000000000000001+0j)]",
    "herm3_complex.content_sha":
        "96a11205642589430cd8dd7ddb5555aaf593506ba19f7d44e967ddf1a41fda5e",
    "herm3_complex.predict_content_sha":
        "60da837ff6fed128c850835e0c6866d51fd932f25ae94231e663c4e5c3c0bad3",
    "herm3_complex.truncate_content_sha":
        "75d102d5a2a16743da9fbae07fb325462ee3e79c6532b2703298297a0918e492",
    "herm3_complex.coefficients_hex":
        "02098cc6202db5bf807538496de1903f167b52369e6bcb3f5143f194e9c2e3bfa2f6406a"
        "1310b4bf1d12752b5a690340",
    "herm3_complex.recompose_repr":
        "[(1.0000000000000013+0.5000000000000011j), "
        "(-0.2500000000000002+2.0000000000000027j), (0.125-1.0000000000000009j)]",
}

# ── PURE arm (HAS_NATIVE=False; rc217 baseline, stdlib fallback) ─────────────
_PURE_PINNED = {
    "p4_real.content_sha":
        "4d1fd5232833249ee384cc95ee3a9a05a6b9e941c44fc6725a813aaeef6b1de4",
    "p4_real.predict_content_sha":
        "b97b9c56207e90a74831349d1be8b0e6b06fedbc22ec831a95757e9222612128",
    "p4_real.truncate_content_sha":
        "2f4d4cf36b984548c8bf091cd0f6cf1640816abf3c9aea6934a1628e07d620cd",
    "p4_real.coefficients_hex":
        "00000000000014400000000000000000d11b6f3cf2d70140000000000000000000000000"
        "0000d8bc0000000000000000a88f0fa2244ac43f0000000000000000",
    "p4_real.recompose_repr":
        "[(0.9999999999999999+0j), (2.0000000000000004+0j), "
        "(2.9999999999999996+0j), (4.000000000000002+0j)]",
    "herm3_complex.content_sha":
        "31155d616878f1f73695906cc7702891ba1362899039fd746247d5e6b8b0309f",
    "herm3_complex.predict_content_sha":
        "1d44f8a89336edd316a0cd6185f539f6d07c5d8aed6b51c0aa2b9de60bb27040",
    "herm3_complex.truncate_content_sha":
        "b3a14a5b3fbb305fe76f4664dde5b35027528089f19579649dada09c17548901",
    "herm3_complex.coefficients_hex":
        "78538d3f2d5eb2bfb00ff9d42bb4a63f10351d247532ddbf0803ef8d86f5ddbf2f61b8b2"
        "35660340747310c4c4d6bdbf",
    "herm3_complex.recompose_repr":
        "[(1.0000000000000349+0.4999999999999567j), "
        "(-0.2500000000000241+2.0000000000000138j), "
        "(0.12500000000001313-0.9999999999999787j)]",
}


def _capture():
    """Recompute the full fixed-input capture (mirrors the rc217/rc218 gate)."""
    out = {}
    for tag, L, s in (("p4_real", _L1, _S1), ("herm3_complex", _L2, _S2)):
        spectral.clear_eigenbasis_cache()
        h = spectral.decompose(s, L, encoder_tag="rc218gate")
        out[tag + ".descriptor_hash"] = h.substrate_descriptor_hash
        out[tag + ".content_sha"] = h.content_sha
        out[tag + ".coefficients_hex"] = h.coefficients_bytes.hex()
        p = spectral.predict(h, L, steps=3, dt=0.5, encoder_tag="rc218gate")
        out[tag + ".predict_content_sha"] = p.content_sha
        t = spectral.truncate_sparse(h, keep_k=2)
        out[tag + ".truncate_content_sha"] = t.content_sha
        out[tag + ".recompose_repr"] = repr(
            spectral.recompose(h, L, encoder_tag="rc218gate")
        )
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


def test_spectral_handle_hashes_are_rc217_byte_stable():
    """The rc218 refactor gate, kept live: descriptor + content SHA-256 (and
    the raw coefficient bytes + exact recompose values) for the fixed inputs
    equal the rc217-captured baseline BYTE-FOR-BYTE on the live dispatch arm."""
    got = _capture()
    pinned = dict(_ARM_INDEPENDENT)
    pinned.update(_NATIVE_PINNED if _native.HAS_NATIVE else _PURE_PINNED)
    drift = {
        k: (got[k], v) for k, v in pinned.items() if got[k] != v
    }
    assert not drift, (
        "spectral handle hash/value drift vs the rc217 baseline "
        f"(arm={'native' if _native.HAS_NATIVE else 'pure'}):\n" + "\n".join(
            f"  {k}:\n    got      {g}\n    expected {e}"
            for k, (g, e) in sorted(drift.items())
        )
    )


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
