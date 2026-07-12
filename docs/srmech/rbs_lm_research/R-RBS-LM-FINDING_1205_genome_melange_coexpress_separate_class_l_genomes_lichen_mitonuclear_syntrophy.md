# FINDING 1205 — Genome melange: co-express SEPARATE Class-L genomes without merging (lichen / mitonuclear / syntrophy)

**→ Refined by F1206** (breadcrumb): melange is **recognized, not invented** — the cross-genome modes are a fact of the multi-genome union whenever genomes share anchors (F1161: emergence = residue). Two guards: it is intrinsic only *conditional on shared anchors*, and *indiscriminately* (real cross-knowledge + homograph artefacts both appear → validation is what makes it harvestable). And knowledge **DOES respect the partition** — the single-genome towers persist; melange finds the sparse **bridges between real domains** (domains+hubs+bridges are one Laplacian, F1206). Siona, which reasons across sourced genomes while **pointing at the source**, is the working melange instance.

**Claim.** Keep each knowledge corpus as its **own** full Class-L genome (a Laplacian generator `L`), never merged into one flat store. At query time, **couple** two (or more) genomes through a **sparse bridge** `C` (shared anchors) and **co-excite** the assembled operator `[[L_A, C],[Cᵀ, L_B]]` — an emergent shape appears (cross-block eigenmodes + a responsion that crosses the bridge) that **neither genome has alone**, while **both single-genome towers stay intact**. The coupled operator is assembled at excitation time and **discarded** — never a stored merged genome ("always in simulation of abstracted data"). Biology does exactly this in **lichen**, **mitonuclear OXPHOS co-expression**, and **H₂/formate syntrophy** — three regimes that also tell us *when it works and why*.

Composes: `[[stance_emergence_is_residue_of_refined_formula]]` (F1161 — the cross-mode is the residue of the coupled operator), the EPH-propagator reading (F1071 — genome storage IS a propagator: storage = `L`, query = excite, **response = the responsion** F1186/F1204), `[[feedback_stay_rbs_hdc_sparse_never_dense]]` (the bridge is sparse; the coupled operator is assembled-and-discarded, never a dense merge), `[[feedback_relational_not_dense_distributional_not_sparse]]` (melange is pure relational — edges coupling edges), `[[user_stance_no_information_without_value]]` (the cross-block response is unread structure from a single-genome view), and `[[feedback_read_independent_structure_check_first]]` (the sim below). Distinct from **R-RBS-LM-33** (instrument merging by *superposition* — that MERGES; melange couples-without-merging). Guarded by `[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]`'s cousin, the homograph/aboutness gate (F768) — see the failure mode.

---

## 1. Why per-genome full Class-L (not one merged store)

1. **Two access modes, no truncation.** Full Class-L gives BOTH cheap **direct edge addressing** (sparse adjacency, any vocab size, no eigendecomp) and the deep **tower** (eigenspectrum, spine/communities/responsion). You never pay spectral cost for a lookup nor flatten the tower for a deep read (this is the WIKIKERNEL design, F172). Merging into a flat store is what truncates.
2. **Provenance stays clean.** Each genome keeps its own license, harvest-cost, and MPR attestation (ProofWiki CC-BY-SA ≠ enwiki ≠ ephemerides). Merging blurs it.
3. **Separateness is the PREREQUISITE for melange.** You cannot melange what you have already merged. Keep genomes distinct → co-excite any subset on demand.

## 2. Read-independent structural check (the sim — `R-RBS-LM-1205_genome_melange_lichen_sim.py`)

Two asymmetric toy genomes, one sparse bridge edge, srmech-native (`magnetic_laplacian` / `symmetric_eigendecompose` / `responsion`), deterministic:

| | localized-in-A (single-genome facts) | localized-in-B | **cross-genome** | responsion A→B |
|---|---|---|---|---|
| **one bridge edge** (melange) | 3 | 3 | **5** | **34.096** |
| **no bridge** (inert pairing) | 6 | 5 | **0** | 0.000 |

