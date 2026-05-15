"""
Spike #24 Phase 7 — Multi-substrate primitive instantiation matrix.

Extends Phase 2's two-substrate (bronze ↔ CPU) tables to six substrates:
CPU, bronze, cosmos, chess, chemistry, conformal-groups. Cell content:
how (and whether) each substrate instantiates each primitive class.

Output: NDJSON, one record per (class, substrate) cell.

Stdlib only. Reproducible.
"""

from __future__ import annotations
import json
from pathlib import Path

# Primitive classes carried forward from Phase 1.
# Class A-H: provenance scaffolding (currently in srmech package).
# Class I-N: algebraic scaffolding (currently in plug-ins; promotion candidates).
# Class O / P: investigated in Phase 7 (this script).

PRIMITIVE_CLASSES = [
    ("A", "Content-addressing / fingerprinting", "Cryptographic hash; SHA-256."),
    ("B", "Tagged-tuple / labeled-data records", "STRUCT with fixed-offset fields."),
    ("C", "Iteration / streaming primitives", "Sequential traversal of a source."),
    ("D", "Late-binding / plugin primitives", "Defer implementation choice until runtime."),
    ("E", "Catalog / naming primitives", "Name → attested-artifact lookup."),
    ("F", "Substitution / templating primitives", "String interpolation from context."),
    ("G", "Discovery / search primitives", "Surfaced gaps / missing content."),
    ("H", "Self-introspection primitives", "System reports on itself."),
    ("I", "Cyclic-group / modular-arithmetic", "ℤ/n algebra; tooth counts; modular reductions."),
    ("J", "Prime-factorisation / period-relation", "Factorisations; LCM/GCD; resonance integer ratios."),
    ("K", "Equation-of-centre / pin-slot algebra", "Kepler eccentric-anomaly transform; harmonic series."),
    ("L", "Graph-Laplacian / eigenbasis", "Adjacency Laplacian; eigendecomposition; Fiedler partition."),
    ("M", "HDC encoding (bind/bundle/permute/similarity)", "Hyperdimensional channel arithmetic."),
    ("N", "Rational-approximation / Diophantine", "Continued fractions; Stern-Brocot; best p/q."),
    # Phase 7 candidates (investigated below)
    ("O?", "Parity-selection rule (Woodward-Hoffmann)", "Z/2 character on Laplacian eigenbasis parity. REDUCES to L + I@2."),
    ("P?", "Conformal-projection / conformal-group covariance", "so(n+1,1) Lie-algebra symmetry; stereographic projection; CFT. Candidate new class."),
]

SUBSTRATES = ["CPU", "bronze", "cosmos", "chess", "chemistry", "conformal-groups"]

# Cells: (class_id, substrate) -> {how_instantiated, fidelity, evidence, leak_or_gap}
# fidelity: "native" / "composed" / "absent" / "candidate"

