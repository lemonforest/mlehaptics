"""test_native_parity — the [profile.native] scaffold proof.

Asserts the whole chain works end-to-end:
  1. libsiona_native.so loads (siona._native.HAS_NATIVE) with the ABI handshake.
  2. The native op == the validated pure-Python reference, bit-for-bit, over
     many inputs (the has_native dispatch is value-identical either way).
  3. srmech's profile_loader picks the SAME lib up as srmech.profile("siona").native
     (a "plugin"-kind Profile, not "simple").

Skips gracefully (not fails) when the .so is absent — a pure-Python-only install
(Pyodide/WASM or a source checkout with no `make -C c`) is a supported mode.
"""
import pytest

from siona import _native


def test_native_loaded_or_skipped():
    if not _native.HAS_NATIVE:
        pytest.skip(f"libsiona_native.so absent (pure-Python mode): {_native.LOAD_ERROR}")
    st = _native.native_status()
    assert st["has_native"] is True
    assert st["abi_version"] == _native.EXPECTED_ABI_VERSION
    assert st["library_path"] is not None


@pytest.mark.parametrize("data", [
    b"", b"a", b"srmech", b"the quick brown fox",
    b"\x00\x01\x02\xff", bytes(range(256)), b"x" * 4096,
    "σ_OC ≠ σ_SC".encode("utf-8"), "café — naïve".encode("utf-8"),
])
def test_fnv1a64_parity(data):
    """native == pure-Python reference, bit-for-bit."""
    py = _native._fnv1a64_py(data)
    got = _native.fnv1a64(data)               # dispatches native when present
    assert got == py, f"dispatch != reference for {data!r}"
    if _native.HAS_NATIVE:
        assert int(_native._LIB.siona_native_fnv1a64(data, len(data))) == py


def test_fnv1a64_known_vector():
    """Anchor to the published FNV-1a-64 test vector (de-magics the constant)."""
    # FNV-1a-64("") = the offset basis; FNV-1a-64("a") is the canonical first step.
    assert _native.fnv1a64(b"") == 14695981039346656037
    assert _native.fnv1a64(b"a") == 12638187200555641996


def test_profile_native_surface():
    """srmech's profile_loader loads the SAME .so as Profile.native (plugin tier)."""
    srmech = pytest.importorskip("srmech")
    if not _native.HAS_NATIVE:
        pytest.skip("native absent; profile loads as simple-tier")
    prof = srmech.profile("siona")
    assert prof.native is not None, "profile did not load the native plugin"
    assert "plugin" in repr(prof)
    # every declared symbol is bound
    for sym in ("siona_native_fnv1a64", "siona_native_tokenize",
                "siona_native_cooccurrence_accumulate", "siona_native_arena_compact",
                "siona_native_cooccurrence_laplacian"):
        assert hasattr(prof.native, sym), f"missing {sym}"


# ── tokenize (byte-scan word boundaries; native == pure-Python) ─────────
@pytest.mark.parametrize("s", [
    b"", b"the Quick brown fox", b"klein4 sha256  E=mc^2", b"a.b,c;d!e?f",
    b"   spaced   out   ", "café σ_OC ≠ σ_SC".encode("utf-8"),
])
def test_tokenize_spans_parity(s):
    assert _native.tokenize_spans(s) == _native._tokenize_spans_py(s)


def test_tokenize_strings():
    assert _native.tokenize("The CAT sat") == ["the", "cat", "sat"]
    assert _native.tokenize("klein4 sha256") == ["klein4", "sha256"]


# ── windowed co-occurrence (native == pure-Python, order-independent) ────
def test_cooccurrence_parity_dicts():
    import random
    rng = random.Random(99)
    for _ in range(200):
        docs = [[rng.randint(0, 40) for _ in range(rng.randint(0, 15))]
                for _ in range(rng.randint(1, 4))]
        tids, dends = _native.flatten_docs(docs)
        w = rng.randint(1, 4)
        py = _native._cooccurrence_counts_py(tids, dends, w)
        # parallel form
        ii, jj, ww = _native.cooccurrence_edges_parallel(tids, dends, w)
        got = {(ii[k], jj[k]): ww[k] for k in range(len(ii))}
        assert got == py
        # tuple form
        edges, weights = _native.cooccurrence_edges(tids, dends, w)
        assert dict(zip(edges, weights)) == py


def test_cooccurrence_known_example():
    docs = [[0, 1, 0], [0, 1]]  # "a b a" ; "a b"  (0=a, 1=b)
    tids, dends = _native.flatten_docs(docs)
    ii, jj, ww = _native.cooccurrence_edges_parallel(tids, dends, window=2)
    got = {(i, j): w for i, j, w in zip(ii, jj, ww)}
    assert got == {(0, 1): 3}  # doc1: (a,b),(b,a)->(0,1)x2 ; doc2: (a,b)x1


# ── fused tokens -> subset Laplacian (P1); native Mat == composed dense_laplacian ──
def test_cooccurrence_laplacian_parity():
    """The fused native Laplacian == cooccurrence_edges + dense_laplacian, bit-for-bit,
    and the eigen-spectrum is identical."""
    pytest.importorskip("srmech")
    from srmech.amsc import laplacian as L
    import random
    if not _native.HAS_NATIVE:
        pytest.skip("native absent; fused path is the pure-Python compose fallback")
    rng = random.Random(5)
    for _ in range(150):
        V = rng.randint(5, 60)
        docs = [[rng.randint(0, V) for _ in range(rng.randint(0, 20))]
                for _ in range(rng.randint(1, 4))]
        tids, dends = _native.flatten_docs(docs)
        allids = list(range(V + 1))
        rng.shuffle(allids)
        subset = allids[:rng.randint(1, min(V + 1, 12))]
        w = rng.randint(1, 4)
        fused = _native.cooccurrence_laplacian(tids, dends, subset, window=w)
        _native.HAS_NATIVE = False
        try:
            ref = _native.cooccurrence_laplacian(tids, dends, subset, window=w)
        finally:
            _native.HAS_NATIVE = True
        assert list(fused._buf) == list(ref._buf)          # bit-for-bit Laplacian
        assert list(L.symmetric_eigendecompose(fused)[0]) == \
               list(L.symmetric_eigendecompose(ref)[0])    # identical spectrum
