"""§49 (rc153): native-vs-pure-Python differential for the genome file-management
dispatch.

The C library ships all 11 ``srmech_genome_*`` symbols (the §41/§43/§44/§45 mirror);
rc153 binds them in ``srmech.amsc._native`` and routes ``srmech.amsc.genome`` through
them when ``HAS_NATIVE`` (the §38 / F708 treatment, genome family). The native path is a
PURE ACCELERATOR — it writes ``turns.bin`` + ``manifest.json`` (and the ``.chr`` bundles)
byte-for-byte identically to the pure-Python path, falling back on ANY native error.

This test PROVES the dispatch is byte-faithful: for every public genome op it runs the
op once with native ON (the real C surface) and once with native forced OFF (pure
Python), and asserts the on-disk strand + manifest are byte-identical AND the returns
match. It SKIPS when the native genome surface is not built (a pure-wheel / numpy-absent
dev tree), where ``has_native_genome()`` is False and there is nothing to differentiate;
the CI test-matrix cells build the native lib (``pip install -e``) so it runs there.

numpy-free per the module's discipline (no numpy import, no ``np.``).
"""
import json
import tempfile
from pathlib import Path

import pytest

import srmech.amsc._native as _native
from srmech.amsc import genome as G
from srmech.amsc.hdc import klein4_random

pytestmark = pytest.mark.skipif(
    not _native.has_native_genome(),
    reason="native genome C surface not built (HAS_NATIVE / srmech_genome_save absent)",
)

DIM = 16


def _one(seed=7):
    return klein4_random(DIM, seed=seed)


def _specs(labels_seeds):
    return [(lbl, [(lbl[0], [klein4_random(DIM, seed=s) for s in seeds])])
            for lbl, seeds in labels_seeds]


class _force_pure:
    """Context manager: force ``genome.py`` onto the pure-Python path by making
    ``_native.has_native_genome()`` read False (genome.py calls it at dispatch time)."""

    def __enter__(self):
        self._orig = _native.has_native_genome
        _native.has_native_genome = lambda: False
        return self

    def __exit__(self, *exc):
        _native.has_native_genome = self._orig
        return False


def _tmp():
    return tempfile.mkdtemp()


def _disk(d):
    d = Path(d)
    return ((d / "turns.bin").read_bytes(), (d / "manifest.json").read_bytes())


def _save(d, labels_seeds, one):
    return G.genome_save(G.genome(chromosomes=_specs(labels_seeds), the_one=one),
                         d, the_one=one)


def _blocks(strand):
    """Byte-blocks of an HV strand — exact element-wise compare independent of HV ==."""
    return G._leaf_blocks(list(strand))


def test_save_byte_identical():
    one = _one()
    nat, pur = _tmp(), _tmp()
    r_nat = _save(nat, [("alpha", (1, 2)), ("beta", (3,)), ("gamma", (4, 5, 6))], one)
    with _force_pure():
        r_pur = _save(pur, [("alpha", (1, 2)), ("beta", (3,)), ("gamma", (4, 5, 6))], one)
    assert _disk(nat) == _disk(pur)          # turns.bin + manifest.json byte-for-byte
    assert r_nat == r_pur                     # returned manifest data dict


def test_catalog_matches():
    one = _one()
    d = _tmp()
    _save(d, [("alpha", (1, 2)), ("beta", (3,))], one)
    nat = G.genome_catalog(d, the_one=one)
    with _force_pure():
        pur = G.genome_catalog(d, the_one=one)
    assert nat == pur


def test_load_matches():
    one = _one()
    d = _tmp()
    _save(d, [("alpha", (1, 2)), ("beta", (3,)), ("gamma", (4,))], one)
    s_nat, o_nat, l_nat = G.genome_load(d, the_one=one)
    with _force_pure():
        s_pur, o_pur, l_pur = G.genome_load(d, the_one=one)
    assert l_nat == l_pur
    assert _blocks(s_nat) == _blocks(s_pur)
    assert _blocks([o_nat]) == _blocks([o_pur])


def test_window_matches():
    one = _one()
    d = _tmp()
    _save(d, [("alpha", (1, 2)), ("beta", (3, 4))], one)
    nat = G.genome_window(d, "beta", the_one=one)
    with _force_pure():
        pur = G.genome_window(d, "beta", the_one=one)
    assert _blocks(nat) == _blocks(pur)


