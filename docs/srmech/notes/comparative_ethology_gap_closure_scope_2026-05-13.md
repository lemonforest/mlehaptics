# Comparative-Ethology Gap-Closure Scoping — Three Concrete Spike Protocols

**Date:** 2026-05-13
**Branch:** `research/comparative-ethology-age-sociality`
**Author:** Subagent gap-closure scoping for srmech
**Status:** Research notes only (no PR)
**Prior:** [`comparative_ethology_age_sociality_literature_review_2026-05-13.md`](./comparative_ethology_age_sociality_literature_review_2026-05-13.md)

---

## Citation corrections vs prior lit review

PDF-verification (per project discipline) caught two errors in the prior lit-review's reference list. Carrying them forward here:

- **Silk, Finn, Porter & Pinter-Wollman (2018)** — the prior review listed this as *Current Zoology* 64(1):27-44, DOI `10.1093/cz/zox071`. That DOI resolves to a different paper (Bierbach, Arias-Rodriguez, Plath 2018 on sulfide-adapted fish). **Correct citation:** *Trends in Ecology & Evolution* 33(6):376–378, DOI `10.1016/j.tree.2018.03.008`. The longer companion methods piece is **Finn, Silk, Porter & Pinter-Wollman (2019)** *Animal Behaviour* 149:7-22, arXiv:1712.01790.
- **Turner, Bills & Holekamp (2018)** "Ontogenetic change in determinants of social network position in the spotted hyena" *Behav Ecol Sociobiol* 72(1):11, DOI `10.1007/s00265-017-2426-x`. Prior review attributed authorship to "Smith, Memenis & Holekamp"; that ordering does not match the published article. The Holekamp-lab connection is correct; the authorship is not.
- **Iacopini et al.** has now been formally published (was a 2023 preprint at first-listing): *Phil Trans R Soc B* 379:20230190 (2024), DOI `10.1098/rstb.2023.0190`. arXiv:2309.03783 confirmed.

---

## Gap #1 — Hodge-Laplacian / Betti-number tracking across ontogenetic-stage simplicial complexes

### A. The gap, as testable proposition

**Proposition (G1):** For a longitudinally-observed social population stratified into ontogenetic stages s ∈ {cub/fledgling, juvenile, sub-adult, adult, post-reproductive}, the Hodge decomposition of the stage-specific clique complex X_s yields a Betti-number trajectory (B_0(s), B_1(s), B_2(s)) that distinguishes species exhibiting the canonical juvenile-cooperation → adult-exclusion transition (chimpanzees, hyenas, elephants, marmots) from species lacking it (bonobos, resident orcas). Specifically: **B_1 (loop content of the social complex) is predicted to be *non-monotone* in stage for transition-exhibiting species (peak in juvenile/sub-adult), and *flat or monotone* in non-transition species.** Falsifiable as: if the within-species across-stage B_1 trajectory is statistically indistinguishable across all sampled species (after permutation null), the proposition is refuted.

### B. Accessible datasets for first pilot

**Primary candidate: Wytham/Wild et al. 2024 great tit ontogeny dataset.**

- Wild, S., Alarcón-Nieto, G., Aplin, L. (2024). "Data for: Social network data in wild great tits during ontogeny." Dryad. DOI `10.5061/dryad.x95x69ps8`.
- License: CC0 (Dryad default; user should re-verify).
- Content: ~208 MB; RFID feeder visits across 4 seasons (summer through spring) of juvenile *Parus major* life; per-individual age class labels (fledgling, juvenile, adult), nestbox metadata, weekly group-by-individual matrices.
- **Critical for Gap #1**: explicit ontogenetic stratification is built into the dataset's RDA files. Several thousand individual-week observation rows; precise count not published in landing page.

**Secondary candidate: Mara Hyena Project CSVs (Holekamp Lab).**

- holekamplab.org/project-database.html — CSV bulk downloads; GitHub mirror at github.com/MaraHyenaProject hosts per-paper analysis scaffolding.
- License unclear from landing page; user should email lab for confirmation before publishing pilot.
- 27 years of observational records, multiple clans, three-stage ontogeny (communal-den, den-independent pre-reproductive, early-adult) is the framing used in **Turner, Bills & Holekamp (2018)** — so dataset is known to support the stratification.