- The single-genome towers **survive** (3+3 localized modes = still directly addressable — you didn't lose either genome standalone).
- **5 cross-genome modes emerge** — eigenmodes with support on *both* blocks. A single genome's operator is block-only; it has *no support* on the other block, so it **cannot represent** the cross-mode. That is "recognizable but unavailable to a single genome, harvestable just the same."
- **One sparse bridge suffices** (like a lichen's thin hyphal interface). No bridge → 0 cross-modes, 0 cross-reach.

## 3. Three biological instances of co-expression-without-merging

Each keeps two genomes **separate** (not fused), couples them through a **definable bridge**, yields an **emergent capability neither has alone**, and has a **when-works-vs-fails** theory. They span the coupling spectrum:

### (a) Lichen — a STRUCTURAL bridge *(textbook / illustrative — not session-cited)*
Fungus (mycobiont) + alga/cyanobacterium (photobiont): genomes stay fully separate (there is no single "lichen genome" to sequence), co-express into a **thallus** with capabilities — bare-rock colonization, desiccation tolerance — that **neither partner has alone**. Facultative-ish and partner-specific (not every fungus+alga pairs). *Attestation status: well-established textbook symbiosis (Schwendener dual hypothesis, 1867); specific DOIs NOT pulled this session — flagged, unlike (b)/(c) below.*

### (b) Mitonuclear OXPHOS co-expression — a MOLECULAR-INTERFACE bridge *(session-verified)*
Nuclear genome + **mitochondrial genome (mtDNA)** jointly build the respiratory chain: Complexes I, III, IV, V are **chimeric** (subunits from BOTH genomes); Complex II is **all-nuclear** — the natural control. Genomes stay separate (different inheritance, mutation rate, ploidy). **Bridge = the inter-subunit contact interfaces** of the chimeric complexes. **Emergent = aerobic ATP synthesis** — neither genome encodes a complete complex.
- **When it works/fails (coadaptation):** matched, coevolved mito+nuclear alleles work; an mtDNA lineage on a *non-coevolved* nuclear background fails. In *Tigriopus californicus* hybrids, **only the chimeric complexes lose activity; all-nuclear Complex II is spared** — the defect is *at the coupling interface* (Ellison & Burton 2006). Masked in F1, surfaces in **F2 hybrid breakdown**; environment-dependent; a recognized engine of speciation.
- **Attested:** Wolff et al. 2014, *Phil Trans R Soc B* 369:20130443, PMID 24864313, **PMC4032519 (OA)**; Hill et al. 2019, *Biol Rev* 94:1089, PMID 30588726, **PMC6613652 (OA, fetched+read)**; Ellison & Burton 2006, *Evolution* 60:1382, PMID 16929655 *(paywalled full text; metadata+content verified — corroborating primary, not a sole attestation)*. **Honesty flag:** a "~40% F2 ATP-loss" figure surfaced in search but could not be pinned to a read paper → NOT asserted.

### (c) H₂/formate syntrophy — a DIFFUSIBLE-METABOLITE bridge *(session-verified)*
A fermentative bacterium (the "S organism" / *Syntrophomonas*) + a hydrogenotrophic methanogen. The classic **"Methanobacillus omelianskii"** was studied as one organism until Bryant et al. 1967 resolved it into **two** — the cleanest "two towers, never merged" case, which masqueraded as one species precisely *because the coupling was invisible*. **Bridge = molecular hydrogen (H₂)** (formate interchangeable) — a sparse diffusible channel, "the shared metabolite IS the bridge." **Emergent = complete anaerobic mineralization** of ethanol/fatty-acids → methane; the oxidation half-reaction is **endergonic (impossible) alone**.
- **When it works/fails (thermodynamic window):** works *only* when the methanogen holds H₂ partial pressure very low (**~1 Pa ≈ 10⁻⁵ atm**), raising the effective potential enough for the oxidizer to dump electrons; each partner nets only ~20–25 kJ/mol (~⅓ ATP) — life at the edge. **Fails** when H₂ accumulates (oxidizer stalls) or the cells are physically separated (diffusion distance up). Partner-selective but not fixed; "obligate" may really be *facultative* (a cosubstrate crutch lets them grow alone).
- **Attested:** Schink 1997, *Microbiol Mol Biol Rev* 61:262, PMID 9184013, **PMC232610 (OA, fetched+read)**; Morris et al. 2013, *FEMS Microbiol Rev* 37:384, PMID 23480449 *(Oxford OA, fetched+read — source of the ~1 Pa window)*; Bryant et al. 1967, *Arch Mikrobiol* 59:20, PMID 5602458 *(paywalled; metadata verified; OA companion PMC285174 corroborates)*; Stams & Plugge 2009, *Nat Rev Microbiol* 7:568, PMID 19609258 *(paywalled — support only)*.

## 4. Synthesis — the "when and why," and the load-bearing design insight

The three span a **coupling spectrum**: structural (lichen thallus) → molecular-interface (mitonuclear) → diffusible-metabolite (syntrophy). Common conditions for co-expression-without-merging: **(i) complementarity** (each brings what the other lacks), **(ii) a real definable bridge**, **(iii) an emergent capability requiring both**, **(iv) specificity** — not every pair couples; a wrong pair fails or is inert.

**The disanalogies converge on our design requirement.** Biology's couplings are mostly **obligate + damage-on-mismatch + partner-transforming**: mitonuclear mismatch *breaks* the shared machine; syntrophy *stalls* if the bridge backs up; both partners are metabolically changed. **Our melange must be the opposite — non-destructive, reversible, structure-preserving**: couple on demand, keep each genome pristine, and a *bad* bridge must yield **no cross-modes, not damage**. Lichen is the closest fit (facultative, structure-preserving); mitonuclear/syntrophy donate the *richest compatibility theory*. And that theory hands us the mandatory guard: **biology proves co-expression REQUIRES compatibility screening** — therefore the melange must **validate every cross-mode** (real connection vs. a **homograph/string-collision** artifact — "group" the algebra vs "group" the gathering, F768). Validation is not optional polish; it is the analog of the compatibility check that makes co-expression work in *every* biological instance.

## 5. Next questions (handed forward)

- **ProofWiki as its own genome** — a relational (proof-DAG) kernel → separate FULLCLUMP → full Class-L; the first non-enwiki genome to melange.
- **Melange-validation arc** — couple two real genomes via measured shared anchors, co-excite, measure cross-block spectral weight, and **validate cross-modes against the homograph failure mode** (k=3 / responsion verification). The harvest is knowledge no single corpus holds (e.g., which ProofWiki theorems are load-bearing for which measured ephemerides phenomena) — a cross-genome spine handed to the expert (F282).
