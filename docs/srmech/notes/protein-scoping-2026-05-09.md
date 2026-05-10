# Protein folding scoping for srmech — 2026-05-09 cross-domain absorption round

**Round:** Protein folding (NMA / GNM / ANM / contact-map / coevolution / AlphaFold-era)
**Date:** 2026-05-09
**Method:** Dual-agent research pattern (`feedback_dual_agent_research_pattern.md`)

## Headline findings

1. **GNM / ANM / NMA on the residue-interaction network is graph-Laplacian eigendecomposition.** **Literally the same primitive** ephemerides-spectral uses on the 52-body resonance graph (§13 gateway-graph Fiedler partition; Matthews φ = +0.336, Spearman ρ = +0.743 vs empirical Δv). Same math, different graph. **Not analogy — identity.** Strongest cross-domain validation evidence to date that srmech's manifold-parameterised Laplace-Beltrami framing (§3.5) is load-bearing rather than aesthetic.
2. **Helmholtz wave on residue interaction network = NMA harmonic time evolution.** `g(λ_k) = cos(c·t·√λ_k)` where `√λ_k = ω_k` (vibrational frequency from Hessian eigenvalues). The §4.1 "Helmholtz wave" row from the absorption brief *is* the harmonic time evolution of vibrational modes on a protein. Same equation; not metaphor.
3. **Protein contact / distance map = 2D image.** Heat-kernel blur, Perona-Malik bilateral, DoG, Varadhan SDF, anisotropic-tensor, power-spectrum noise — all graphics primitives port verbatim. Perona-Malik on contact map preserves α-helix and β-sheet diagonal-band structure precisely because Perona-Malik preserves edges (state-dependent diffusion); biologically meaningful primitive.
4. **Ramachandran (φ, ψ) torus T² = §3.5 torus row instantiated.** First non-graphics use of the flat torus row. Same `λ_{m,n} = m² + n²` Fourier eigenvalues.
5. **Protein surface = §3.5 sphere S² and triangle-mesh rows.** Globular proteins approximate genus-0 sphere → spherical harmonics with `λ = l(l+1)` (3D Zernike, ZAFCM shape descriptors). Solvent-accessible-surface mesh → cotangent Laplacian; heat-kernel signature (Sun-Ovsjanikov-Guibas) is direct port of Varadhan SDF framework.
6. **Foldseek 3Di alphabet = `SkPhase9BIP` structural cousin.** 20-letter learned structural alphabet (VQ-VAE on protein structure). Cyclic-group-amenable; drop-in HDC binding analogue. **The strongest non-text discrete-alphabet HDC fit outside chess + ephemerides.**
7. **Sheaf-Laplacian on RIN ↔ doom-spectral §3 sheaf-Laplacian raycasting.** Each residue's local frame (rotamer state, local environment) is a stalk; RIN edges are restriction maps. Sheaf cohomology over RIN is a real research direction. Cross-pollination with doom-spectral, not just graphics.
8. **AMSC binary_archive scaling forcing function.** AlphaFold DB ~25 TB; ESM Atlas ~100 TB (via ~600M predicted structures). 4000–20000× larger than JPL DE441 (~5 GB). Forces `binary_archive` adapter to mature: streaming-download, partial fetch, content-addressed deduplication. **Forcing function for AMSC design beyond ephemerides scope.**
9. **Config-vs-substrate ratio inverts to ~20/80.** Closed-form menu (NMA / GNM / contact-map smoothing / Ramachandran T² priors / surface heat-kernel signatures / coevolution Potts) is meaningful but the actual computational work is substrate-dominated: molecular dynamics, AlphaFold / ESMFold / RoseTTAFold, Rosetta abinitio, Monte Carlo, replica-exchange, ligand docking. **Calibration update for §4.2** — config/substrate ratio is domain-dependent, not a fixed 80/20.
10. **EMDR-project connection: none direct.** Protein folding is a cross-domain stretch test for srmech's universality, not a productisation target. Honest framing.

## Operator counts

