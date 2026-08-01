"""rc219 (gh #827): srmech_spectral_decompose / _recompose parity gate.

The C peers collapse the per-state half of `srmech.spectral.decompose` /
`recompose` over the CACHED eigenbasis — carrier marshal + Vᴴ·state (or
V·coeffs) matvec + complex128 pack + content sha — into ONE C crossing, fed
zero-copy from the eigenvector ``Mat`` buffer. The eigendecomposition itself
is NOT re-implemented (the existing LRU cache stays); rc219 also memoizes the
substrate descriptor hash by carrier identity (Python-side only).

PARITY KIND (the rc218 macOS CI lesson, made a build constraint): these are
FLOAT-eig-derived NUMERIC values, byte-UNSTABLE across platforms/arms (libm /
FMA last-ULP divergence in the eigenvectors). So this gate pins:

* **same-machine kernel-equality** — native `decompose`/`recompose` ==
  the rc218 ``mat_matvec`` composition run on the SAME cached eigenbasis,
  byte-for-byte (both routes dispatch the SAME
  ``srmech_dense_matmul_complex`` kernel over the same bytes) — this holds on
  a no-C host too (both sides then take the same pure route);
* **round-trip** — ``recompose(decompose(state)) ≈ state`` within 1e-9
  (the rc148–151 numeric contract), on the live arm AND on the in-file
  forced-pure arm (``monkeypatch.setattr(_native, "HAS_NATIVE", False)`` —
  the house rc213/rc217 convention; the eigenbasis LRU is cleared around it
  because the cache key is arm-independent);
* **input-byte-derived hashes** — the descriptor hash (memoized + the
  complex-buffer fast path) is byte-identical to the struct-pack loop it
  replaced (these ARE cross-platform-stable — no float in the preimage).

It deliberately pins NO cross-platform coefficient SHA.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from srmech import spectral
from srmech.amsc import _native
from srmech.math.laplacian import mat_matvec
from srmech.amsc.mat import Mat
from srmech.spectral import (
    _complex128_bytes,
    _descriptor_hash,
    _eigenbasis,
    _sha256_hex,
    _unpack_complex128,
)

_TOL = 1e-9

_L_SMALL = [
    [2.0 + 0j, 1.0 - 1j, 0.5 + 0.25j],
    [1.0 + 1j, 3.0 + 0j, -0.75 - 0.5j],
    [0.5 - 0.25j, -0.75 + 0.5j, 1.5 + 0j],
]
_S_SMALL = [1.0 + 0.5j, -0.25 + 2j, 0.125 - 1j]


def _path_laplacian(n):
    rows = [[0.0] * n for _ in range(n)]
    for i in range(n):
        rows[i][i] = 2.0
        if i + 1 < n:
            rows[i][i + 1] = rows[i + 1][i] = -1.0
    rows[0][0] = rows[n - 1][n - 1] = 1.0
    return Mat.from_rows([[complex(x) for x in r] for r in rows],
                         is_complex=True)


def _rand_state(n, seed):
    rng = random.Random(seed)
    return [complex(rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(n)]


@pytest.mark.parametrize("n", [3, 4, 16, 32])
def test_decompose_matches_matvec_route_same_machine(n):
    """decompose == the rc218 mat_matvec composition on the SAME cached
    eigenbasis, byte-for-byte, on THIS machine + arm (kernel equality — both
    routes run the same contraction over the same bytes). NOT a
    cross-platform pin."""
    if n == 3:
        L = Mat.from_rows(_L_SMALL, is_complex=True)
        state = list(_S_SMALL)
    else:
        L = _path_laplacian(n)
        state = _rand_state(n, seed=n)
    handle = spectral.decompose(state, L)
    desc = _descriptor_hash(L)
    assert handle.substrate_descriptor_hash == desc
    _eigvals, V = _eigenbasis(L, desc)                 # the SAME cached basis
    coeffs_vec = mat_matvec(V.conj().T, [complex(x) for x in state])
    route_bytes = _complex128_bytes([complex(coeffs_vec[k]) for k in range(n)])
    assert handle.coefficients_bytes == route_bytes
    assert handle.content_sha == _sha256_hex(route_bytes)


@pytest.mark.parametrize("n", [3, 4, 16, 32])
def test_recompose_matches_matvec_route_same_machine(n):
    L = _path_laplacian(n) if n != 3 else Mat.from_rows(_L_SMALL,
                                                        is_complex=True)
    state = _rand_state(n, seed=100 + n) if n != 3 else list(_S_SMALL)
    handle = spectral.decompose(state, L)
    got = spectral.recompose(handle, L)
    _eigvals, V = _eigenbasis(L, handle.substrate_descriptor_hash)
    coeffs = _unpack_complex128(handle.coefficients_bytes, n)
    route = mat_matvec(V, coeffs)
    assert got == [complex(route[i]) for i in range(n)]


@pytest.mark.parametrize("n", [3, 8, 32])
def test_round_trip_within_tol(n):
    """recompose ∘ decompose ≈ identity within the numeric contract on the
    live arm — the float-eig content is NEVER pinned to a cross-platform
    SHA."""
    L = _path_laplacian(n) if n != 3 else Mat.from_rows(_L_SMALL,
                                                        is_complex=True)
    state = _rand_state(n, seed=7 * n) if n != 3 else list(_S_SMALL)
    back = spectral.recompose(spectral.decompose(state, L), L)
    worst = max(abs(complex(a) - complex(b)) for a, b in zip(back, state))
    assert worst <= _TOL, f"round-trip drift {worst:.3e} at n={n}"


@pytest.mark.parametrize("n", [3, 8])
def test_round_trip_within_tol_forced_pure(monkeypatch, n):
    """The forced-pure arm (HAS_NATIVE off — the rc219 peers AND the carrier
    kernels all decline): decompose/recompose still round-trip within tol.
    The eigenbasis LRU is cleared on BOTH sides — its key (the descriptor
    hash) is arm-independent, so a natively-minted basis would otherwise leak
    into the pure arm (and vice versa)."""
    L = _path_laplacian(n) if n != 3 else Mat.from_rows(_L_SMALL,
                                                        is_complex=True)
    state = _rand_state(n, seed=11 * n) if n != 3 else list(_S_SMALL)
    spectral.clear_eigenbasis_cache()
    try:
        with monkeypatch.context() as m:
            m.setattr(_native, "HAS_NATIVE", False)
            back = spectral.recompose(spectral.decompose(state, L), L)
        worst = max(abs(complex(a) - complex(b)) for a, b in zip(back, state))
        assert worst <= _TOL, f"pure round-trip drift {worst:.3e} at n={n}"
    finally:
        spectral.clear_eigenbasis_cache()      # no pure-eig leak to live tests


def test_descriptor_hash_fast_path_is_byte_identical():
    """The rc219 complex-buffer fast path == the struct-pack loop it replaced
    (the descriptor preimage is input bytes only — platform-stable)."""
    from srmech.amsc.format import sha256_bytes
    L = Mat.from_rows(_L_SMALL, is_complex=True)
    nr, nc = L.shape
    loop_bytes = _complex128_bytes(
        L[i, j] for i in range(nr) for j in range(nc))
    expected = sha256_bytes(loop_bytes + b"|" + b"default")
    assert _descriptor_hash(L) == expected
    # a real (non-complex) Mat still takes the loop path — same contract
    R = Mat.from_rows([[1.0, -1.0], [-1.0, 1.0]])
    loop_r = _complex128_bytes(R[i, j] for i in range(2) for j in range(2))
    assert _descriptor_hash(R) == sha256_bytes(loop_r + b"|" + b"default")


def test_descriptor_hash_memo_is_identity_keyed_and_value_stable():
    """The memo caches by carrier identity + encoder_tag and never changes
    the value: a fresh equal-valued Mat yields the SAME hex (so the memo is
    an optimization, not a semantic key), and distinct tags stay distinct."""
    a = Mat.from_rows(_L_SMALL, is_complex=True)
    b = Mat.from_rows(_L_SMALL, is_complex=True)
    h1 = _descriptor_hash(a)
    assert _descriptor_hash(a) == h1                  # memo hit
    assert _descriptor_hash(b) == h1                  # fresh carrier, same value
    assert getattr(a, "_srmech_desc_hash_memo")["default"] == h1
    assert _descriptor_hash(a, encoder_tag="raw") != h1


def test_decompose_handles_are_stable_across_repeat_calls():
    """Two decomposes of the same (state, L) — memo + eig cache + native path
    — give the same handle bytes (per-arm determinism)."""
    L = _path_laplacian(8)
    state = _rand_state(8, seed=3)
    h1 = spectral.decompose(state, L)
    h2 = spectral.decompose(state, L)
    assert h1.coefficients_bytes == h2.coefficients_bytes
    assert h1.content_sha == h2.content_sha
    assert h1.substrate_descriptor_hash == h2.substrate_descriptor_hash


def test_delta_predict_still_compose():
    """The downstream ops still ride the rc219 handles (sanity compose)."""
    L = _path_laplacian(6)
    s1 = _rand_state(6, seed=1)
    s2 = _rand_state(6, seed=2)
    h1 = spectral.decompose(s1, L)
    h2 = spectral.decompose(s2, L)
    d = spectral.delta(h1, h2)
    assert len(d) == len(h1.coefficients_bytes)
    p = spectral.predict(h1, L, steps=1)
    assert p.substrate_descriptor_hash == h1.substrate_descriptor_hash


def test_native_path_actually_dispatches(monkeypatch):
    """On a native host the wrappers genuinely reach the C kernels (not a
    silent pure fallback): sentinels on the ctypes symbols must fire."""
    if not (_native.HAS_NATIVE and _native.has_native_spectral_decompose()
            and _native.has_native_spectral_recompose()):
        pytest.skip("no native lib — pure-only host")
    hits = {"dec": 0, "rec": 0}
    real_dec = _native.LIB.srmech_spectral_decompose
    real_rec = _native.LIB.srmech_spectral_recompose

    def spy_dec(*args):
        hits["dec"] += 1
        return real_dec(*args)

    def spy_rec(*args):
        hits["rec"] += 1
        return real_rec(*args)

    with monkeypatch.context() as m:
        m.setattr(_native.LIB, "srmech_spectral_decompose", spy_dec)
        m.setattr(_native.LIB, "srmech_spectral_recompose", spy_rec)
        L = _path_laplacian(5)
        h = spectral.decompose(_rand_state(5, seed=9), L)
        spectral.recompose(h, L)
    assert hits["dec"] >= 1, "native decompose gate on but C never fired"
    assert hits["rec"] >= 1, "native recompose gate on but C never fired"


_LEDGER = Path(__file__).resolve().parent / "rosetta_classification.ndjson"


def test_rosetta_rows_are_c_dispatched():
    """The rc219 ledger move: decompose / recompose now carry their OWN C
    symbols → c_dispatched."""
    rows = {r["defined_at"]: r["bucket"]
            for r in (json.loads(line)
                      for line in _LEDGER.read_text(encoding="utf-8").splitlines()
                      if line.strip())}
    assert rows["srmech.spectral.decompose"] == "c_dispatched"
    assert rows["srmech.spectral.recompose"] == "c_dispatched"
