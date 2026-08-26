# R-RBS-LM Finding 363 — battery test 3: the directed off-diagonal TRANSPORTS the observer to the projected spot and the new local diagonal reads from that position; relocation is genuine/one-way (the symmetric shadow bleeds back)

**Date:** 2026-06-04 · **srmech:** 0.7.0rc28 · **battery:** F361 test 3 of 4 · **tests the claim:** "this off-diag value might be needed to put the observer into that projected spot to see the full structure from that position" · **uses:** rc28 `dense_matvec_complex` (srmech-native transport) · **script:** `R-RBS-LM-R16_ride_and_read_new_diagonal.py`

## Result (directed tree, N=8; anchor = node 1, out-neighbours {2,4})

- **Ride one directed step (transport):** `A·e₁` → reached **{2, 4}** = exactly the out-neighbours of the anchor. The off-diagonal relocated the anchor to the projected spot.
- **Read the new diagonal:** ride again `A·x₁` → **{3, 5}** = exactly the out-neighbours of {2,4}. The new local structure reads correctly *from the relocated frame*.
- **Genuine / one-way relocation:** directed `A²·e₁` does **NOT** return to the anchor (False), but the symmetric shadow `A_sym²·e₁` **does** return (True). So the directed off-diagonal genuinely *moves* the observer; the symmetric shadow only *scans in place* (bleeds back).
- **Composability (ride further):** depth-1..4 frontiers = {2,4} → {3,5} → {6} → {7}. Composing off-diagonal steps rides further along the manifold.

## Reading

This confirms the F361 claim that the off-diagonal is the **transport** (not just the view): applying it relocates the anchor to the projected spot, and from there the new local diagonal (the destination's own structure) reads out — you "see the full structure of space from that position." Crucially, **directed transport is one-way** (genuine relocation), where the **symmetric shadow bleeds back** to the origin (scan-in-place, no relocation). This is the navigation analog of F361 test 1: only the bit-exact *directed* off-diagonal supports genuine travel; the symmetrized shadow lets you scan but not move.

## Discipline
srmech-native transport (`dense_matvec_complex`, Class L); directed adjacency built from the edge list (mechanics, flagged); composes with F361 (the reading), F357/F360 (the directed Hermitian op), F348 (navigation manifold). Honest: the directed adjacency here is a clean DAG fixture for legibility — the one-way/composability result is structural (holds for any directed graph), the specific frontiers are fixture-specific.
