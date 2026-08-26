# F279 — mass spec from the ground up: the flat chart (m/z vs intensity) is a projection; the hidden fiber is the neutral-loss difference-graph + the isotope-composition decode (+ the gauge-gated fragmentation tree)

**Headline:** A standard mass spectrum is a **flattened chart** — m/z (scalar) vs intensity, peaks as independent points. The framework reads it as a projection of a richer object whose **hidden fiber** the flat chart drops: (1) the **neutral-loss difference-graph** — which peaks come from which by losing which neutral, every edge **mass-conserving** (the F278/F259 EC-code parity); (2) the **isotope envelope** decoding elemental composition; (3) charge (folded into m/z); (4) the full directed **fragmentation tree**. First pass (benign known compound, ethanol C₂H₆O): the flat chart `[46,45,31,29,27]` hides an **8-edge difference-graph** (Laplacian signature `[0,2,4,5,5]`) and an **M+1 → 2-carbon** isotope decode. Same **now/soon** split as F278: positions + difference-graph + isotopes are reachable **now** (Class L/N/I + the EC-code); peak **heights** + the directed **fragmentation tree** are the **loop bind** (k=7), gauge-gated (#814). Single-model; srmech v0.6.0rc20.

*User direction (2026-06-02): "mass spec from ground up … work it from the ground up and then create the flattened chart we currently get … to help them see hidden fiber content and show where to take mass spectroscopy next without losing data."*

---

### §A — the projection / fiber split
| layer | what it is | who has it |
|---|---|---|
| **flat chart** | m/z vs intensity, peaks as independent points | what MS currently outputs (the projection) |
| **fiber 1** | the **neutral-loss difference-graph** — peak→peak edges labeled by the lost neutral; every edge mass-conserving (EC-code) | the fragmentation *relationships* (dropped) |
| **fiber 2** | the **isotope envelope** — M+1/M+2 decoding composition | implicit in the peaks (not read as a decode) |
| **fiber 3/4** | charge (folded into m/z) + the directed **fragmentation tree** | the genealogy (dropped) |

The recurring framework move (F259/F260/F131): the projection looks like independent points; the substrate holds the relational fiber.

### §B — first pass (ethanol C₂H₆O) — **DEMONSTRATED**
- **Flat chart (peak positions, from conservation):** `m/z = [46, 45, 31, 29, 27]`.
- **Fiber 1 — neutral-loss difference-graph (8 edges the flat chart drops):** 46→45 (−H), 46→31 (−CH₃), 46→29 (−OH), 45→31 (−CH₂), 45→29 (−O/CH₄), 45→27 (−H₂O), 31→29 (−H₂), 29→27 (−H₂). Built as a Class-L graph (`dense_laplacian`); **Laplacian spectrum `[0, 2, 4, 5, 5]`** = the fiber's srmech-native storage signature (F172). The single `0` = the graph is connected (every peak reachable by neutral losses — one fragmentation family).
- **Fiber 2 — isotope decode:** `M+1/M ≈ n_C × 1.07% = 2 × 0.0107 = 2.14%` → the M+1 peak **decodes 2 carbons** (attested ¹³C abundance, B). The flat chart shows M+1 as just-another-peak, not as a composition readout.

*(The peak m/z are textbook/illustrative EI-MS values; the difference-graph + isotope decode are computed from conservation + attested abundances — no fabricated measurements.)*

### §C — NOW vs SOON (the user's "ground up … then the flat chart")
- **NOW:** peak **positions** (conservation), the **difference-graph** (Class L), the **isotope decode** (Class N + attested abundances). The flat chart's *structure* + the dropped fiber — reproduced + surfaced.
- **SOON (gauge-gated #814):** peak **heights/intensities** = the fragmentation-*probability* model, and the directed **fragmentation tree** (which bond cleaves, in what order) = the **loop bind** (k=7 order/tree/direction, F274). The flat chart's heights are a projection of the mechanism; the mechanism is the loop bind. So the chart is built in two layers — positions now (conservation), heights soon (mechanism).

### §D — "where to take MS next without losing data"
The framework reading: **retain the fiber instead of collapsing to m/z-vs-intensity** — keep the **difference-graph** (the parent→fragment relationships) and the **full isotope envelope** (the composition decode). *(Honest no-lineage note: the field already moves this way — tandem MS / MSⁿ recover parent→fragment relationships; high-resolution / FT-MS resolves the isotope envelope; ion mobility adds a shape axis. The framework READS *why* these help — they recover the fiber the single-stage flat chart drops — it does not claim to invent them.)* The framework's specific "don't-flatten" prescription: **publish the difference-graph + isotope envelope as first-class data**, not just the peak list — the relationships are the information.

### §E — scope discipline
Framework-reading ONLY; **benign known compound** (ethanol); illustrative textbook peaks. **NO unknown-identification, NO detection capability, NO synthesis** — only the *information structure* of a spectrum (what the flat chart drops). CAD-ban (graph/algebra, not 3D molecular geometry). Defensive scope (`[[feedback_trauma_informed_defensive_scope]]`). No-lineage (mass spectrometry is the field's; the projection/fiber + EC-code reading is ours).

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (the difference-graph + Laplacian signature + isotope decode, reproducible via committed `mass_spec_ground_up.py`). NEW sub-lock of the chemistry arc (F278); same EC-code key (F259/F260). No-magic (the neutral-loss Δ's + isotope abundance = attested-B; the graph structure = attested-to-conservation A). Class-K (difference magnitudes, no sign-fold/`abs()`). CAD-ban; defensive scope; no-lineage. Single-model / no-twin. Class L (`dense_laplacian`/`jacobi_eigvals`) + the F278 conservation EC-code + the gauge-gated loop-bind mechanism (#814). Builds on F278 (the conservation lock), F259/F260 (the EC-code key), F274 (the loop bind = the fragmentation-tree layer). Verified srmech v0.6.0rc20, `/tmp/srmech_rc20_venv`. `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`; the user's "fiber as spatially-absent encoding" stance.
