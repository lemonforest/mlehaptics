"""TEMPORARY DIAGNOSTIC for #955 — REMOVE BEFORE MERGE.

rc337 bound the C catalog derive to the manifest head's COMMITTED ``body_sha256``.
That bound FIRES ON A CLEAN STORE on windows-latest only (22 tests), while ubuntu /
macOS / asserts-live are green. Windows is only reachable here through CI, so this
test prints the two digests plus the per-region breakdown for a clean genes store
and then FAILS ON PURPOSE, so the values land in the CI log.

It asserts nothing about correctness — it is an instrument, not a gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from srmech.amsc import _native
from srmech.amsc import genome as G


def _dump(tag, obj):
    print(f"[955] {tag}: {obj}", flush=True)


@pytest.mark.parametrize("with_genes", [False, True])
def test_diag_955_committed_vs_derived(tmp_path, with_genes):
    _dump("platform", sys.platform)
    _dump("has_native_genome", _native.has_native_genome())
    _dump("version", G.GENOME_FORMAT_VERSION)

    D = 64
    one = G._default_coupling(D)
    leaves = [G._HV.from_sequence(bytes((i + j) % 4 for i in range(D)), sectors=G.QUAD)
              for j in range(3)]
    if with_genes:
        strand = G.chromosome(leaves, one, label="chrA", genes=[("g1", 1), ("g2", 2)])
    else:
        strand = G.chromosome(leaves, one, label="chrA")

    p = tmp_path / "g"
    saved = G.genome_save(strand, p, coupling=one)
    body = (p / "turns.bin").read_bytes()
    _dump("body_len", len(body))
    _dump("saved.body_sha256", saved.get("body_sha256"))

    # what is actually ON DISK in the head
    head = json.loads((p / "manifest.json").read_text(encoding="utf-8"))
    hdata = head.get("data", head)
    _dump("head.keys", sorted(hdata.keys()))
    _dump("head.committed_body_sha256", hdata.get("body_sha256"))
    _dump("head.has_chromosomes_array", "chromosomes" in hdata)
    _dump("head.n_chromosomes", hdata.get("n_chromosomes"))
    _dump("head.n_turns", hdata.get("n_turns"))

    # the PURE re-derivation (the C peer of this is what rc337 binds)
    try:
        pure = G._catalog_data(p, one)
        _dump("pure_derived.body_sha256", pure.get("body_sha256"))
        _dump("pure_derived.n_turns", pure.get("n_turns"))
        _dump("pure_derived.n_chrom", len(pure.get("chromosomes", [])))
        for c in pure.get("chromosomes", []):
            _dump("pure_region", {k: c.get(k) for k in
                                  ("label", "byte_offset", "byte_len", "leaf_count", "cap_sha256")})
        for i, r in enumerate(pure.get("regions", []) or []):
            _dump(f"pure_regions[{i}]", r)
        _dump("MATCH pure_derived == committed",
              pure.get("body_sha256") == hdata.get("body_sha256"))
    except Exception as exc:            # noqa: BLE001 - diagnostic
        _dump("pure_derive_RAISED", f"{type(exc).__name__}: {exc}")

    # the NATIVE derive (this is the one that fires on windows)
    try:
        nat = G._canonical_catalog(p, one)
        _dump("native_derived.body_sha256", nat.get("body_sha256"))
        _dump("MATCH native_derived == committed",
              nat.get("body_sha256") == hdata.get("body_sha256"))
    except Exception as exc:            # noqa: BLE001 - diagnostic
        _dump("native_derive_RAISED", f"{type(exc).__name__}: {exc}")

    # and the op that actually failed on windows
    try:
        G.genome_append(p, "chrB", leaves, one)
        _dump("append", "ok")
        G.genome_remove(p, "chrB", coupling=one)
        _dump("remove", "ok")
    except Exception as exc:            # noqa: BLE001 - diagnostic
        _dump("mutation_RAISED", f"{type(exc).__name__}: {exc}")

    pytest.fail("[955] diagnostic — see the [955] lines above (this failure is intentional)")