**Tertiary candidate: Amboseli Elephant Research Project.**

- elephanttrust.org (custodian: Amboseli Trust for Elephants). Five decades, ~3000 individuals. Public data-availability protocol is *not* documented in landing-page material I could verify — likely requires custodian-permission. Mark as **paywalled-ish** / custodian-gated.

**Cayo Santiago rhesus macaques** — referenced in lit review; data is collected but redistribution is gated through Caribbean Primate Research Center. Treat as conditional.

### C. First-spike protocol sketch

```
INPUT: edge-list E = {(i, j, t, w)} with individual IDs i,j; timestamp t; weight w (interaction count / duration / RFID co-presence).
INPUT: metadata M = {i -> age_class_at_time(t)}.

STEP 1. Stage-stratify E. For each ontogenetic stage s, restrict to edges where both endpoints
  are in stage s at time t. Aggregate over a stage-appropriate window (e.g., per-season for tits;
  per-life-phase for hyenas). Output: G_s = weighted graph for stage s.

STEP 2. Threshold to get a binary skeleton. Use a principled threshold sweep (not a single cut):
  for each percentile p ∈ {0.50, 0.70, 0.85, 0.95} of edge weights, build G_s(p).
  This is the persistence parameter analogue.

STEP 3. Build the flag (Vietoris-Rips-style) clique complex X_s(p). Library: gudhi (Python) or
  TopoNetX. Triangles are 2-simplices iff all 3 pairs co-interact above threshold; tetrahedra
  similarly. Cap dimension at k=3 (computational tractability + biological interpretability:
  cliques larger than 4 rare in animal data).

STEP 4. Compute Hodge Laplacians L_0, L_1, L_2 of X_s(p). Library: HodgeLaplacians (tsitsvero,
  github.com/tsitsvero/hodgelaplacians) or TopoNetX. L_k = B_{k+1} B_{k+1}^T + B_k^T B_k where
  B_k is the k-th boundary matrix.

STEP 5. Betti numbers: B_k(s,p) = dim ker(L_k). (Equivalently, rank deficiency.)

STEP 6. Per-stage Betti trajectory: B_k(s) := median over p of B_k(s,p), with bootstrap CI.

STEP 7. Test the proposition. Compute D_1 := max_s B_1(s) - min_s B_1(s) for each species.
  Permutation null: shuffle stage labels within species, recompute D_1, repeat 1000x.
  If observed D_1 exceeds 95% of null draws *and* sign of trajectory matches juvenile-peak
  prediction, accept G1 for that species. Compare species-level outcomes (transition-exhibiting
  vs non-exhibiting) by Fisher's exact.

STEP 8. (Stretch) Hodge-decompose interaction-flow signals on edges into harmonic + gradient
  + curl components. Schaub-Benson-Horn-Lippner-Jadbabaie (2020 SIAM Rev) framework. The
  harmonic component is what survives both div=0 and curl=0 — the genuinely cyclic
  cohomological signal.

FALSIFIABILITY: if across all four transition-exhibiting species, D_1 sits inside the
  permutation null (juvenile-stage B_1 indistinguishable from adult-stage), the proposition is
  refuted — sociality transitions do not have a cycle-content signature.
```

Input shape: edge-list with O(10^4-10^6) rows depending on species. Output shape: 6-row table (3 Betti numbers × 2 statistical-significance flags) per species per stage.

### D. Priority citations (PDF-verified)

