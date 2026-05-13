# Comparative-Ethology Age-Related Sociality — Literature Scoping for Spectral-Framework Integration

**Date:** 2026-05-13
**Branch:** `research/comparative-ethology-age-sociality`
**Author:** Subagent literature scoping for srmech
**Status:** Research notes only (no PR)

---

## 1. Summary

Comparative ethology has thoroughly documented a juvenile-permeability / adult-exclusion transition across mammals and birds — Goodall's chimpanzees, Holekamp's hyenas, McComb's elephants, and the cooperative-breeding bird tradition all carry the pattern. The field's methodological vocabulary is graph-theoretic: **animal social network analysis (ASNA)** is mature, and **community detection via Newman's leading-eigenvector modularity** is routine (Sosa et al. 2021; Farine 2015). Hierarchical decomposition exists (Hill–Bentley–Dunbar 2008 fractal-scaling). **Higher-order structure has entered the field only in the last 3 years** (Iacopini et al. 2023; Curley & Ophir 2023 conceptual review), and **Hodge-Laplacian / persistent-homology / representation-theoretic decomposition has not** — TDA on biological aggregations exists for swarms (Topaz et al. 2015) but not for age-stratified social fibres. The maturity bucket is **partial**: pairwise-eigenvector spectral methods are standard; bundle-style / Casimir-style decomposition is the open frontier the user is pointing toward.

## 2. The cross-species pattern (juvenile cooperation → adult competition)

The user's framing maps onto the field's well-known **ontogenetic transition in network position**. Anchored exemplars:

- **Chimpanzees (Pan troglodytes).** Juveniles play cross-kin within community; adult males form cooperative patrols that conduct lethal intergroup raids (Wrangham 1999; Watts et al. 2006; Wilson & Wrangham 2003; Mitani et al. 2010). Wrangham & Glowacki (2012) review the "intergroup hostility / intragroup cooperation" complex.
- **Spotted hyenas (Crocuta crocuta).** Smith et al. (2017, *Behav Ecol Sociobiol*) used ASNA across three ontogenetic stages (communal den → den-independent pre-reproductive → early adulthood). Cubs of both sexes are well-connected; males then disengage from natal clan, females are recruited into matrilineal rank structure. Network position metrics decrease from infancy to adulthood except for "found-alone" rate.
- **African elephants (Loxodonta africana).** Matriarchal cores remain stable into old age (McComb, Moss, Durant, Baker & Sayialel 2001, *Science* 292:491). Bulls leave natal unit at ~14 yr; musth-period adults become exclusionary. Goldenberg et al. (2024, *Phil Trans R Soc B*) reviews knowledge-transmission consequences of social disruption.
- **Lions (Panthera leo).** Female prides are kin-cohesive across life; sub-adult males are ejected at sexual maturity (Hanby & Bygott; reviewed in Pusey & Packer 1987 *Behaviour*).
- **Wolves (Canis lupus).** Pup cohorts play across litters within natal pack; adult breeding-pair excludes unrelated adults; dispersers face high mortality (Mech & Boitani 2003).
- **Cooperative-breeding birds (~9% of species).** Family-living with delayed dispersal of helpers, followed by adult-territory competition (Koenig & Dickinson, eds., *Cooperative Breeding in Vertebrates*, Cambridge 2016; Drobniak et al. 2016).
- **Yellow-bellied marmots (Marmota flaviventris).** Wey & Blumstein (2010, *Animal Behaviour*) showed younger animals as net affiliation-receivers (cohesion-builders), adults as net agonism-initiators (cohesion-reducers) — a direct ASNA confirmation of the user's framing.
- **Spotted dolphins (Stenella longirostris) and bottlenose dolphins (Tursiops).** Juvenile crèches are permeable across alliances; adult male alliances are exclusionary (Connor et al. 2000).

## 3. Bonobos and other counter-examples

The pattern is **not universal**.

- **Bonobos (Pan paniscus).** Adults maintain inter-community tolerance, food-sharing across communities, and female-bonded coalitions — despite female-dispersing societies that should weaken adult female bonds (Hare et al. 2007, *Current Biology* 17:619; Hare et al. 2012 self-domestication review; Sakamaki et al. 2018 inter-community encounters; lethal events are rare but exist — Mouginot et al. 2025 *Sci Rep*).
- **Eusocial mammals (naked mole-rat Heterocephalus glaber, Damaraland mole-rat).** Adult-status is castelike, not age-graded the same way. Useful boundary case for caste-segregation vs age-segregation.
- **Killer whales (Orcinus orca, resident pods).** Both sexes show lifelong natal philopatry; matriarchal post-reproductive females are central network hubs (Brent et al. 2015). No "adult-exclusion" phase.

