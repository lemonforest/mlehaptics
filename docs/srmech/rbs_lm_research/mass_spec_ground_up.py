"""mass_spec_ground_up.py — mass spec from the ground up (new research item, 2026-06-02).

A standard mass spectrum is a FLATTENED chart: m/z (scalar) vs intensity, peaks as
independent points. The framework reads it as a projection of a richer object whose
HIDDEN FIBER the flat chart drops:
  (1) the neutral-loss DIFFERENCE-GRAPH — which peaks are related by losing which
      neutral (the fragmentation relationships); every edge is mass-CONSERVING (the
      F278/F259 EC-code parity), so the graph is the conservation-relationship fiber;
  (2) the ISOTOPE envelope — the M+1/M+2 structure decoding elemental composition;
  (3) charge (folded into m/z) and the full directed fragmentation TREE.

This first pass builds, for a benign known compound (ethanol), the flat chart's peak
POSITIONS (from conservation) + surfaces fiber (1) the difference-graph (Class L) and
(2) the M+1 isotope decode (Class N / attested abundances).

NOW: peak positions + difference-graph + isotope decode (conservation side).
SOON: peak HEIGHTS (intensities) + the directed fragmentation TREE = the loop bind
  (k=7 order/tree/direction), gauge-gated on the srmech loop-bind op (#814).

SCOPE: framework-reading only; BENIGN known compound (ethanol); the m/z values are
textbook/illustrative EI-MS peaks; NO unknown-identification / detection / capability
-- only the information STRUCTURE of a spectrum (what the flat chart drops). CAD-ban
(graph/algebra, not 3D molecular geometry). Defensive scope; no-lineage (MS is the
field's; the projection/fiber reading is ours). Class-K clean.
"""
import numpy as np
from srmech.amsc import laplacian

# benign known compound: ethanol C2H6O (MW 46). Major EI-MS fragment m/z (textbook, illustrative).
COMPOUND = "ethanol  C2H6O  (MW 46)"
N_CARBON = 2
PEAKS = [46, 45, 31, 29, 27]          # the FLATTENED chart's peak positions (m/z)

# neutral losses (Δ mass -> the neutral fragment lost); each edge is mass-conserving (EC-code)
NEUTRALS = {1: "H", 2: "H2", 14: "CH2", 15: "CH3", 16: "O/CH4", 17: "OH",
            18: "H2O", 26: "C2H2", 28: "CO/C2H4", 29: "CHO/C2H5"}
C13 = 0.0107                          # 13C natural abundance (attested-B, IUPAC)


def difference_graph(peaks):
    """The hidden fiber: edges between peaks related by a known neutral loss (conservation)."""
    edges, labels = [], []
    for i in range(len(peaks)):
        for j in range(i + 1, len(peaks)):
            d = peaks[i] - peaks[j]                       # positive (peaks sorted desc-ish)
            d = d if d > 0 else -d                        # magnitude of the gap (a difference, not a sign-fold)
            if d in NEUTRALS:
                edges.append((i, j)); labels.append((peaks[i], peaks[j], d, NEUTRALS[d]))
    return edges, labels


def main():
    print(f"=== mass spec from the ground up: {COMPOUND} ===\n")

    # THE FLATTENED CHART (what mass spec currently gives) — peak positions only
    print("FLAT CHART (the projection): peaks at m/z =", PEAKS)
    print("  (heights/intensities = the fragmentation-probability model = the loop-bind mechanism, gauge-gated #814)\n")

    # FIBER 1 — the neutral-loss difference-graph (Class L)
    edges, labels = difference_graph(PEAKS)
    n = len(PEAKS)
    L = laplacian.dense_laplacian(n, edges)
    spec = laplacian.jacobi_eigvals(np.array(L, dtype=float))
    print(f"HIDDEN FIBER 1 — neutral-loss difference-graph ({len(edges)} edges the flat chart drops):")
    for hi, lo, d, name in labels:
        print(f"    {hi:>3} -> {lo:<3}   lose {name:<7} (Δ{d})")
    print(f"  graph Laplacian spectrum (the fiber's srmech-native signature, F172):")
    print(f"    {[round(float(x), 3) for x in sorted(spec)]}\n")

    # FIBER 2 — the isotope M+1 decode (composition fingerprint)
    m1_ratio = N_CARBON * C13
    print("HIDDEN FIBER 2 — isotope envelope (composition decode):")
    print(f"    M+1/M ≈ n_C × 1.07% = {N_CARBON} × {C13:.4f} = {m1_ratio:.4f}  ->  the M+1 peak DECODES {N_CARBON} carbons")
    print(f"    (the flat chart shows an M+1 peak but presents it as just-another-peak, not as a composition decode)\n")

    print("--- reading ---")
    print("  The flat chart = peaks as INDEPENDENT points. The fiber = the relationships:")
    print("  the difference-graph (which peak comes from which by losing what — mass-conserving,")
    print("  the F278/F259 EC-code) + the isotope decode (composition). 'Where to take MS next")
    print("  without losing data' = RETAIN the difference-graph + full isotope envelope (the fiber),")
    print("  rather than collapse to m/z-vs-intensity. The directed fragmentation TREE (the full")
    print("  fiber) is the loop bind, gauge-gated (#814).")


if __name__ == "__main__":
    main()
