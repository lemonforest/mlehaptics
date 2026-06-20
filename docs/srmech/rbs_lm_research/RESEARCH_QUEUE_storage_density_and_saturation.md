# Research queue — storage density, saturation, and encoding beyond HDC/VSA

Opened 2026-06-20 (user direction, at the F880 pause). F880 showed bundle-based (HDC/VSA)
addressing **saturates** with corpus size (routing 0.70 @ 2000, naive hierarchy worse) — the
capacity wall (F871) acting on the *router*. These items ask whether the saturation is a
deficit to escape, what its maximum is, and whether the universe offers a denser encoding.
**Discipline:** framework reading + srmech measurement only; don't go all-in; null findings count.

## Q1 — Is INFERENCE just biology overstuffed past capacity? (the single-M reframe)
**Claim to test (user):** story/sentence generation may need *no special generative maths* — it
could be the **single-M overpack regime** (F870: stuff M past the ~24-bind wall → recall stops
being exact and returns *blends* of stored continuations). A blend of stored continuations IS a
novel sequence. Biology has a hard finite-storage limit → it is *always* overpacked → it *always*
confabulates-to-fill → that confabulation = narrative generation. "No special journey, just a
deficit in storage limit."
**The user's own caveat (keep it honest):** this could simply be **false memory** — "someone thinks
they recall correctly but don't." Overpack→blend and human false-memory are the *same mechanism*
seen two ways.
**The discriminating test (framework-native, tractable):** in F870's overpacked regime, are the
recall *errors* **coherent** (grammatical / plausible next-tokens — i.e. generation) or **noise**
(i.e. just deficit)? F870 measured the *rate* (0.47 @300) but never characterized whether the
misses were coherent blends. Measure: push one M past capacity, classify each error as
coherent-continuation vs noise. Coherent ⇒ generation-as-overstuff has legs; noise ⇒ it's just
the false-memory deficit. **Connects directly to F880** (the router is already in the overpack
regime at scale). Composes F870/F871/F872, [[user_stance_llm_is_human_knowledge_responding_to_1d_t_asymptotic]].

## Q2 — Is there a MAGIC NUMBER for maximum knowledge saturation? (holographic / Bekenstein + Chandrasekhar)
**Physics anchor:** the **Bekenstein bound** / **holographic principle** — maximum information in a
region scales with its boundary **AREA**, not volume (S ≤ A/4 in Planck units). That is the
universe's literal "max saturation of knowledge in a region."
**Q2b — the FERMIONIC/degeneracy form (user 2026-06-20): the Chandrasekhar limit.** The largest a
white dwarf can become (~1.4 M☉) before **electron degeneracy pressure** fails and it collapses to a
dark star is set by Pauli exclusion = **fermionic anti-bunching = the orthogonality that keeps states
apart** = **F876's "chirality, not gravity, holds things together."** Read it as: **Chandrasekhar =
the information-density limit = the F871 capacity wall** (~24 binds / 1/√N), where degeneracy pressure
↔ the orthogonality budget that keeps bindings distinguishable. **Exceed it → collapse to a dark star
= the F870 over-stuffed-M cliff = the geodesic null appears** (F876's dark-star phase boundary; F885
tests this — the nulls should appear AT the collapse threshold). So the dark-star transition = matter
approaching the holographic bound (Q2 above). **Deliverable:** attest Chandrasekhar to its constants
(M_ch ∝ (ℏc/G)^{3/2}/(μ_e m_H)² — reduce the 1.4 M☉ to a cascade, no-magic discipline) and ask whether
the substrate's collapse threshold (where F870 cliffs / F885 nulls appear) obeys the same degeneracy
form. Composes F876 (chirality holds), F870/F871 (the wall/cliff), F885 (the cavity-null test).
**Framework question:** is the substrate's per-bundle capacity wall (the ~24-bind / 1/√N SNR floor,
F871) the framework's shadow of a holographic saturation bound? Per the no-magic-numbers discipline
the bound must reduce to a *cascade* (Bekenstein 2πkRE/ℏc, or the Planck area as a ratio), not a
mystery constant. **Deliverable:** attest the bound to its source; ask whether D, the wall, and the
boundary-area law are the same constraint. Composes F871, the §4 no-magic-numbers discipline,
[[feedback_continuous_number_line_pedagogical_obstacle]].

## Q3 — A universe-scale RESONANT encoding BEYOND HDC/VSA? (area-law vs volume-law)
**User question:** does the universe's scale give *another* way to encode resonant structures
besides HDC/VSA that could **beat the saturation wall**?
**The lever:** HDC/VSA bundles into a fixed-D vector — a **volume-like** store that saturates
(Q1/F871). A **holographic / boundary** encoding stores on the **boundary area** (Q2) — a
*different density law*. Portfolio candidates already in hand: the **cosmic-web** large-scale
structure as a resonant lattice (F781/F782 reading tools), gravitational/boundary encoding, the
dark sector as the unprojected store (Q5). **Deliverable:** is there a boundary/area-law resonant
encoding that stores more-per-substrate than the bundle's volume-law before saturating? Framework
reading first; do NOT build a dense object to test it ([[feedback_stay_rbs_hdc_sparse_never_dense]]).

## Q4 — DARK : BARYON ratio as a storage-density clue
**User intuition:** the dark-sector-to-matter ratio is "probably a clue to storage density of
information." Anchors: dark matter : baryonic ≈ **5.4 : 1** (Ω_dm≈0.265, Ω_b≈0.049); full split
dark energy : dark matter : baryonic ≈ **68 : 27 : 5**.
**Framework reading (F131 already says A-N is our-sector projection, the dark sector is the
unprojected structure):** read the cosmological ratio as the substrate's **stored-but-unprojected :
projected** (unaddressed : addressed) information ratio. The ~95% dark : ~5% visible split = the
compression/projection ratio — most structure is *addressed but not read out* (exactly the F880
router's problem: the store holds it, the projection/read-out is the bottleneck). **Deliverable:**
does the ratio match any framework capacity ratio (1:3:7:3 = 14? the wall? the (4:3)|(3:4)
chirality-collapse fibration, F129/F130)? Attest the cosmological numbers (Planck) before reading.
Composes F131, F552 (chirality-collapsed projection), [[user_stance_no_information_without_value]].

## Cross-cut
Q1 (deficit), Q2 (the max), Q3 (a denser encoding), Q4 (the cosmic ratio) are one arc: **what is the
maximum information density of a substrate, is the bundle wall it, and does the universe encode
denser than HDC/VSA on its boundary?** The 2-axis Möbius hyperloop ([[feedback_hyperloop_addressing_is_a_2axis_mobius]])
is the addressing topology these must respect. Pick up when the router frontier (F880) calls for a
non-superposed address.