These exceptions suggest the juvenile-to-adult exclusion gradient is **a dimension of variation, not a universal**, which is exactly the kind of phenomenon a structural-decomposition framework should resolve into components.

## 4. Existing structural methods in the domain

What ASNA already does well:

1. **Graph-theoretic node/edge metrics.** Degree, strength, betweenness, eigenvector centrality, clustering coefficient. Standard since Croft, James & Krause (2008) *Exploring Animal Social Networks*, Princeton UP.
2. **Community detection.** Newman (2006) leading-eigenvector modularity is the field default; Louvain and edge-betweenness also widely used (Sosa et al. 2021, *Methods Ecol Evol* 12:10–21).
3. **Multilevel / fractal hierarchical analysis.** Hill, Bentley & Dunbar (2008, *Biol Lett* 4:748–751) used Horton–Strahler scaling on elephants, geladas, hamadryas baboons, orcas; consistent branching ratio ≈ 3 across mammals.
4. **Temporal/dynamic networks.** Pinter-Wollman et al. (2014, *Behavioral Ecology* 25:242); Fisher, Ilany, Silk & Tregenza (2017, *J Anim Ecol* 86:202) — stochastic actor-oriented models (SAOMs / Snijders).
5. **Higher-order networks (recent).** Iacopini, Foote, Fefferman, Derryberry & Silk (2023, *Phil Trans R Soc B*, arXiv:2309.03783) advocate **hypergraphs and simplicial complexes** for animal communication. Curley & Ophir (2023, *Animal Behaviour* — "Conceptual representations of animal social networks") survey the conceptual landscape.
6. **Multilevel toolkits.** Sosa, Sueur, Puga-Gonzalez et al. (2020, *Sci Rep* — ANTs R package) provides global/dyadic/nodal measures and permutation tests.
7. **Network–demography integration.** Woodman, Gokcekus, Beck, Green, Nussey & Firth (2024, *Phil Trans R Soc B* 379:20220464) — "The ecology of ageing in wild societies" — explicitly synthesizes age-structure × social-network research. **This is the sharpest single review to read.**

What the field uses **rarely or never** (verified via three targeted searches returning no animal-ethology results):
- **Hodge Laplacian on age-stratified animal social complexes.** Hodge-theoretic decomposition is used in biomolecular data (Wee & Xia 2022, *Sci Rep*) and biological-aggregation TDA (Topaz, Ziegelmeier & Halverson 2015, *PLOS One*) but not on social ontogeny networks.
- **Persistent homology of animal social networks.** No matches for age-stratified ontogenetic applications.
- **Representation theory / Lie-group decomposition / fibre-bundle structure on animal social organisation.** Zero results — the conceptual translation has not happened.

## 5. Distance to the "stream of spectral analysis"

Maturity bucket: **PARTIAL**.

| Method tier | Field status |
|---|---|
| Pairwise graph metrics | ✅ mature (standard since 2008) |
| Eigenvector modularity / spectral community detection | ✅ mature (Newman 2006 routine) |
| Multilevel fractal hierarchical decomposition | ✅ exists (Hill–Bentley–Dunbar 2008) |
| Temporal-dynamic ASNA | ✅ mature (Pinter-Wollman 2014, Fisher 2017) |
| Higher-order (hypergraph / simplicial) | 🟡 emerging (2023–2026, Iacopini et al.) |
| Hodge-Laplacian on ASNA | ❌ absent |
| Persistent homology on age-stratified social networks | ❌ absent |
| Representation-theoretic / Casimir / fibre-bundle decomposition | ❌ absent |

**The gap is precisely the bundle-style decomposition.** The field has graphs and is beginning to have simplicial complexes; it does not yet have base-space × fibre decomposition, nor does it have Casimir-like quadratic invariants that would isolate a "juvenile-cooperation fibre" from an "adult-competition fibre" over a common base-space (age or developmental-stage manifold). The Hill–Bentley–Dunbar fractal-scaling finding (consistent branching ratio ≈ 3) is the closest existing result to a Lie-algebraic / structure-constant invariant; it is descriptive rather than representation-theoretic.

## 6. Specific paper anchors