1. **Wild, Alarcón-Nieto & Aplin (2024).** "Data for: Social network data in wild great tits during ontogeny." Dryad, DOI `10.5061/dryad.x95x69ps8`. **VERIFIED via Dryad landing page.** *The data target.*
2. **Turner, Bills & Holekamp (2018).** "Ontogenetic change in determinants of social network position in the spotted hyena." *Behav Ecol Sociobiol* 72(1):11, DOI `10.1007/s00265-017-2426-x`. **VERIFIED via PubMed / SpringerLink summary.** *The three-stage stratification used.*
3. **Schaub, Benson, Horn, Lippner & Jadbabaie (2020).** "Random Walks on Simplicial Complexes and the Normalized Hodge 1-Laplacian." *SIAM Review* 62(2):353–391, DOI `10.1137/18M1201019`. **VERIFIED via SIAM Review listing.** *Methods anchor.*
4. **Iacopini, Foote, Fefferman, Derryberry & Silk (2024).** "Not your private tête-à-tête: leveraging the power of higher-order networks to study animal communication." *Phil Trans R Soc B* 379:20230190, DOI `10.1098/rstb.2023.0190` (arXiv:2309.03783). **VERIFIED via arXiv + Royal Society listing.** *Field's only ASNA-adjacent simplicial-complex paper to date.*
5. **Topaz, Ziegelmeier & Halverson (2015).** "Topological data analysis of biological aggregation models." *PLOS One* 10(5):e0126383, DOI `10.1371/journal.pone.0126383`. Verified via lit review prior; bridge case for biological-TDA precedent (flocks/swarms, not ontogeny).
6. **Woodman, Gokcekus, Beck, Green, Nussey & Firth (2024).** "The ecology of ageing in wild societies." *Phil Trans R Soc B* 379(1916):20220464, DOI `10.1098/rstb.2022.0464`. **VERIFIED via PMC.** *Framing review.*
7. **Wee & Xia (2022)** persistent Laplacians on biomolecules — closest biological-Hodge precedent. *Sci Rep*. Citation **unverified at the volume/page level** in this scoping; user should resolve before citing in a paper.

### E. Load-bearing risk

**The likely failure mode:** Animal social network data is heavy-tailed in edge weight and sparse in higher-order structure. Real triangles (genuine 3-way associations all-pairwise-elevated) may be rare enough at stage-restricted subsets that B_2 is trivially zero for all species/stages, and B_1 (cycle content) is dominated by sampling thresholds rather than biology. If the threshold sweep in STEP 2 shows B_k values that *track the threshold p* rather than *track the stage s*, the spike has measured an artefact of edge-weight tail behaviour, not a biological signal. This is mitigated by (a) within-species statistical contrasts that hold p fixed, (b) the permutation-null in STEP 7 which controls for it, and (c) the multi-species comparison which would be more vulnerable if real but is also more falsifying-power. Honest possibility: the spike runs, the Betti numbers are flat and threshold-driven, and the answer is "Hodge on raw ASNA is not the right lift; weighted-simplicial-Laplacian on signed flow fields would be."

---

## Gap #2 — Base × fibre decomposition of multilayer animal social networks

### A. The gap, as testable proposition

**Proposition (G2):** A multilayer animal social network with K interaction-type layers L_1...L_K (play, agonism, affiliation, grooming, mating) over a node set V admits a useful fibre-bundle factorisation iff there exists a base space B (life-history-stage manifold, kin-graph, or spatial habitat partition) and a projection π: V → B such that the multilayer adjacency tensor A[i,j,k] factors as π-pulled-back base structure × fibre-localised perturbation, with a residual that is statistically smaller than the layered tensor itself. **Concrete operational form:** test whether π(V) recovers life-history stage *better than chance* under unsupervised spectral coclustering of the multilayer tensor. **Refuted if** the spectrum of the supra-Laplacian (Sola, Romance et al. 2013 / De Domenico et al. 2013) shows no clean separation between intra-base and intra-fibre eigenvalue regimes.

### A.i. Why fibre-bundle, not just multilayer

Existing multilayer ASNA (Silk et al. 2018; Finn et al. 2019) treats interaction-type layers as parallel networks with inter-layer couplings. A fibre-bundle framing is stricter: it asserts a *base space B* with intrinsic geometry (e.g., the totally-ordered life-history-stage manifold {0, 1, 2, 3, 4} with adjacency only between consecutive stages, or a kin-graph as a tree) and asks whether the multilayer structure is *equivariant* with respect to base-space transformations. This is testable; "multilayer" alone is not.

### B. Accessible datasets for first pilot