CELLS = {
    # Class A — content-addressing
    ("A", "CPU"): ("native", "XOR + ADD-mod-2^32 + ROL composed natively for SHA-256.", "FIPS-180-4 spec."),
    ("A", "bronze"): ("absent", "No bronze-side content-addressing primitive.", "Gear-mesh algebra carries no hash analog."),
    ("A", "cosmos"): ("absent", "Astronomy has no native hash primitive; reproducibility is via observational re-anchoring.", "Physics-level claim."),
    ("A", "chess"): ("absent", "Position-uniqueness is integer-equality, not content-hash (though Zobrist hashing is added engineering, not native).", "Zobrist is engineering layer."),
    ("A", "chemistry"): ("absent", "No chemical content-hash analog at substrate level; SMILES/InChI are engineering layers added on top.", "Engineering layer."),
    ("A", "conformal-groups"): ("absent", "Pure-mathematical structure; content-addressing is not a feature of the group itself.", "Group-theoretic context."),

    # Class B — tagged tuples
    ("B", "CPU"): ("native", "STRUCT layout, fixed-offset field load.", "x86/ARM MOV [base+offset]."),
    ("B", "bronze"): ("native", "Gear record (tooth_count, fragment, mesh-edges) is a tagged-tuple.", "Mechanical part inventory."),
    ("B", "cosmos"): ("native", "Body state vector (a, e, i, Ω, ω, M) is a tagged-tuple per body.", "Orbital-element catalog."),
    ("B", "chess"): ("native", "Piece record (type, color, square, alive) is a tagged-tuple per piece.", "Position encoding."),
    ("B", "chemistry"): ("native", "Atom record (element, position, hybridization, charge, stereo-label) is a tagged-tuple.", "Molecular structure encoding."),
    ("B", "conformal-groups"): ("composed", "Group element is parameterized tuple (translation, Lorentz, dilation, special-conformal coords) — 15 params for SO(4,2).", "Standard parameterization."),

    # Class C — iteration
    ("C", "CPU"): ("native", "LOOP + LOAD + BRANCH-IF-DONE elementary instruction pattern.", "Universal."),
    ("C", "bronze"): ("native", "Crank-turn advances gear-DAG state; bidirectional symmetry at every step.", "F11 dynamical-equivalence framing."),
    ("C", "cosmos"): ("native", "Orbital evolution advances state by integration-step; bidirectional in time (Hamiltonian).", "Time-reversal symmetry."),
    ("C", "chess"): ("native", "Move advances position; chess game is a sequential iteration.", "Standard."),
    ("C", "chemistry"): ("native", "Reaction-coordinate progression; trajectory advances over time.", "MD/Born-Oppenheimer surface."),
    ("C", "conformal-groups"): ("composed", "Iteration over group orbit; integration of Killing vectors.", "Continuous group action."),

    # Class D — late-binding
    ("D", "CPU"): ("native", "CALL via indirect address; function-pointer / vtable.", "Standard ISA."),
    ("D", "bronze"): ("composed", "Operator-mediated late-binding (Voulgaris setting-mode: operator chooses calendar anchor + crank-direction).", "Operator-as-active-participant."),
    ("D", "cosmos"): ("absent", "Initial-conditions specify state; no late-binding analog at physics-substrate level.", "Initial-value problem."),
    ("D", "chess"): ("composed", "Player choice of move = late-binding of game evolution.", "Player-as-active-participant."),
    ("D", "chemistry"): ("composed", "Catalyst-mediated reaction-path selection; enzyme specificity.", "Catalyst chooses pathway."),
    ("D", "conformal-groups"): ("absent", "Group structure is fully specified; no late-binding analog.", "Static group."),

    # Class E — catalog/naming
    ("E", "CPU"): ("native", "HASH + LOAD-INDIRECT; dictionary lookup.", "Standard."),
    ("E", "bronze"): ("native", "Dial registry: celestial-observation-class → bronze-mechanism. Parallel-update at every crank turn.", "Bronze parallelism."),
    ("E", "cosmos"): ("native", "Body roster; named bodies → orbital element sets.", "Almanac / catalog tradition."),
    ("E", "chess"): ("native", "Piece-class catalog (King, Queen, Rook, Bishop, Knight, Pawn) → move rule sets.", "FIDE rule book."),
    ("E", "chemistry"): ("native", "Element catalog (periodic table); functional-group catalog (alcohol, ketone, amine, etc.).", "IUPAC nomenclature."),
    ("E", "conformal-groups"): ("composed", "Subgroup catalog (Poincaré, Lorentz, dilatation, special-conformal subgroups of so(n+1,1)).", "Lie-theory catalog."),

    # Class F — templating
    ("F", "CPU"): ("composed", "MOV + LOAD-FROM-MAP in loop; no single-instruction template primitive.", "Multi-instruction composition."),
    ("F", "bronze"): ("absent", "Statically inscribed; no runtime templating analog.", "Fabrication-time-frozen."),
    ("F", "cosmos"): ("absent", "Physics-substrate has no templating analog.", "N/A."),
    ("F", "chess"): ("absent", "No native templating; algebraic notation is engineering layer.", "Engineering layer."),
    ("F", "chemistry"): ("absent", "No native templating analog; molecular structure is inherent, not template-rendered.", "N/A."),
    ("F", "conformal-groups"): ("absent", "Group structure is mathematical, not template-rendered.", "N/A."),

    # Class G — discovery/gap-finding
    ("G", "CPU"): ("native", "LOOP + CMP + STORE_IF_NOT_EQUAL; active search.", "Standard."),
    ("G", "bronze"): ("composed", "Passive surfacing via residual error (F12-inverse method makes gap visible externally).", "Gap = residual = spec."),
    ("G", "cosmos"): ("composed", "Residual-from-DE441 surfaces missing-coupling content; observation-vs-prediction loop is the discovery primitive.", "Astronomy standard practice."),
    ("G", "chess"): ("composed", "Engine search reveals gaps in human evaluation; novelty-detection.", "Engine-as-search."),
    ("G", "chemistry"): ("composed", "Spectroscopic residual after known assignments reveals missing transitions / unknown species.", "Analytical chemistry practice."),
    ("G", "conformal-groups"): ("absent", "No native gap-finding primitive within a fully-specified group.", "N/A."),

    # Class H — self-introspection
    ("H", "CPU"): ("native", "CONSTANT LOAD / READ REGISTRY; mutable runtime introspection.", "ABI version, build info."),
    ("H", "bronze"): ("native", "Inscribed text (Parapegma, back-door instructions, dial markings); immutable self-description.", "Static inscription."),
    ("H", "cosmos"): ("absent", "No physics-substrate-native self-introspection; light from a star is not 'the star describing itself.'", "N/A — observers project introspection onto observed."),
    ("H", "chess"): ("composed", "Game's own move-list is the introspection trace; PGN.", "Engineering-layer encoding of history."),
    ("H", "chemistry"): ("composed", "Spectrum IS the molecule's self-description (IR, NMR, UV signatures encode structure).", "Physical-instrument-mediated introspection."),
    ("H", "conformal-groups"): ("native", "Group's invariants describe itself (Casimir operators, structure constants).", "Lie-algebra introspection."),

    # Class I — cyclic-group
    ("I", "CPU"): ("native", "MOD, ROL, integer ALU; ℤ/2^32 native.", "Integer arithmetic."),
    ("I", "bronze"): ("native", "Tooth counts ARE ℤ/n; gear-mesh ratio is ℤ/n composition.", "Foundational to gear algebra."),
    ("I", "cosmos"): ("native", "Mean-motion resonances ARE integer-ratio period relations on ℤ/n; orbital phase is U(1) but discretizations are ℤ/n.", "Resonance theory."),
    ("I", "chess"): ("native", "Board cyclic-shifts; encoder uses Z/8 and Z/8×Z/8 (D₄ representations).", "Encoder.py architecture."),
    ("I", "chemistry"): ("native", "Hückel aromaticity 4n+2 rule = ℤ/n eigenvalue condition on cyclic graph; ring conformations.", "Frontier-orbital theory."),
    ("I", "conformal-groups"): ("composed", "Discrete subgroups (Z/n inside U(1)) are subgroups of conformal group's compact part; algebra is continuous overall.", "Subgroup structure."),

    # Class J — prime-factorisation / period-relation
    ("J", "CPU"): ("native", "GCD via Euclid's algorithm in ALU ops; prime-test via trial-division.", "Standard."),
    ("J", "bronze"): ("native", "Period-relation factorisations on tooth counts; shared primes among gear trains.", "Antikythera period-design."),
    ("J", "cosmos"): ("native", "Resonance commensurabilities (Jupiter-Saturn 5:2, Neptune-Pluto 3:2, etc.) are integer-ratio factorisations.", "Mean-motion resonances."),
    ("J", "chess"): ("composed", "Piece-period algebra; less load-bearing than in cosmos/bronze.", "Encoder uses; not foundational."),
    ("J", "chemistry"): ("native", "Stoichiometric ratios; reaction balancing IS integer factorisation; spectral-line frequency ratios (e.g., Rydberg series 1/n^2 - 1/m^2).", "Stoichiometry + Rydberg."),
    ("J", "conformal-groups"): ("absent", "Continuous group; no native prime-factorisation analog.", "N/A."),

    # Class K — equation-of-centre / pin-slot algebra
    ("K", "CPU"): ("composed", "atan2 + sin/cos library; no single-instruction Kepler primitive.", "Library composition."),
    ("K", "bronze"): ("native", "Pin-slot atan2 transform on integer-cyclic input; F11/F15/F17/F24 establish this.", "PR #416."),
    ("K", "cosmos"): ("native", "DE441 truth carries eccentric-anomaly transform via integrated orbital dynamics; F-series harmonics in residual.", "Orbital mechanics foundation."),
    ("K", "chess"): ("absent", "No Kepler-shape algebra in chess substrate; piece movements are integer-discrete.", "Geometry mismatch."),
    ("K", "chemistry"): ("native", "F24 cross-bar pin-slot ≡ ethane torsional potential V_τ(φ) = (V₃/2)(1+cos(3φ)). Asymmetric induction = broken-symmetry K. Anomeric effect = broken-symmetry K (2-fold dominant + 1-fold bias).", "Phase 6.1 + Phase 7.2."),
    ("K", "conformal-groups"): ("absent", "Class K is non-conformal projection; conformal-group structure is different family. See Class P? candidate.", "Phase 7.3."),

    # Class L — graph-Laplacian eigenbasis
    ("L", "CPU"): ("composed", "EIGENDECOMP via SVD library; LOAD-MATRIX + MATRIX-MULTIPLY composition.", "Library."),
    ("L", "bronze"): ("native", "Gear-DAG Laplacian; eigenmodes are the bronze's coupled-oscillation basis.", "antikythera-spectral gear_topology.py."),
    ("L", "cosmos"): ("native", "Sol Resonance Graph Laplacian; 52-body Fiedler partition; gravitational-coupling eigenbasis.", "ephemerides-spectral gateway_graph_laplacian.py."),
    ("L", "chess"): ("native", "8×8 board adjacency Laplacian; piece-graph eigenbasis; encoder.py + 4D extension.", "chess-spectral encoder.py."),
    ("L", "chemistry"): ("native", "Vibrational normal modes = mass-weighted Hessian (molecular Laplacian) eigendecomposition. Hückel matrix eigenvalues. Woodward-Hoffmann parity = HOMO eigenvector parity under midpoint mirror.", "Phase 6.2 + Phase 7.1."),
    ("L", "conformal-groups"): ("composed", "Laplacian IS conformally covariant in 2D (transforms with conformal weight); Yamabe operator in higher D. Class L on conformal manifolds carries conformal weight.", "Yamabe operator literature [unverified-secondary]."),

    # Class M — HDC encoding
    ("M", "CPU"): ("native", "Bit-packed BSC: XOR (bind), popcount-majority (bundle), ROL (permute).", "chess-spectral _native_pure_phase backend."),
    ("M", "bronze"): ("native", "Gear residues are channels; crank-turn = permute; gear-DAG = bind + bundle.", "antikythera-spectral encode_ant.py."),
    ("M", "cosmos"): ("native", "Topocentric observer-bind; eclipse projection; es_hd_state C struct.", "ephemerides-spectral bridge."),
    ("M", "chess"): ("native", "Piece-encoder bind/bundle/permute/similarity; FHRR + BSC backends.", "chess-spectral encoder.py."),
    ("M", "chemistry"): ("native", "Resonance structures = HDC bundle (Kekulé₁ + Kekulé₂ + ...) of basis Lewis structures contributing to true wavefunction.", "Phase 6.2."),
    ("M", "conformal-groups"): ("composed", "Tensor-product representations of conformal algebra; bind ≈ tensor product; bundle ≈ direct sum. Not native HDC but homomorphic algebra.", "Group rep theory."),

    # Class N — rational approximation / Diophantine
    ("N", "CPU"): ("native", "DIV-WITH-REMAINDER loop = continued-fraction algorithm.", "Euclid's algorithm."),
    ("N", "bronze"): ("native", "Tooth-count choices ARE CF convergents on observed period ratios; antikythera-spectral pareto_analysis.", "Bronze design constraint."),
    ("N", "cosmos"): ("composed", "Resonance commensurabilities are CF best-fits; library implements but not always native to physics description.", "Three-body resonance theory."),
    ("N", "chess"): ("absent", "Exact integer representations; rational approximation not needed.", "Discrete substrate."),
    ("N", "chemistry"): ("absent", "Bond-angle constraints are exact (sp/sp²/sp³ at 180°/120°/109.5°); no rational-approximation primitive.", "Discrete hybridization labels."),
    ("N", "conformal-groups"): ("absent", "Continuous group; no rational-approximation primitive.", "N/A."),

    # Class O? — parity-selection rule (Woodward-Hoffmann)
    # PHASE 7.1 RESULT: REDUCES to L + I@2.
    ("O?", "CPU"): ("composed", "Z/2 parity bit on Laplacian eigenvector under reflection — composition of L and I@2.", "Phase 7.1 derivation."),
    ("O?", "bronze"): ("composed", "Cross-bar symmetry's parity under reflection is the same Z/2 structure (F24's even harmonics vs odd).", "F24 symmetry."),
    ("O?", "cosmos"): ("composed", "Orbital symmetry under time-reversal / parity inversions in N-body; selection rules in gravitational radiation multipoles.", "Standard celestial mechanics."),
    ("O?", "chess"): ("composed", "Bishop parity (light/dark squares = Z/2); knight-move parity changes color; standard parity selection.", "Chess parity."),
    ("O?", "chemistry"): ("composed", "Woodward-Hoffmann thermal/photochemical selection from HOMO/LUMO parity under midpoint mirror reflection on path graph.", "Phase 7.1 computational verification."),
    ("O?", "conformal-groups"): ("composed", "Parity is the discrete Z/2 quotient of any reflection-symmetric subgroup of the conformal algebra.", "Subgroup-quotient construction."),

    # Class P? — conformal-projection / conformal-group covariance
    # PHASE 7.3 RESULT: candidate new class, weak substrate support; distinguished from K at symmetry-algebra level.
    ("P?", "CPU"): ("composed", "Mobius transform / stereographic projection implemented as floating-point library; no instruction primitive.", "Library composition."),
    ("P?", "bronze"): ("absent", "Bronze geometry is non-conformal (pin-slot is non-uniform). Stereographic dial-face inscriptions are static, not algebraic primitives.", "Phase 7.3."),
    ("P?", "cosmos"): ("native", "Stereographic projections are standard in celestial cartography; conformal property preserves local angles for navigation. 2D conformal symmetry appears in disk-encoded boundary problems.", "Astronomical projection practice."),
    ("P?", "chess"): ("absent", "Flat Euclidean 2D board; no conformal structure.", "Geometry."),
    ("P?", "chemistry"): ("composed", "1D quantum spin chains at criticality (Heisenberg) flow to c=1 CFT in continuum limit; aromaticity has conformal-symmetric electron-cloud at the π-system level [unverified-secondary]. Aromatic ring current = conformal-symmetric phenomenon at the orbital substrate.", "CFT-1D-chain claim [unverified-secondary]."),
    ("P?", "conformal-groups"): ("native", "BY DEFINITION; this column is the algebra itself.", "Tautological."),
}