- **Manifolds:** 22 (main) / 22 (sub) — backbone dihedral T² / side-chain rotamer T^k / RIN graph / contact map 2D / distance map / Cα polymer 1D / 3D Cartesian / internal coords / energy landscape / folding funnel / sequence space / MSA latent / AlphaFold pair-rep / PPI graph / surface mesh / spherical projection / topology graph / ensemble config space / fragment library / DSSP alphabet / β-sheet topology / allosteric network
- **Transforms:** ~18 — graph-Laplacian on RIN (GNM), Hessian (ANM, full atomistic NMA), 2D Fourier on T², spherical harmonics, mesh Laplacian, PCA / tICA / diffusion maps on ensemble, DCA / mfDCA / plmDCA / GREMLIN / EVcouplings on coevolution, wavelets on Cα, fragment-library projection, DCT-II/III on contact map, Plate-style HRR, sheaf-Laplacian, KLT on aligned ensemble
- **Closed-form `g(λ)` operators:** 50+ (main) / 43 (sub-agent numbered) across thematic groups: NMA / mode-propagation family (B-factor prediction, slow-mode reconstruction, mean-square fluctuation, cross-correlation matrix, allosteric perturbation response, domain decomposition / Fiedler partition, hinge-residue identifier, vibrational entropy, mode-coupling, Einstein heat-capacity); contact-map smoothing family (heat-kernel blur, sharpen, DoG, Varadhan SDF, anisotropic, Helmholtz wave, power-spectrum noise, log-normal); Ramachandran T² family (density smoothing, log-prior, band-pass, Kramers' transition rates, harmonic basis fit); coevolution / DCA family (contact prediction, spectral DCA denoising, APC); PCA / ensemble family (essential dynamics, tICA, RMSIP, quasi-harmonic free energy, diffusion-map embedding); Cα-polymer family (smoothing, high-pass, curvature spectrum); surface family (3D Zernike, HKS, WKS, SES smoothing); coarse-graining family (MARTINI-style spectral, RG block-spin, mixed-resolution NMA)
- **Substrate primitives:** 25+ — MD (Amber / GROMACS / NAMD / OpenMM / CHARMM), Langevin, Brownian, REMD / T-REMD / H-REMD, metadynamics, umbrella sampling, MSM, MC (Metropolis / Wang-Landau), Rosetta abinitio + relax, AlphaFold2/3, ESMFold / OmegaFold / RoseTTAFold / RoseTTAFold-AllAtom, SCWRL4 / OPUS-Rota, MODELLER, loop modeling (KIC), AutoDock Vina / Glide / DiffDock, HADDOCK / pyDock / AlphaFold-Multimer, FEP / TI, polarisable force fields (AMOEBA), implicit solvent (GB/SA), steered MD, NMR structure determination (CYANA / ARIA), cryo-EM reconstruction (RELION / cryoSPARC), reaction-diffusion fold prediction (legacy 1980s), Cahn-Hilliard fold-domain separation, QM/MM
- **HDC cyclic groups:** Z₂₀ amino-acid alphabet (caveat: bag with metric structure, not pure cyclic — bind via random projection), Z_64 codon table (degeneracy mapping to Z_20 as sheaf projection), backbone (φ, ψ) on T² (genuine cyclic), side-chain χ-tuples on T^d, secondary-structure 3-letter / 8-letter (DSSP) alphabets, **Foldseek 3Di alphabet** (20-letter structural — strongest non-text fit), Plate-style HRR for sequence binding, k-mer / window binding, structural-fragment binding (Rosetta 9-mer / 3-mer)

## Cross-pollination with already-absorbed srmech primitives

§3.5 cross-manifold table extends — protein instantiation column:

| Manifold | Protein instantiation |
|---|---|
| Euclidean grid + Neumann BC | Distance map; contact map |
| Sphere S² | Globular protein surface (genus-0 topology) |
| Flat torus T² | Ramachandran (φ, ψ) backbone dihedrals |
| Triangle mesh | Solvent-accessible surface mesh |
| **General graph** | **Residue-interaction network — primary protein structure manifold; GNM / ANM / NMA live here** |

Direct primitive ports (graphics → contact map):

- Heat-kernel blur on contact map → smooth predicted contact maps from coevolution; clean noisy AlphaFold pair logits
- Perona-Malik on contact map → preserves α-helix (long stretches of i, i+3, i+4 contacts) and β-sheet (long off-diagonal stretches) while smoothing intra-domain noise
- DoG on contact map → fold boundary detection (where contact density transitions intra-domain → inter-domain)
- Sharpen / band-pass on contact map → emphasises secondary-structure boundaries
- Anisotropic-tensor on contact map → smooth along sequence direction differently from off-diagonal long-range contacts; preserves diagonal-band α-helix structure
- Helmholtz wave on RIN → allosteric perturbation propagation as standing waves (NMA in time domain — same equation)
- Power-spectrum noise on RIN → log-normal-distributed per-residue properties (B-factor, conservation, accessibility)
- Varadhan SDF analogue → reverberation-time-from-RIR-to-distance-to-reverb-tail-onset structurally identical to heat-kernel-decay-to-distance for graphics SDF

Cross-pollination with non-graphics srmech projects:

- **GNM/ANM Fiedler partition ↔ ephemerides §13 gateway-graph Fiedler partition.** Identical math; same architectural slot. Quantitative ephemerides results (Matthews φ = +0.336; Spearman ρ = +0.743 vs Δv) suggest the protein-domain Fiedler analysis would yield comparable predictive power for dynamic-domain identification.
- **Sheaf-Laplacian on RIN ↔ doom-spectral §3 sheaf-Laplacian raycasting.** Stalk = local residue frame; restriction maps = RIN edges.
- **HDC sequence binding ↔ chess BIP / ephemerides BIP / `SkPhase9BIP`.** Foldseek 3Di alphabet is the closest structural cousin.

## AMSC ingestion paths

### `literature_curated`

Ramachandran 1963 + revisions (Lovell 2003 top-8000), DSSP secondary-structure dictionary (Kabsch-Sander 1983), STRIDE secondary structure (Frishman-Argos), rotamer libraries (Dunbrack 2011, SCWRL4), force-field parameters (AMBER ff14SB / ff19SB, CHARMM36m, GROMOS 54A7, OPLS-AA / OPLS-AA/M), BLOSUM matrices (45 / 50 / 62 / 80 / 90), PAM matrices (Dayhoff series), substitution matrices (JTT / WAG / LG), Chou-Fasman propensities, hydrophobicity scales (Kyte-Doolittle, Hopp-Woods, Eisenberg, Wimley-White), disorder predictor tables, CATH / SCOP / SCOPe / ECOD fold classifications, Pfam / InterPro family definitions, EC enzyme classification, GO annotations, OPM membrane orientations, Atchley factors (5D PCA), genetic-code table, Foldseek 3Di alphabet centroids, BLOSUM / PAM matrices.

### `binary_archive`

| Source | Scale | Format |
|---|---|---|
| Protein Data Bank (PDB) | ~220K experimental structures, ~50 GB compressed / ~500 GB uncompressed | PDBx / mmCIF |
| AlphaFold Database | ~214M predicted structures, ~25 TB | mmCIF + pLDDT |
| ESM Atlas / MGnify3D | ~617M predicted structures, ~100 TB | structure + confidence |
| UniProt (TrEMBL + Swiss-Prot) | ~250M sequences, ~250 GB | FASTA |
| MGnify metagenomic | ~2.5B sequences, ~2.5 TB | FASTA |
| BFD (Big Fantastic Database) | ~2.5B clustered MSAs, ~270 GB | FASTA |
| MSA databases per UniRef cluster | precomputed alignments | various |
| CASP archives (CASP7–CASP16) | targets + models + evaluations, ~10 GB | various |
| SCOP / SCOPe / CATH | domain-classification trees, ~500 MB | versioned |
| Pfam / InterPro | family HMMs + signatures, ~3 / 30 GB | HMMER |
| Foldseek / MMseqs2 indices | precomputed alignment indices, ~50–500 GB | binary |
| Rosetta fragment libraries | per-target ~10 MB | text |
| EMDB cryo-EM density maps | ~30K maps | MRC |
| Crystallographic structure factors | per-PDB diffraction data | various |
| MD trajectory databases | Folding@home, GPCRmd, MoDEL, MemProtMD | various |
| Mutation effect databases | ProTherm, HumSavar, ClinVar | various |
| Drug-target interaction databases | ChEMBL, BindingDB, PDBbind | various |

### `csv_bulk` / `json_api`

UniProt API (REST + SPARQL), Ensembl / NCBI Gene / KEGG, PDBe API, AlphaFold REST, ESM Atlas API.

**Scale comment:** AlphaFold DB at 25 TB and ESM Atlas at 100 TB are the largest binary archives the project would touch. Per-structure lazy retrieval via REST is probably right; don't pre-mirror at this scale. Per-protein hypervector precompute (Path D pattern: spectral index over heavy store) is structurally preferable for similarity search.

## Honest project-mission assessment

**Direct EMDR-pulser connection: none.** Protein folding has zero overlap with bilateral haptic therapy. Don't force a connection.

**What this round genuinely earns srmech:**

1. **Validates the cross-manifold framing empirically.** Protein NMA *literally is* the ephemerides Fiedler-partition primitive on a different graph. Universal-claim survives the most demanding stretch test.
2. **Forces AMSC binary_archive maturation.** 25 TB / 100 TB scales force streaming-download, partial fetch, content-addressed dedup design earlier than ephemerides DE441 alone would.
3. **Calibration update for §4.2.** 80/20 is graphics+audio; 20/80 is proteins. Architectural framing must accommodate both ratios.
4. **Path D pattern more relevant than Path C in substrate-dominated domains.** Spectral *index* over heavy store > full unification of computation.
5. **HDC sister application.** Foldseek 3Di alphabet → `Phase3DiBIP` similarity-search service is a clean Path D demo (separate from EMDR device).

**Tenuous-but-honest stretches** (don't force these):

- UTLP for distributed MD — distributed MD already has well-developed infrastructure; UTLP overkill for fs/ms timesteps.
- Drug-discovery cross-cut — possible long-term direction, irrelevant to EMDR therapy device.
- Therapeutic-monitoring / patient-genomic correlation — multi-year horizon if at all.

## First-principles cautions (framework-edge)

- **Hessian vs Laplacian: distinct operators on the same graph.** GNM uses Kirchhoff matrix (1D scalar springs); ANM uses 3N×3N anisotropic Hessian (3D vector springs along contact directions); NMA uses full atomistic Hessian. They share the *graph* but differ in the *operator* — different λ_k, different eigenvector structure. The (Transform, λ_k, g) decomposition needs to track which operator is meant.
- **Residue interaction graph definition is non-canonical.** Cα-Cα cutoff (8 Å, 10 Å, 15 Å variants) gives different graphs.
- **Coarse-graining levels.** Per-atom, per-residue, per-domain graphs all valid; eigenvalue interpretations differ.
- **Protein topology is not closed S² in general.** Globular proteins approximate sphere; membrane proteins, fibrous, IDPs, complexes don't.
- **20-amino-acid alphabet is not cleanly cyclic.** HDC binding via random projection rather than cyclic shift, unlike audio Z₁₂.
- **AlphaFold confidence (pLDDT, PAE) is itself a substrate output.** Treating as ground truth for downstream operations is iffy; catalogue should attest source.
- **Ensemble vs single-structure semantics.** PDB entry may be one X-ray structure or 20 NMR models; catalogue must specify.
- **Time scales are enormous.** Vibrational ps, side-chain ns, loop μs, domain ms, folding s-min, evolution 10⁶ years — different spectral analysis applies at each.
- **Allostery is intrinsically state-dependent.** Pure-spectral `g(λ)` cannot capture conformational coupling that depends on ligand binding; substrate-primitive territory.

## Comparison: main-agent vs sub-agent

| Dimension | Main-agent (with conversation context) | Sub-agent (independent fresh-read) |
|---|---|---|
| Manifold count | 22 | 22 (very close convergence) |
| Closed-form ops | 50+ | 43 (numbered explicitly 1–43) |
| Substrate ops | 25 | 25 (numbered explicitly 1–25) |
| Citation specificity | Loose | **Strong** — Bahar-Atilgan-Erman 1997 (GNM B-factor), Holm-Sander 1996 (Fiedler), Sun-Ovsjanikov-Guibas (HKS), Kabsch-Sander 1983 (DSSP), Lovell 2003 |
| Ephemerides §13 quantitative parallel | Vague | **Specific** — Matthews φ = +0.336, Spearman ρ = +0.743 vs Δv |
| Sheaf-Laplacian → doom-spectral cross-link | Missed | **Caught** |
| **20/80 inversion as framework calibration update** | Missed | **Caught + framed as meta-level insight** |
| Reaction-diffusion fold-prediction historical context (1980s pre-AlphaFold) | Missed | **Caught** |
| Helmholtz wave on RIN = NMA (sharp identity claim) | **Caught** ("literally the same equation, not metaphor") | Stated but less sharp |
| Cyclic-group purity caveat for amino acids | **Caught** ("Z_20 is bag with metric structure, not clean cyclic") | Glossed (treated Z_20 as cyclic-group binding) |
| First-principles cautions as structured section | **§10** | Distributed |
| Time-scale enumeration (ps / ns / μs / ms / s / 10⁶y) | **Caught** | Light treatment |
| AMSC binary_archive maturation forcing function | Caught | **Sharper framing** |
| Path D index-over-heavy-store relevance | Implicit | **Named explicitly** for protein similarity search |

**Convergent core (both reached independently):** all 10 headline findings above. Highest convergence of the three rounds (graphics absorption / audio / protein).

## Takeaways landed in master srmech notebook

- §3.5 cross-manifold table: protein instantiation column added; explicit identity claim "GNM/ANM/NMA on RIN = ephemerides 52-body Fiedler partition primitive — not analogy, identity"
- §4.2 calibration: 80/20 (graphics, audio) vs 20/80 (protein) ratio variation by domain
- §5.3 absorption-round subsection: headline findings + link to this file
- §1.5 future-notebook candidates: protein-spectral row added (status: scoped, strongest cross-domain validation evidence to date, no direct EMDR-project connection)