**Primary candidate: Same Wytham/Wild 2024 great tit dataset (Gap #1's primary).**

- Multilayer reconstruction available: RFID co-presence ≠ a single relationship; this dataset's per-week aggregations could be split into "siblings-only," "parent-tracking," and "non-kin peer" layers using the included nest-box pedigree. *Three* natural layers from one observation modality.

**Primary alternative: Pinter-Wollman / Carbone & Pinter-Wollman ant or marmot multilayer datasets.**

- Wey & Blumstein (2010) marmot data is in supplementary of *Animal Behaviour* 79(6):1343–1352, DOI `10.1016/j.anbehav.2010.03.008`. Lit-review-cited; redistribution status check pending. Has affiliation + agonism layers.

**Secondary candidate: Sosa et al. (2020) ANTs R package companion datasets.**

- *Sci Rep* 10:12507, DOI `10.1038/s41598-020-69265-8`. Package: github.com/SebastianSosa/ANTs. Several worked-example multilayer datasets for chimps, macaques, baboons. License of bundled data uncertain; needs check.

**Speculative tertiary: Hare et al. bonobo cooperative-task experiments (2007).**

- *Current Biology* 17(7):619-623. Counter-example anchor for the proposition; but individual-level interaction data not obviously available as a network-shaped dataset. Likely needs author contact. Mark **unconfirmed**.

### C. First-spike protocol sketch

```
INPUT: multilayer interaction tensor A[i, j, k] for i,j ∈ V (individuals), k ∈ {1..K} layers
       (play, agonism, affiliation, ...).
INPUT: candidate base-space partition functions π_α: V -> B_α for candidates α ∈ {life-stage,
       kin-class, spatial-territory}.

STEP 1. Build the supra-Laplacian L_supra of the multilayer network. Block-diagonal layer
  Laplacians + inter-layer coupling identity blocks scaled by ω. Standard reference: De Domenico
  et al. 2013 "Mathematical Formulation of Multilayer Networks" Phys Rev X 3:041022.

STEP 2. Spectral decomposition of L_supra. Compute the first ~50 eigenvectors. Plot the
  eigenvalue gap structure.

STEP 3. For each candidate π_α, define the *base-quotient* graph: G_α has nodes B_α, edges
  weighted by mean inter-block interaction across all layers. Compute L(G_α) and its
  eigenvalues.

STEP 4. Fibre extraction. For each base-block b ∈ B_α, restrict the multilayer tensor to
  V_b := π_α^{-1}(b). This gives a stack of "fibre tensors" F_b[i, j, k] over base point b.

STEP 5. Test base-fibre factorisation. Compute:
   R_α := || A - (π_α^* L_base ⊗ F_avg) ||_F / || A ||_F
  where F_avg is the average fibre tensor and the tensor product is the natural pullback
  along π_α. R_α near zero means π_α is a *good* base; near 1 means π_α is no better than
  a random partition.

STEP 6. Null comparison. Compute R for 100 random partitions of V into |B_α|-many blocks.
  Empirical-p-value: where does R_α fall in the null distribution?

STEP 7. Cross-species: repeat for ≥3 species (great-tit ontogeny base / marmot kin base /
  bonobo non-base). The conjecture is that *life-history-stage* is a good base for
  transition-exhibiting species but a poor base for bonobos (where the relevant base, if
  one exists, would be coalition-membership not age).

STEP 8. (Stretch) If a base is identified, examine the fibre cohomology — the residual
  variation of F_b across b that does NOT factor through the base. This is the
  "purely-fibre" signal that the bundle structure does not capture.

FALSIFIABILITY: if every candidate π_α (including life-stage, kin, territory) has R_α
  indistinguishable from random partition, no base-fibre decomposition is supported by the
  data. Reject G2.
```

Input shape: multilayer tensor of shape |V| × |V| × K, K ∈ {2-5}. Output shape: per-candidate-base scalar R_α + p-value.

### D. Priority citations (PDF-verified)

1. **Silk, Finn, Porter & Pinter-Wollman (2018).** *Trends in Ecology & Evolution* 33(6):376–378, DOI `10.1016/j.tree.2018.03.008`. **VERIFIED via PMC PMC5962412.** *The conceptual ASNA-multilayer formulation.* (Note: prior lit review's DOI was wrong; corrected here.)
2. **Finn, Silk, Porter & Pinter-Wollman (2019).** "The use of multilayer network analysis in animal behaviour." *Animal Behaviour* 149:7-22, arXiv:1712.01790. **VERIFIED via arXiv.** *The full methods companion.*
3. **De Domenico, Solé-Ribalta, Cozzo, Kivelä, Moreno, Porter, Gómez & Arenas (2013).** "Mathematical Formulation of Multilayer Networks." *Phys Rev X* 3:041022. Citation from training data; supra-Laplacian formalism standard reference. User should re-verify DOI/volume before any external publication.
4. **Sosa, Sueur, Puga-Gonzalez & Poisot (2021).** "Network measures in animal social network analysis: their strengths, limits, interpretations and uses." *Methods Ecol Evol* 12(1):10-21, DOI `10.1111/2041-210X.13366`. **VERIFIED via Wiley/Methods Ecol Evol.** *Field baseline of network-metric vocabulary.*
5. **Sosa, Puga-Gonzalez, Hu, Pansanel, Xie & Sueur (2020).** "ANTs R package." *Sci Rep* 10:12507, DOI `10.1038/s41598-020-69265-8`. **VERIFIED via PMC PMC7385643.** *Toolkit + companion data.*
6. **Wey & Blumstein (2010).** "Social cohesion in yellow-bellied marmots is established through age and kin structuring." *Animal Behaviour* 79(6):1343–1352, DOI `10.1016/j.anbehav.2010.03.008`. Citation from prior lit review; not re-verified in this scoping.
7. **Iacopini et al. (2024).** As in Gap #1. Higher-order network framing for ASNA.

### E. Load-bearing risk

**The likely failure mode:** Multilayer ASNA datasets are usually constructed *after-the-fact* from a single observation stream (focal-animal sampling, or RFID co-presence) by re-categorising the same event-record into layer types. The layers are therefore *not statistically independent* — they share underlying sampling decisions. The "base × fibre" residual R_α could measure the *non-independence between layers* (a constant offset) rather than any genuine base-space structure. To rule this out, the protocol would need a dataset with *genuinely separate observation modalities per layer* (e.g., RFID for affiliation + camera trap for agonism + GPS for ranging). I am not aware of such a dataset in the wild-population literature; this would have to be assembled from a captive-group study or via custodian collaboration. **Honest scenario:** the spike runs, R_α looks promising for life-stage base, but post-hoc the result is attributed to the shared-observation-pipeline artefact and the spike resolves to "we need a multimodally-observed dataset first." That itself is a useful finding — it tells the field what data is needed.

---

## Gap #3 — Representation-theoretic invariants computed identically across species (Hill-Bentley-Dunbar branching-ratio-≈-3)

### A. The gap, as testable proposition (with strong honest-negative caveat)

**Proposition (G3):** The consistent branching ratio ≈ 3 reported by Hill, Bentley & Dunbar (2008) across elephant, gelada, hamadryas, and orca multi-level societies — and replicated in human cognitive-network studies (5/15/50/150/500 layer structure, Mac Carron, Kaski & Dunbar 2016) — is **either** (i) a structure-constant trace artefact of a small representation acting on the underlying social interaction algebra, **or** (ii) a cognitive-bandwidth / time-budget artefact in which each layer is allocated ≈ 1/3 of the relationship-maintenance effort of the inner layer (Dunbar's own preferred explanation). G3 asks whether (i) is testable in a way that distinguishes it from (ii) — and the honest answer is that on present evidence, (ii) is the parsimonious explanation and (i) needs a much sharper sharpening before it earns a spike.

### A.i. The honest-negative scaffold (read first)

**Dunbar's own preferred explanation already exists:**

- Mac Carron, Kaski & Dunbar (2016) "Calling Dunbar's Numbers" *Social Networks* 47:151-155, arXiv:1604.02400, DOI `10.1016/j.socnet.2016.06.003` — explicitly attributes the 3× layer ratio to *time-budget allocation per relationship class*, fitted by mobile-phone-call frequency clustering. The 3× ratio falls out of "each next-outer layer gets 1/3 of the time-investment-per-individual of the layer inside it." That is a budget-allocation explanation, not a representation-theory explanation.
- Dunbar (2021) "Social complexity and the fractal structure of group size in primate social evolution" *Biological Reviews* 96:1889, DOI `10.1111/brv.12730` — same author re-grounds the fractal structure in cognitive-bandwidth (neocortex-size-correlated) constraints. Again a cost-allocation account.
- The ≈ 3 ratio is *not robust*: orcas already show 3.8 in Hill-Bentley-Dunbar 2008. If the ratio were genuinely Lie-algebraic (say, the index of an SO(3) ↓ SO(2) branching, or the dim of the adjoint of su(2) = 3), it would not drift to 3.8 for marine mammals.

**The Lie-algebra reading is intriguing but speculative.** No published derivation that I could verify connects a specific Lie algebra to the cross-species branching-ratio finding. A rank-2 Lie algebra (e.g., su(3)) has structure constants f^a_{bc} taking values in {0, ±1/2, ±1/√3, ...} depending on basis; none of these obviously delivers "3." The 3-fold dihedral group D_3 has order 6 and acts on a triangle, but is not the same object as a continuous branching ratio. **It is not at all clear that any concrete representation-theoretic object predicts 3.**

**Conclusion of honest-negative pass:** G3 *as stated* (Lie-algebraic structure-constant artefact predicting ≈3) appears to dissolve under inspection. The 3× ratio has a mundane and field-accepted cognitive-bandwidth explanation, and no published Lie-algebra link survives even informal sanity-checking against the orca = 3.8 datapoint. **However**, G3 can be reframed (next section) into a sharper question that *is* testable — about whether *humans show a different invariant* than other species, not about whether the invariant itself is Lie-algebraic.

### A.ii. The reframed proposition (G3′)

**Proposition (G3′):** For a structural invariant that is *not the branching ratio* but rather the **spectrum of the hierarchical-clustering modularity tree** (specifically, the largest few Laplacian eigenvalues of the dendrogram-induced quotient graph at each Horton-Strahler order), an identically-computed invariant on chimpanzee, bonobo, hyena, marmot, and human social datasets will show **bonobos as the outlier** and humans as **within-species range** of the great-ape group, not exceptional. Falsifiable by: if humans sit outside the species-cluster envelope (≥2σ in the multivariate invariant space), the "humans-are-not-exceptional" framing is refuted. If bonobos do *not* sit at the tolerance/cooperation end of the axis, the framing is also refuted (the predicted counter-example anchor must hold).

G3′ replaces "Lie-algebraic structure-constant" with "computed-identically Laplacian-spectral fingerprint" — a much more defensible methodology that retains the cross-species comparison the user's framing implies.

### B. Accessible datasets for first pilot

For G3′, the species set is the constraint, not the method. Need at least:

- **Chimpanzees:** Goodall / Gombe Stream Research Centre archives; data redistribution gated. **Mark unconfirmed.**
- **Bonobos:** Wamba / Kokolopori; even more gated. **Mark unconfirmed.**
- **Hyenas:** Holekamp CSVs (Gap #1 candidate, public).
- **Marmots:** Wey & Blumstein 2010 supplementary, lit-review-cited.
- **Humans:** Mac Carron, Kaski & Dunbar (2016) call-record clustering data is *not* publicly available; the underlying mobile dataset is custodian-gated. Alternative: published-network datasets like SocioPatterns RFID conferences (sociopatterns.org), but these are not multi-level in the Dunbar sense and conflate co-location with friendship.

**Realistic first-pilot would be:** hyena + marmot + great-tit (Gap #1's dataset) + simulated-human comparator built from Mac Carron et al.'s published *layer sizes* (5, 15, 50, 150) reconstructed as a hierarchical tree. This is **not a great experimental design** — it leans on simulated comparator for the headline cross-species species. Better-but-slower: arrange a data-use agreement with Gombe / Wamba consortia (timeline: months to years).

### C. First-spike protocol sketch (for G3′)

```
INPUT: weighted social network G = (V, E, w) per species.

STEP 1. Build hierarchical-clustering dendrogram D using a consistent linkage (average-linkage on
  edge-weight-distance) and a consistent cut algorithm. Library: scipy.cluster.hierarchy.

STEP 2. Read off Horton-Strahler orders on D. At each order h, compute the order-h *quotient*
  graph Q_h: contract all subtrees of order < h to single nodes, keep edges as weighted sums.

STEP 3. Compute the normalized Laplacian L(Q_h) for each h ∈ {1, 2, 3, 4}. Extract the first
  k=5 eigenvalues λ_1(h),...,λ_5(h).

STEP 4. Build the species fingerprint F_species = [λ_1(1), ..., λ_5(4)] — a 20-component
  vector. CRITICAL: this is *identically computed* across species; no per-species tuning.

STEP 5. PCA across species fingerprints. The user's conjecture predicts: humans (computed from
  whatever proxy is available) sit within the great-ape cluster; bonobos are PC-1-distant
  in the tolerance-direction.

STEP 6. Hypothesis test: against a permuted-species null (shuffle species labels), is the
  bonobo-distance significantly above null? Is the human-position within-cluster?

STEP 7. Report failures honestly. If the human comparator is too synthetic to be credible
  (which it likely is on a first pilot), document this and gate the conclusion: "result is
  conditional on real human data being acquired."

FALSIFIABILITY: if bonobos sit *with* chimpanzees in the fingerprint space rather than as
  outliers, the user's tolerance-counter-example framing is refuted at the methodological
  level. If humans sit *outside* the great-ape envelope, the humans-not-exceptional framing
  is refuted.

NOT-A-FALSIFICATION: if the branching ratio comes out close to 3 across species, that does
  not validate the Lie-algebra reading — the cognitive-bandwidth explanation already accounts
  for it.
```

Input shape: per-species edge-list. Output shape: 5-row × 20-column species × fingerprint matrix + PCA loadings.

### D. Priority citations (PDF-verified)

1. **Hill, Bentley & Dunbar (2008).** "Network scaling reveals consistent fractal pattern in hierarchical mammalian societies." *Biol Lett* 4(6):748-751, DOI `10.1098/rsbl.2008.0393`. **VERIFIED via PubMed + Wikidata Q28755915.** *The branching-ratio source.*
2. **Mac Carron, Kaski & Dunbar (2016).** "Calling Dunbar's numbers." *Social Networks* 47:151-155, DOI `10.1016/j.socnet.2016.06.003`, arXiv:1604.02400. **VERIFIED via arXiv + ScienceDirect listing.** *The cognitive-bandwidth alternative explanation — primary honest-negative anchor.*
3. **Dunbar (2021).** "Social complexity and the fractal structure of group size in primate social evolution." *Biol Reviews* 96(5):1889, DOI `10.1111/brv.12730`. **VERIFIED title via Wiley listing; abstract paywalled, citation unverified at full-content level — paywalled.**
4. **Hare, Melis, Woods, Hastings & Wrangham (2007).** "Tolerance allows bonobos to outperform chimpanzees on a cooperative task." *Current Biology* 17(7):619–623, DOI `10.1016/j.cub.2007.02.040`. Lit-review-cited; not re-verified in this scoping. *The bonobo-counter-example anchor.*
5. **Newman (2006).** "Finding community structure in networks using the eigenvectors of matrices." *Phys Rev E* 74:036104, DOI `10.1103/PhysRevE.74.036104`, arXiv:physics/0605087. **VERIFIED.** *The spectral-modularity baseline G3′ leans on.*
6. **Snyder-Mackler, Burger, Gaydosh et al. (2020).** "Social determinants of health and survival in humans and other animals." *Science* 368:eaax9553, DOI `10.1126/science.aax9553`, PMID 32439765. **VERIFIED.** *The cross-species health-and-sociality synthesis — establishes that identically-computed cross-species comparison is methodologically respectable.*
7. **Brent, Franks, Foster, Balcomb, Cant & Croft (2015).** "Ecological knowledge, leadership, and the evolution of menopause in killer whales." *Current Biology* 25(6):746-750. Lit-review-cited (orca natal-philopatry counter-anchor); not re-verified in this scoping.

### E. Load-bearing risk

**The likely failure mode is already named in section A.i above:** G3 as originally stated *appears to dissolve under closer look*. The branching ratio ≈ 3 has a well-published cognitive-bandwidth explanation from the field's own primary author (Dunbar himself), and no published derivation connects it to a Lie algebra. The orca = 3.8 datapoint argues against any *strict* representation-theoretic invariant. **The reframed G3′ is testable but expensive** — it depends on getting real chimpanzee and bonobo network data from custodian-gated archives, and the cross-species comparison is the most demanding logistic of the three gaps. Even if data acquisition succeeds, the result is most likely to be "humans sit within great-ape envelope on a multi-spectral fingerprint, bonobos do anchor the tolerance end" — which is a useful finding but is closer to a *confirmation of the field's existing consensus* than a novel structural-decomposition result.

**Honest negative summary for Gap #3:** The Lie-algebra reading does not survive informal inspection; the testable reframe (G3′) is methodologically clean but logistically heavy and unlikely to surprise the field. **This is the gap most likely to be a research dead-end relative to the project's spectral-decomposition mission.**

---

## Which gap is most spike-able first?

**Ranking by tractability × signal-value:**

1. **Gap #1 (Hodge-Laplacian / Betti-number across ontogeny)** — **most spike-able**. Has a fully-public, well-labelled, ontogeny-stratified dataset already on Dryad (Wild et al. 2024 great tits) that the field has not analysed this way. The methods stack (gudhi, HodgeLaplacians, TopoNetX) is mature, Python-native, and pip-installable. The hypothesis is sharply falsifiable. The result will be novel regardless of sign — either Betti-trajectory differentiation exists and the field has a new methodology, or it doesn't and we learn that the threshold-sweep artefact dominates and weighted-flow Laplacians are needed. ~1-2 week spike for a competent topology-and-Python practitioner with the dataset already in hand.

2. **Gap #2 (Base × fibre decomposition)** — second-most spike-able, but with a substantive data-quality risk. The supra-Laplacian framework is mature (De Domenico et al. 2013), candidate datasets exist, but the "shared-observation-pipeline" failure mode is real — the spike might run cleanly and produce a result that turns out to be measuring sampling artefact rather than biology. A defensible spike would still surface that finding, but it's a less crisp falsifier than Gap #1. ~2-3 week spike; runs second.

3. **Gap #3 (Representation-theoretic / branching-ratio)** — **least spike-able and partially dissolved under inspection**. The original Lie-algebra framing does not survive sanity-checking. The reframed G3′ is testable but logistically expensive (cross-species data acquisition is months-to-years), and the predicted result is closer to consensus-confirmation than novel structural insight. Recommend deferring G3 until either (a) Gap #1 or #2 surface a representation-theoretic structure organically, or (b) cross-species data access is independently arranged for some other project. **This is the honest-negative outcome of the scoping.**

**Recommendation:** spike Gap #1 first, with the Wild et al. 2024 Dryad great-tit dataset. If it produces a clean cross-stage Betti trajectory in the predicted direction, the spike is a clean win and Gap #2 becomes the natural follow-up (now with at least one validated topological methodology already in the project's toolbox). If Gap #1's result is null or threshold-driven, that itself is a publishable methodological-limit finding, and the project pivots to either Gap #2 directly or to the weighted-Laplacian extension the failure mode would point at.

---

**Discipline notes for this scoping:**

- No MVP framing used. Each protocol is the protocol that would settle the proposition, not a "minimal first cut."
- No lineage claims; the spectral-decomposition methodology is cited technically, not editorialised on inheritance.
- 2020+ citations PDF-verified where reachable; paywalled sources flagged as such.
- Two citation corrections vs prior lit review (Silk et al. DOI; Turner et al. authorship) documented in header.
- Gap #3 honestly negative: the Lie-algebra reading does not survive close inspection. This is logged as a finding, not buried.
- Dual-use: animal-social-network methodology has no security-adjacent application I can identify. No defensive-scope concern.