def test_append_byte_identical():
    one = _one()
    nat, pur = _tmp(), _tmp()
    _save(nat, [("alpha", (1,))], one)
    _save(pur, [("alpha", (1,))], one)
    new = [klein4_random(DIM, seed=s) for s in (8, 9)]
    r_nat = G.genome_append(nat, "beta", new, one)
    with _force_pure():
        r_pur = G.genome_append(pur, "beta", new, one)
    assert _disk(nat) == _disk(pur)
    assert r_nat == r_pur


def test_remove_byte_identical():
    one = _one()
    nat, pur = _tmp(), _tmp()
    _save(nat, [("alpha", (1,)), ("beta", (2,)), ("gamma", (3,))], one)
    _save(pur, [("alpha", (1,)), ("beta", (2,)), ("gamma", (3,))], one)
    r_nat = G.genome_remove(nat, "beta", the_one=one)
    with _force_pure():
        r_pur = G.genome_remove(pur, "beta", the_one=one)
    assert _disk(nat) == _disk(pur)
    assert r_nat == r_pur


def test_replace_byte_identical():
    one = _one()
    nat, pur = _tmp(), _tmp()
    _save(nat, [("alpha", (1,)), ("beta", (2,))], one)
    _save(pur, [("alpha", (1,)), ("beta", (2,))], one)
    new = [klein4_random(DIM, seed=s) for s in (7, 8, 9)]
    r_nat = G.genome_replace(nat, "alpha", new, one)
    with _force_pure():
        r_pur = G.genome_replace(pur, "alpha", new, one)
    assert _disk(nat) == _disk(pur)
    assert r_nat == r_pur


def test_export_byte_identical():
    one = _one()
    d = _tmp()
    _save(d, [("alpha", (1, 2)), ("beta", (3,))], one)
    nat_chr = Path(_tmp()) / "n.chr"
    pur_chr = Path(_tmp()) / "p.chr"
    r_nat = G.genome_export(d, "alpha", nat_chr, the_one=one)
    with _force_pure():
        r_pur = G.genome_export(d, "alpha", pur_chr, the_one=one)
    assert nat_chr.read_bytes() == pur_chr.read_bytes()
    assert r_nat == r_pur


def test_import_byte_identical():
    one = _one()
    src = _tmp()
    _save(src, [("alpha", (1, 2))], one)
    chr_path = Path(_tmp()) / "alpha.chr"
    G.genome_export(src, "alpha", chr_path, the_one=one)
    nat, pur = _tmp(), _tmp()                 # existing (mkdtemp) dirs → native SEED fires
    r_nat = G.genome_import(chr_path, nat, the_one=one)
    with _force_pure():
        r_pur = G.genome_import(chr_path, pur, the_one=one)
    assert _disk(nat) == _disk(pur)
    assert r_nat == r_pur


def test_explode_byte_identical():
    one = _one()
    d = _tmp()
    _save(d, [("alpha", (1, 2)), ("beta", (3,)), ("gamma", (4, 5))], one)
    nat, pur = _tmp(), _tmp()
    r_nat = G.genome_explode(d, nat, the_one=one)
    with _force_pure():
        r_pur = G.genome_explode(d, pur, the_one=one)
    # each loose <label>.chr byte-identical + the returned descriptor list matches
    # (paths differ by out-dir; compare label + region hash).
    for label in ("alpha", "beta", "gamma"):
        assert (Path(nat) / f"{label}.chr").read_bytes() == \
               (Path(pur) / f"{label}.chr").read_bytes()
    strip = lambda rows: [{"label": r["label"], "region_sha256": r["region_sha256"]}
                          for r in rows]
    assert strip(r_nat) == strip(r_pur)


def test_pack_byte_identical():
    one = _one()
    src = _tmp()
    _save(src, [("gamma", (4,)), ("alpha", (1, 2)), ("beta", (3,))], one)
    loose = _tmp()
    G.genome_explode(src, loose, the_one=one)
    nat, pur = _tmp(), _tmp()
    r_nat = G.genome_pack(loose, nat, the_one=one)
    with _force_pure():
        r_pur = G.genome_pack(loose, pur, the_one=one)
    assert _disk(nat) == _disk(pur)           # re-canonicalised to sorted-label order
    assert r_nat == r_pur