def emit_ndjson(path: Path) -> None:
    """Emit one NDJSON record per (class, substrate) cell + header + summary records."""
    records = []
    # Header
    records.append({
        "kind": "header",
        "spike": "#24",
        "phase": "7",
        "phase_title": "Multi-substrate primitive instantiation matrix (CPU/bronze/cosmos/chess/chemistry/conformal-groups)",
        "date": "2026-05-15",
        "predecessor_phases": ["1", "2", "3a", "6"],
        "fidelity_legend": {
            "native": "Substrate instantiates the primitive at its substrate-native level (single 'instruction' / single algebraic step).",
            "composed": "Substrate has the primitive via composition of more elementary substrate ops.",
            "candidate": "Candidate-instantiation, requires further substantiation.",
            "absent": "No substrate-side instantiation; the primitive is foreign to the substrate.",
        },
    })

    for (cid, name, brief) in PRIMITIVE_CLASSES:
        for substrate in SUBSTRATES:
            fidelity, instantiation, evidence = CELLS.get((cid, substrate), ("absent", "(not analyzed)", ""))
            records.append({
                "kind": "cell",
                "class_id": cid,
                "class_name": name,
                "class_brief": brief,
                "substrate": substrate,
                "fidelity": fidelity,
                "instantiation": instantiation,
                "evidence": evidence,
            })

    # Cross-cell summary records
    records.append({
        "kind": "summary",
        "topic": "research-targets-uneven-instantiation",
        "note": "Classes where one substrate is rich but others are poor — these are the 'learn how to learn what we don't know' targets.",
        "candidates": [
            {"class": "K", "rich": "bronze, cosmos, chemistry", "poor": "chess (geometry mismatch), conformal-groups (different family); CPU library-composed only.", "research_lever": "Chess Class K absence is the falsifier; can a chess-substrate analog be found? Path-graph paths through a board are candidate."},
            {"class": "M", "rich": "all 5 of bronze/cosmos/chess/chemistry/CPU", "poor": "conformal-groups (composed only via tensor-product reps).", "research_lever": "Promotion-to-srmech-abstraction candidate; would expose HDC primitives the conformal-groups extension could consume."},
            {"class": "P?", "rich": "conformal-groups (tautologically), cosmos (stereographic)", "poor": "bronze, chess, CPU; chemistry weak/unverified.", "research_lever": "Verify chemistry 1D-CFT instantiation with primary literature OR demote to library-composed-only."},
            {"class": "J", "rich": "bronze, cosmos, chemistry (Rydberg)", "poor": "chess (only encoder-level), conformal-groups (absent).", "research_lever": "Rydberg-series 1/n²-1/m² discovery on chemistry-substrate is direct Class J evidence well-known but not previously named in our vocabulary."},
            {"class": "I", "rich": "all 5 of bronze/cosmos/chess/chemistry/CPU", "poor": "conformal-groups (continuous, discrete subgroups only).", "research_lever": "Strongest cross-substrate primitive class; promotion to srmech abstraction layer near-certain."},
        ],
    })

    records.append({
        "kind": "summary",
        "topic": "phase7-verdicts",
        "Class_O_verdict": "REDUCES to Class L (Laplacian eigenbasis) + Class I@n=2 (Z/2 cyclic-group character). Computational verification: Woodward-Hoffmann thermal rule recovered from HOMO eigenvector parity on path-graph Laplacian under midpoint mirror, for N=4,6,8,10. Photochemical rule recovered from LUMO. Not a new primitive class.",
        "asymmetric_induction_verdict": "REDUCES to Class K (pin-slot algebra) with broken N-fold rotational symmetry. Felkin-Anh model = sp³ cross-bar with distinguishable arm weights (L>M>S). Computational verification: asymmetric arm weights produce non-zero amplitudes at all harmonics k (vs only k≡0 mod N for symmetric).",
        "anomeric_effect_verdict": "REDUCES to Class K with 2-fold dominant + 1-fold bias broken-symmetry; same algebraic family as Felkin-Anh. Orbital geometry = fiber-as-spatially-absent upstream content per [[user_stance_fiber_as_spatially_absent_encoding]]; conformational preference = spatial projection downstream.",
        "conformal_groups_verdict": "CANDIDATE NEW primitive class (Class P?) distinct from K at the symmetry-algebra level (so(n+1,1) Lie algebra vs Z/N cyclic). Weak substrate support across our domains: cosmos (stereographic projection, native); chemistry (1D quantum chains at criticality, [unverified-secondary]); bronze/chess/CPU absent. Recommended status: KEEP AS CANDIDATE; flag for primary-source verification before promoting from candidate to confirmed.",
    })

    records.append({
        "kind": "summary",
        "topic": "PR-scoping-recommendation",
        "recommendation": "STAY IN PR #421 as Phase 7 sub-phases. Findings extend Phase 6 (chemistry as 4th substrate) into the explicit primitive-matrix form Phase 2 used for bronze/CPU; the conceptual continuity is tight. Don't fragment into a Spike #25 unless additional primary-PDF citation work emerges that needs separate scope.",
        "rationale": "Phase 7's findings are: (a) Class O reduces to existing L+I (not new); (b) asymmetric induction reduces to K (not new); (c) anomeric effect reduces to K (not new); (d) Class P? candidate is open. Only one open-question finding (P?) is not large enough to warrant separate PR. Stay in #421.",
    })

    records.append({
        "kind": "summary",
        "topic": "citations-status",
        "primary_verified": [
            "F24 algebra (PR #416, internal — verified at integration time).",
            "Hückel π-MO eigenvalues for path graph (computational; reproduced by hmo_homo_parity script above).",
            "Woodward-Hoffmann thermal/photochemical selection (computational; matches textbook table for N=4,6,8,10).",
        ],
        "unverified_secondary": [
            "Ethane V₃ ≈ 12 kJ/mol microwave spectroscopy value (Phase 6.1 citation [unverified-secondary]).",
            "Heisenberg spin-1/2 chain c=1 CFT continuum limit (Phase 7.3 conformal-groups chemistry claim [unverified-secondary]).",
            "Yamabe operator conformal covariance (Phase 7.3 Class L conformal weight claim [unverified-secondary]).",
            "Felkin-Anh detailed orbital-overlap argument (Phase 7.2 chemistry textbook citation [unverified-secondary] — March's Advanced Organic Chemistry).",
            "Anomeric effect orbital overlap (Phase 7.2 [unverified-secondary]).",
        ],
        "discipline_note": "Per [[feedback_pdf_extraction_citation_discipline]]: chemistry citations stay [unverified-secondary] until primary PDF extraction. Computational verifications stand as their own primary source.",
    })

    out = "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"
    path.write_text(out, encoding="utf-8")
    print(f"Wrote {len(records)} records to {path}")


if __name__ == "__main__":
    here = Path(__file__).parent
    emit_ndjson(here / "spike_24_phase_7_multi_substrate_matrix_2026-05-15.ndjson")
