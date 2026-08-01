"""§102 G7 (rc329) — BYTE-PARITY between the two coherency projections of the two
genome LEAF-family wire-glue ops that earned whole-op C peers this rc:

  * ``genome.active_telomere`` -> ``srmech_genome_active_telomere`` — the op⊗operand
    §127 Hayflick cap PACKER (marker + label + NUL + count(uint64 BE), NUL-padded),
    factored out of ``srmech_genome_telomere_tick`` so a bare-C host builds ONE active
    cap with NO daughter-minting.
  * ``genome.mint_plan`` -> ``srmech_genome_mint_plan`` — the read-only introspection
    loop that BUILDS NOTHING: per kernel the F715 shape decision (encode_shape ->
    plasmid vs nuclear) and, for a nuclear kernel, its content-addressed orientation
    (sha256(content)[0] & 3). The per-step primitive was already native; the loop that
    assembles the plan was the gap.

ADR-0009: the capability is the invariant; neither implementation is primary. So the
test is NOT "does C agree with Python" — it is "do the two projections emit the SAME
result". The native whole-op peer runs the WHOLE op in C; the pure body (forced here by
disabling the native surface) is the byte-parity ORACLE.

Both closures move ``_KNOWN_GLUE_GAPS -> _WHOLE_OP_C_PEER`` and drop
``CEIL_WIRE_GLUE_GAPS`` 8 -> 6 in test_rosetta_transitive_standalone.py; this file pins
the byte-parity AND that each peer is both DECLARED in the whole-op map and actually
DISPATCHED (not merely present in the lib).
"""
import pytest

from srmech.amsc import _native
from srmech.biology import genome


# ---------------------------------------------------------------------------
# active_telomere — srmech_genome_active_telomere
# ---------------------------------------------------------------------------

_at_native = pytest.mark.skipif(
    not _native.has_native_genome_active_telomere(),
    reason="rc329 native srmech_genome_active_telomere not built into this lib",
)


def _active_bytes(hv):
    return hv.tobytes()


@_at_native
@pytest.mark.parametrize("label,count,dim", [
    ("chr1", 50, 64),
    ("", 0, 64),                       # empty label
    ("chr1", 0, 64),                   # count 0 (senescent-at-birth)
    ("chrX", 2 ** 63, 128),            # a high bit of the uint64 field set
    ("chrY", (1 << 64) - 1, 96),       # the max uint64 count
    ("t", 1, 52),                      # the minimum §89 leaf_dim
    ("a" * 50, 7, 64),                 # a label that fills the cap to the field
    ("longlabelhere", 99999, 96),
    ("mtDNA", 16569, 200),
])
def test_active_telomere_byte_parity(monkeypatch, label, count, dim):
    """native == forced-pure, byte for byte."""
    nat = genome.active_telomere(label, count, dim)
    assert _native.has_native_genome_active_telomere()
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        assert not _native.has_native_genome_active_telomere()
        pur = genome.active_telomere(label, count, dim)
    assert _active_bytes(nat) == _active_bytes(pur), (
        f"active_telomere({label!r}, {count}, {dim}): strand bytes diverge")
    # the packed cap is self-describing — the count + label read back exactly
    assert genome._active_telomere_count(nat) == count
    assert genome._active_telomere_label(nat) == label
    # and it ticks like a tick-minted cap (the pack is the tick's inverse-in-spirit)
    senescent, after, _ = _native.genome_telomere_tick_c(nat.tobytes(), dim)
    assert senescent == (count == 0)
    assert after == (0 if count == 0 else count - 1)


@_at_native
@pytest.mark.parametrize("label,count,dim", [
    ("x" * 80, 1, 64),                 # label + field over leaf_dim
    ("a\x00b", 1, 64),                 # a NUL inside the label
    ("c", -1, 64),                     # a negative count (never signed)
    ("c", 1 << 64, 64),                # count past the uint64 field
])
def test_active_telomere_error_parity(monkeypatch, label, count, dim):
    """The C peer DECLINES exactly where the pure body RAISES — the caller falls back
    to the pure path, which raises the same ValueError, native or not."""
    with pytest.raises(ValueError):
        genome.active_telomere(label, count, dim)
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        with pytest.raises(ValueError):
            genome.active_telomere(label, count, dim)


# ---------------------------------------------------------------------------
# mint_plan — srmech_genome_mint_plan
# ---------------------------------------------------------------------------

_mp_native = pytest.mark.skipif(
    not _native.has_native_genome_mint_plan(),
    reason="rc329 native srmech_genome_mint_plan not built into this lib",
)


def _leaf(dim=64, seed=0):
    """A Klein-4 data leaf (bytes 0..3), dim wide."""
    return genome._HV.from_sequence(
        [(seed + i) % 4 for i in range(dim)], sectors=genome.QUAD)


def _kernels(spec, dim=64):
    """Build a ``{label: leaves}`` mapping from a ``{label: n_leaves}`` spec."""
    return {lbl: [_leaf(dim, seed=lbl_i * 3 + j) for j in range(n)]
            for lbl_i, (lbl, n) in enumerate(spec.items())}


