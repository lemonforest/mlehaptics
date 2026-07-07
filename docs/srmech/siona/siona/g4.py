"""siona.g4 — selective, AUTOMATIC G4 chirality-stabilization (F1153).

Biology stabilizes G-quadruplex (G4) — a 4-strand higher-order fold — SELECTIVELY on an otherwise double-helix
chromosome: at sequence-predictable G-rich MOTIFS, folding/unfolding AUTOMATICALLY (the motif + local conditions
decide; helicases unfold on demand). No manual placement.

We do the same. On our otherwise-flat / bit-exact (double-helix) encoding, chiral collapse is LOSSY only at the
~4% metamer loci (F1152) — a CO-PRESENT ANTONYM PAIR, where flattening the chirality confuses two present
opposites. So:

- the **G4 MOTIF** = the metamer (Class-C `opposite` co-presence) — content-derived, AUTOMATIC, like the G-rich
  sequence motif; `g4_motif` scans for it, no manual placement;
- the **G4 FOLD** = encode that locus with the full-chirality KLEIN-4 (the 4 sectors, F132/F1138) — assign the two
  poles to DIFFERENT sectors (`chirality.structural_poles`), so the flat-collapsed metamer becomes distinguishable
  (the which-way preserved);
- the **UNFOLD** = the ~96% with no motif stay FLAT (bit-exact double-helix) — no fold, no cost.

`g4_stabilize` runs the whole automatic pass over a story: scan every phrase-cycle, fold the G4 loci, leave the
rest flat — the automatic per-scale chirality firing (F1151) the bit-exact silicon substrate otherwise flattens.

Sparse, numpy-free. Klein-4 sector assignment via the srmech Class-L signed Laplacian (`chirality.structural_poles`).
"""
from siona import anchor, chirality

__all__ = ["g4_motif", "g4_fold", "g4_stabilize", "has_g4"]


def g4_motif(concepts):
    """The automatic G4-locus detector: a phrase-cycle carries a G4 motif iff it contains a CO-PRESENT ANTONYM
    PAIR (a metamer — flat chiral collapse would confuse them). Returns the metamer ``(a, b)`` pairs (the loci to
    fold). Content-derived (Class-C `opposite` co-presence), like biology's G-rich sequence motif — AUTOMATIC, no
    manual placement, no everywhere-cost."""
    ws = [w.lower() for c in concepts for w in c.replace("to ", "").split() if w]
    seen = list(dict.fromkeys(ws))
    pairs = []
    for i, a in enumerate(seen):
        for b in seen[i + 1:]:
            if chirality.opposite(a, b):
                pairs.append((a, b))
    return pairs


def g4_fold(concepts):
    """FOLD the full-chirality Klein-4 at a cycle's G4 loci (F1153): assign the metamer poles to DIFFERENT Klein-4
    sectors (the chirality bit) via `chirality.structural_poles` (the Class-L signed-Laplacian partition, F1138) —
    so the flat-collapsed metamer becomes distinguishable, the which-way preserved. Returns ``{word: sector 0|1}``
    for the folded (chirality-preserved) words, or ``{}`` if the cycle has no motif (stays flat). SELECTIVE: only
    a metamer cycle folds; the full Klein-4 carrier (`srmech.amsc.hdc.klein4_bind` on the sector key) realizes it
    in HDC, the sector bit here IS the load-bearing chirality (F132)."""
    motif = g4_motif(concepts)
    if not motif:
        return {}                                       # no G4 locus → the double-helix stays flat (no fold, no cost)
    field = sorted({w for pair in motif for w in pair})
    poles = chirality.structural_poles(field)           # Klein-4 sector (0/1) from the signed Laplacian
    if not poles:                                        # <3 field words → fall back to the direct pole split
        a, b = motif[0]
        poles = {a: 0, b: 1}
    return poles


def g4_stabilize(glyph_lines):
    """The AUTOMATIC selective-G4 pass over a story (F1153): scan every phrase-cycle, FOLD the G4-motif loci
    (Klein-4 sector-assign the metamer poles), leave the rest FLAT. Returns ``(folded, total)`` — a list of
    ``(line_idx, cycle_idx, {word: sector})`` for the folded loci, and the total cycle count. This is the
    automatic per-scale chirality firing: the motif (content) decides where to fold, no manual placement."""
    folded, total = [], 0
    for li, gl in enumerate(glyph_lines):
        cs = [c for c in anchor.transcribe([gl])[0] if c]
        for ci, cy in enumerate(anchor._phrase_cycles(cs)):
            total += 1
            f = g4_fold(cy)
            if f:
                folded.append((li, ci, f))
    return folded, total


def has_g4():
    return chirality.have_axis()