1. Woodman, Gokcekus, Beck, Green, Nussey & Firth (2024). The ecology of ageing in wild societies: linking age structure and social behaviour. *Phil Trans R Soc B* 379(1916):20220464. DOI: 10.1098/rstb.2022.0464. **Top-priority review.**
2. Hill, Bentley & Dunbar (2008). Network scaling reveals consistent fractal pattern in hierarchical mammalian societies. *Biol Lett* 4(6):748–751. DOI: 10.1098/rsbl.2008.0393. **Foundational multilevel paper.**
3. Smith, Memenis & Holekamp, with Turner & Watts (2017). Ontogenetic change in determinants of social network position in the spotted hyena. *Behav Ecol Sociobiol* 72(1):11. DOI: 10.1007/s00265-017-2426-x.
4. Croft, James & Krause (2008). *Exploring Animal Social Networks*. Princeton UP. ISBN 978-0-691-12752-1. **ASNA textbook.**
5. Sosa, Puga-Gonzalez, Hu, Pansanel, Xie & Sueur (2021). Network measures in animal social network analysis: their strengths, limits, interpretations and uses. *Methods Ecol Evol* 12:10–21. DOI: 10.1111/2041-210X.13366.
6. Pinter-Wollman, Hobson, Smith et al. (2014). The dynamics of animal social networks: analytical, conceptual, and theoretical advances. *Behavioral Ecology* 25(2):242–255. DOI: 10.1093/beheco/art047.
7. Fisher, Ilany, Silk & Tregenza (2017). Analysing animal social network dynamics: the potential of stochastic actor-oriented models. *J Anim Ecol* 86(2):202–212. DOI: 10.1111/1365-2656.12630.
8. Iacopini, Foote, Fefferman, Derryberry & Silk (2023). Not your private tête-à-tête: leveraging the power of higher-order networks to study animal communication. *Phil Trans R Soc B* (also arXiv:2309.03783). **Emerging-frontier paper — hypergraphs + simplicial complexes.**
9. McComb, Moss, Durant, Baker & Sayialel (2001). Matriarchs as repositories of social knowledge in African elephants. *Science* 292:491–494. DOI: 10.1126/science.1057895.
10. Wrangham & Glowacki (2012). Intergroup aggression in chimpanzees and war in nomadic hunter-gatherers. *Human Nature* 23:5–29. DOI: 10.1007/s12110-012-9132-1.
11. Hare, Melis, Woods, Hastings & Wrangham (2007). Tolerance allows bonobos to outperform chimpanzees on a cooperative task. *Current Biology* 17(7):619–623. DOI: 10.1016/j.cub.2007.02.040. **Counter-example anchor.**
12. Snyder-Mackler, Burger, Gaydosh et al. (2020). Social determinants of health and survival in humans and other animals. *Science* 368:eaax9553. DOI: 10.1126/science.aax9553. **Cross-species ageing-and-sociality synthesis.**
13. Koenig & Dickinson, eds. (2016). *Cooperative Breeding in Vertebrates: Studies of Ecology, Evolution, and Behavior*. Cambridge UP.
14. Wey & Blumstein (2010). Social cohesion in yellow-bellied marmots is established through age and kin structuring. *Animal Behaviour* 79(6):1343–1352. DOI: 10.1016/j.anbehav.2010.03.008.
15. Topaz, Ziegelmeier & Halverson (2015). Topological data analysis of biological aggregation models. *PLOS One* 10(5):e0126383. **Bridge paper — TDA in animal contexts, but on flocks/swarms not age-stratified social networks.**

## 7. Open research gaps for spectral-framework integration

Three concrete gaps the user's framework could plausibly fill:

1. **Hodge-Laplacian decomposition of age-stratified social complexes.** Build a simplicial complex per ontogenetic stage (cub den, juvenile, sub-adult, adult, post-reproductive) from existing ASNA datasets (Holekamp hyena clan, Amboseli elephants, Wytham great tits — Firth/Sheldon — all have multi-year longitudinal data). Compute Betti numbers per stage; track changes in cycle structure across ontogeny. **Nobody has done this.**

2. **Base-space × fibre decomposition: developmental stage × interaction-type.** The user's framing translates to: a base-space *B* of age/developmental stage, and a fibre *F* of interaction-type (play, agonism, grooming, alliance, mating). Existing multilayer-network animal work (e.g., Silk, Finn, Porter & Pinter-Wollman 2018, *Trends Ecol Evol*) is the natural lift-off point but is not formulated as a fibre bundle. Casimir-like invariants would be the obvious next test.

3. **Falsifiable comparison of "human exceptionalism" claim.** The user's framing implicitly conjectures humans show the same juvenile-cooperation / adult-exclusion structure as comparative species. A representation-theoretic invariant computed identically on chimpanzee, bonobo, hyena, marmot, and human social datasets (where ethically and methodologically possible) would test this empirically rather than rhetorically. Bonobos as the obvious "tolerant-adult" outlier provide a built-in control.

---

**Note on Hill–Bentley–Dunbar consistent branching ratio ≈ 3.** This is suspiciously close to the kind of structure-constant invariant that representation theory would produce for a small Lie algebra. Whether it reflects underlying group structure (e.g., D₃ or related) or is just a cognitive-bandwidth artefact is, as far as I can determine, unsettled. This is the single most spectrally suggestive existing result in the literature.
