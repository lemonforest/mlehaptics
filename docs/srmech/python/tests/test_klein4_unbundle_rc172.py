"""rc172 — klein4_unbundle: recover a bound value from a bundle (the dual of bundle).

The per-class reversibility audit (srmech_research_notebook.md §3.27 audit) used to
mark Class M (HDC) bundle as "irreversible — no unbundle, similarity-query only."
That was wrong: bundle's dual is unbundle = unbind-on-the-bundle + similarity
cleanup, recoverable "because the bundle keeps the relationship". These tests pin
the three facts that overturn the old claim.

numpy-free ([[feedback_test_for_numpy_free_module_must_itself_be_numpy_free]]).
"""

from array import array

from srmech.amsc import hdc


def _codes(seed, n):
    return array("B", [((i * seed + 1013904223) >> 5) & 3 for i in range(n)])


def test_single_pair_is_exact():
    """unbundle(bind(k, v), k) == v exactly — the XOR self-inverse, no cleanup."""
    for D in (1, 7, 64, 1000):
        k = _codes(7, D)
        v = _codes(13, D)
        bound = hdc.klein4_bind(k, v)
        rec = hdc.klein4_unbundle(bound, k)
        assert list(rec.buffer) == list(v), f"single-pair recall not exact at D={D}"


def test_unbundle_is_bind_back():
    """unbundle(S, key) == bind(S, key) == unbind(S, key) — the composition identity."""
    S = _codes(3, 256)
    key = _codes(29, 256)
    assert list(hdc.klein4_unbundle(S, key).buffer) == list(hdc.klein4_bind(S, key).buffer)
    assert list(hdc.klein4_unbundle(S, key).buffer) == list(hdc.klein4_unbind(S, key).buffer)


def test_multi_pair_record_recall():
    """A record bundles bound key→value pairs; unbundle by key + similarity-cleanup
    against the value codebook recovers the correct value (recoverable up to HDC
    capacity — the dual of bundle is unbundle + cleanup, NOT a blind query)."""
    D = 512
    keys = [_codes(s, D) for s in (11, 17, 23)]
    vals = [_codes(s, D) for s in (101, 211, 307)]
    record = hdc.klein4_bundle(*[hdc.klein4_bind(k, v) for k, v in zip(keys, vals)])
    for qi, key in enumerate(keys):
        recovered = hdc.klein4_unbundle(record, key)
        sims = [hdc.klein4_similarity(recovered, v) for v in vals]
        best = max(range(len(vals)), key=lambda j: sims[j])
        assert best == qi, (
            f"recall for key {qi} picked value {best}; sims={[round(s, 3) for s in sims]}")
        # the correct value scores strictly above the foils (above-chance recall)
        assert sims[qi] > max(s for j, s in enumerate(sims) if j != qi)