_MINT_CASES = {
    "empty": {},
    "one_plasmid": {"p": 1},
    "one_nuclear": {"n": 6},
    "zero_leaf": {"z": 0},             # 0 leaves -> tome -> plasmid
    "boundary_4": {"four": 4},         # <= 4 leaves stays plasmid
    "boundary_5": {"five": 5},         # >= 5 leaves -> quad_strand -> nuclear
    "mixed": {"p1": 1, "n1": 9, "p2": 2, "n2": 5},
    "many": {f"k{i}": (i % 8) for i in range(12)},
}


@_mp_native
@pytest.mark.parametrize("tag", sorted(_MINT_CASES))
def test_mint_plan_byte_parity_dict(monkeypatch, tag):
    kernels = _kernels(_MINT_CASES[tag])
    nat = genome.mint_plan(kernels)
    assert _native.has_native_genome_mint_plan()
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        assert not _native.has_native_genome_mint_plan()
        pur = genome.mint_plan(kernels)
    assert nat == pur, f"mint_plan[{tag}]: plan diverges"


@_mp_native
def test_mint_plan_byte_parity_list_form(monkeypatch):
    """The ``(label, leaves)`` sequence input form (not just the dict form)."""
    items = [("a", [_leaf(seed=1)]),
             ("b", [_leaf(seed=i) for i in range(7)]),
             ("c", [_leaf(seed=i) for i in range(5)])]
    nat = genome.mint_plan(items)
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        pur = genome.mint_plan(items)
    assert nat == pur


@_mp_native
def test_mint_plan_orientation_int_not_none_for_nuclear(monkeypatch):
    """A nuclear kernel carries an INTEGER orientation (0..3, possibly 0 — the 0-vs-None
    edge case), a plasmid carries None; native and pure agree on both."""
    kernels = {"five": [_leaf(seed=i) for i in range(5)],   # nuclear
               "one": [_leaf(seed=99)]}                     # plasmid
    nat = genome.mint_plan(kernels)
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        pur = genome.mint_plan(kernels)
    assert nat == pur
    assert nat[0]["shape"] == "nuclear" and nat[0]["centromere"] is True
    assert isinstance(nat[0]["orientation"], int) and nat[0]["orientation"] in (0, 1, 2, 3)
    assert nat[1]["shape"] == "plasmid" and nat[1]["orientation"] is None


@_mp_native
def test_mint_plan_wide_leaf_dim_parity(monkeypatch):
    """A non-default leaf width still content-addresses identically native vs pure."""
    kernels = _kernels({"p": 3, "n": 8}, dim=128)
    nat = genome.mint_plan(kernels)
    with monkeypatch.context() as m:
        m.setattr(_native, "HAS_NATIVE", False)
        pur = genome.mint_plan(kernels)
    assert nat == pur


# ---------------------------------------------------------------------------
# ratchet coherence — both peers are DECLARED whole-op AND actually DISPATCHED
# ---------------------------------------------------------------------------

def _load_rosetta():
    """Load the sibling rosetta ratchet module by file path (robust to pytest's
    per-invocation sys.path — the module is not always importable by bare name)."""
    import importlib.util
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "test_rosetta_transitive_standalone.py")
    spec = importlib.util.spec_from_file_location("_rosetta_rc329", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_rc329_peers_declared_whole_op():
    """The two rc329 ops left ``_KNOWN_GLUE_GAPS`` for ``_WHOLE_OP_C_PEER`` — assert the map
    names the right symbol and that neither is still a gap. (The full transitive ratchet — and
    the DOWN-ONLY ``CEIL_WIRE_GLUE_GAPS`` pin, which later rcs keep lowering — lives in
    test_rosetta_transitive_standalone.py; this is a local coherence pin for THESE ops only, so
    it does NOT re-pin the global ceiling to its rc329-era value.)"""
    rosetta = _load_rosetta()
    assert rosetta._WHOLE_OP_C_PEER["srmech.biology.genome.active_telomere"] == \
        "srmech_genome_active_telomere"
    assert rosetta._WHOLE_OP_C_PEER["srmech.biology.genome.mint_plan"] == \
        "srmech_genome_mint_plan"
    assert "srmech.biology.genome.active_telomere" not in rosetta._KNOWN_GLUE_GAPS
    assert "srmech.biology.genome.mint_plan" not in rosetta._KNOWN_GLUE_GAPS
    assert len(rosetta._KNOWN_GLUE_GAPS) == rosetta.CEIL_WIRE_GLUE_GAPS


def test_rc329_peers_actually_dispatched():
    """A declaration proves nothing (the rc273 failure mode) — assert the op truly
    REACHES its C peer when the lib carries it."""
    if _native.has_native_genome_active_telomere():
        peer = _native.genome_active_telomere_c("chr", 3, 64)
        assert peer is not None
        assert peer == genome.active_telomere("chr", 3, 64).tobytes()
    if _native.has_native_genome_mint_plan():
        assert _native.genome_mint_plan_c([b"", b"\x00" * (6 * 64)], [0, 6]) is not None
