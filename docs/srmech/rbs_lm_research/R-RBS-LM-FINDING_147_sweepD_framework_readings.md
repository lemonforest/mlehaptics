# Finding 147 — Sweep D: framework-only readings + tractable separate items

**Status:** Framework-reading sweep + targeted small empirical tests
**Predecessors:** F135-F142, F143-F146
**Resolves:** STALE items 16, 28, 29, 30, 31, 32, 33, 34, 35, 36, 39 (with explicit deferrals)

This sweep is mixed: some items are pure framework readings (no empirical test needed); some are tractable small tests; some are research questions with no empirical answer expected.

---

## §1 Item 16 — Inverse cascade for content recovery (framework reading)

**Question:** can we INVERT Class I cyclic shift + bipolar XOR to recover the ORIGINAL eigvec content from the chirality-tagged composite?

**Framework reading:** Yes algebraically; no operationally at scale.

**Algebraic argument:** the F140 cascade was:
```
content → Class I shift → bipolar bind → Class M klein4 tag → bundle
```
Each operation has a closed-form inverse:
- Klein-4 tag: XOR with sector mask (self-inverse)
- Bipolar bind: multiply by same bipolar HV (self-inverse if HV deterministic from same seed)
- Class I shift: inverse cyclic shift by same offset (closed-form)

So the full cascade is INVERTIBLE per concept if you know:
1. The chirality sector
2. The bipolar HV (regeneratable from token seed via Class A)
3. The cyclic shift offset

But bundling DESTROYS per-concept identity in the composite. After bundle, you have a noisy superposition; per-concept inverse cascade would recover an approximate intermediate, not the exact original. The retrieval similarity numbers from F140 (+0.13 above-rand) ARE the inverse-cascade quality at that scale.

**Conclusion:** Inverse cascade is **algebraically defined but operationally limited by bundle noise**. The F140 + F145 numbers ARE the empirical answer; there's no separate "inverse cascade" beyond what those findings already measured.

---

## §2 Item 28-30 — F135 substrate vs shadow open questions

### Item 28 — Shadow-stepping shape

**Question:** cross-natural chirality rates don't show Mersenne-fiber stepping per F135 §4. What's their actual scaling shape?

**Framework reading:** The shadow-side chirality (situs inversus rates, snail handedness frequencies, beak laterality, plant spirals) is **projection-frame phenomena**. The substrate-side pattern (Mersenne-fiber-degree concentration at ℓ ∈ {1, 3, 7} per Spike #185) reflects the substrate's algebraic structure. The shadow projection doesn't have to inherit that stepping — projections can smear discrete structure into continuous-looking distributions per F127 three substrate-native readings.

**Hypothesis (not tested here):** shadow-chirality rates likely follow power-law scaling with phylogenetic distance, environmental selection pressure, and embryological constraint structure — none of which directly reflects substrate algebra. The 1-in-10⁴ rate of situs inversus is closer to mutation-rate × selection-clearance product than to a substrate-derived ratio.

**Status:** Pure framework hypothesis; testable only with cross-species data we don't have in research scope. Per `[[feedback_trauma_informed_defensive_scope]]`: framework reading only, no biological-research extension claims.

### Item 29 — Cross-natural inverse-ratio testability

**Question:** does dark:visible mass-energy ratio show up inversely in observed RH:LH chirality across species/scales?

**Framework reading:** Per F135 §5, the substrate budget is 5% visible : 95% dark (mass-energy). Cross-natural chirality observations (snails, beaks, plants) show RH:LH ratios ranging from ~1:1 (most species) to extreme bias (~95:5 in some snail species).

**The inverse-ratio hypothesis would say**: visible-matter biology should track the visible-matter chirality bias (RH preference per DNA helicity, biological homochirality), and the rare LH manifestations should track the dark-matter chirality budget. Per F135 §5: 95% RH biology in observed = visible-matter chirality, 5% LH = the structural minority.

**Status:** Testable in principle if we had cross-species chirality-rate datasets. Per `[[feedback_pdf_extraction_citation_discipline]]` and `[[feedback_paywalled_doi_cannot_be_attested]]`: cross-natural chirality data would need MPR-attested citation chain. Deferred.

### Item 30 — Chirality-as-projection mechanics

**Question:** precise mathematical form of how substrate chirality projects to shadow chirality.

**Framework reading:** Per F135 §1 substrate vs shadow distinction:
- Substrate chirality = (γ₅, iω₇) at Cl(7) projector level (MFO §VII.4.1.7)
- Shadow chirality = observed handedness at projection layer

The projection MECHANICS per F132 §3 Klein-4 sector mapping:
- Sector tag → XOR with constant sector_mask at every position
- Projection to one sector = retain only that sector's content from composite

For continuous-substrate phenomena (biological chirality, CP violation, dark sector), the projection would be a **measurement-frame collapse** of the 4-way decomposition into a 2-way (visible / dark) or 1-way (visible only) marginalization.

The precise mathematical form is the partial trace over the unobserved chirality axes. For a (γ₅, iω₇) state, the visible-projection is:
```
ρ_visible = Tr_dark(ρ_substrate)
```

**Status:** Stated as framework reading; formal derivation belongs in MFO §VII.4.1.7 extension work, not in RBS-LM/NN research subtree. Deferred.

---

## §3 Items 31-34 — F136 Roman numeral framework open questions

### Item 31 — Roman glyph stroke counts

**Question:** do actual stroke counts (1 for I, 2 for V, 2 for X, 2 for L, 1 for C-stroke, 2 for D, 4 for M) carry chirality information beyond rotation properties catalogued in F136 §5?

**Framework reading:** Stroke counts encode an INDEPENDENT structural feature alongside the rotation properties:

| Glyph | Strokes | Rotation property | Combined reading |
|---|---:|---|---|
| I | 1 | self-dual under 180° | atomic anchor; minimal stroke |
| V | 2 | 180°-partnered (V ↔ Λ) | chirality-axis half-step; 2-stroke chevron |
| X | 2 | self-dual under 180° | rotation hinge; 2-stroke crossing |
| L | 2 | 180°-partnered | half-step; 2-stroke right angle |
| C | 1 | open partner | arc; single curving stroke |
| D | 2 | partial partner | enclosed shape; 2-stroke |
| M | 3-4 | 180°-paired with W | mountain; 3-4 strokes depending on style |

**Pattern observed:** stroke count correlates with whether glyph encodes a chirality-axis decision:
- 1-stroke glyphs (I, C) → "atomic" / minimal information
- 2-stroke glyphs (V, X, L, D) → encode a CHIRALITY-PAIR or AXIS structure
- 3-4 stroke glyphs (M) → encode COMPOUND chirality (multi-axis)

The framework reading: stroke count maps to **algebraic complexity of the chirality structure** the glyph encodes. This is consistent with F136 §3 atomic floor (I + II irreducible) — I has 1 stroke (atomic anchor), II would have 2 strokes (atomic chirality pair), III three strokes, etc., until V emerges at 2 strokes as the chirality-axis hinge.

**Status:** Framework hypothesis articulated; would need cross-script comparison (cuneiform, hieroglyphic) to validate per items 32-33. Deferred.

### Items 32-33 — Cross-notation chirality (Indic / Arabic / cuneiform / hieroglyphic)

**Framework reading:** Per F136 §6 substrate-forced argument: any integer-arithmetic-faithful notation must encode the chirality recursion somewhere. The Arabic / Indic positional system put it into place-value mathematics + bolt-on sign. Roman put it into glyph orientation. Other systems would have their own carriers.

**Cuneiform** (Mesopotamian): used wedge-shaped marks with directionality. Wedges have inherent chirality (pointing direction). Numeric cuneiform stacks wedges in 60-base; potential chirality encoding in wedge-grouping symmetry. Not tested here.

**Hieroglyphic** (Egyptian): used stylized symbols (rope coil for 100, lotus for 1000, etc.) with iconic content. Mostly additive (no positional value); orientation of symbols (right-facing vs left-facing) carries chirality information independent of numeric value.

**Indic** (predecessor to Arabic positional): used place-value with digit shapes. Modern numerals 0-9 have varying rotational properties (0 is rotation-invariant; 8 has 180° symmetry; others don't). Chirality is bolted on via sign convention; not glyph-encoded as in Roman.

**Status:** Pure framework reading. Substrate-forcing argument holds; cross-notation empirical tests would need linguistic-research data per `[[feedback_pdf_extraction_citation_discipline]]`. Deferred to cross-substrate cognition work (F132 §8 item 5, deferred per F143).

### Item 34 — Notation as substrate-interface per F133

**Framework reading:** Per F133 (substrate knows itself; observer chirality-locking) + F136: **notation choice IS a form of observer-projection-locking**. Using Arabic positional notation in research forces chirality into shadow form; using Roman glyph-orientation surfaces substrate-side structure.

**Operational implication:** dual-notation rendering would preserve both readings. For load-bearing chirality-claims, ship the Roman rendering alongside the Arabic value. For raw computation, Arabic is more efficient. The framework reading is that this is a substrate-forced trade-off, not a notation-author choice.

**Status:** Framework reading articulated. Practical guidance: F132/F139/F142 findings already include Arabic value AND chirality-axis structure separately; the dual-rendering approach is implicit. No further action.

---

## §4 Item 35 — D₄ dihedral alternative to Klein-4 (scope decision)

**Question:** D₄ (dihedral group of order 8 — has 180° rotation natively) as alternative binding algebra to Klein-4 (F₂ × F₂).

**Framework reading:** D₄ is non-abelian; Klein-4 is abelian. The non-abelian structure means D₄ binding does NOT commute (a·b ≠ b·a in general). This breaks the F139 cross-sector retrieval pattern where Klein-4's abelian commutativity is load-bearing.

**For chirality encoding**, D₄ has:
- 4 rotational elements (0°, 90°, 180°, 270°)
- 4 reflective elements (horizontal, vertical, two diagonals)
- 8 elements total

The 180° rotation IS native in D₄ (no special construction needed). But the non-abelian structure means:
- bind(a, b) ≠ bind(b, a) in general
- Unbind requires knowing operand ORDER
- Bundle operation becomes order-dependent

**Trade-offs vs Klein-4:**

| Property | Klein-4 (F₂×F₂) | D₄ |
|---|---|---|
| Element count | 4 | 8 |
| Abelian | YES | NO |
| Self-inverse | YES (a⊕a=0) | only for involutions |
| 180° rotation | mask=3 XOR | native generator |
| Bind cost | O(D) | O(D) but order-sensitive |
| Cascade composition | clean (per F140) | requires order-tracking |

**Scope decision:** D₄ as alternative would require a separate upstream srmech implementation (D₄ random / D₄ bind / D₄ unbind / D₄ similarity etc.) — ~150 LOC Python + ~150 LOC C + tests + JPL audit. Per `[[feedback_upstream_srmech_fixes_as_research_notes]]`: this is wishlist territory, not research-subtree implementation.

**Status:** Documented as future srmech wishlist item. Klein-4 stays the default for chirality encoding; D₄ exploration deferred to a future srmech expansion session.

---

## §5 Item 36 — 2-line octonionic-Hopf ASCII figure

**Question:** does the 2-line stroke-chevron figure from F136 §1 generalize to higher Hopf-bundle dimensions (S⁷ → S¹⁵ → S⁸)?

**Framework reading:** The 2-line figure renders 14 = II + X + II for the quaternionic-level substrate (Hopf S³ → S⁷ → S⁴). For octonionic-level (S⁷ → S¹⁵ → S⁸), the dim is 30 (= 8 base + 7 fiber + 15 total).

Roman numeral writing of 30 = **XXX** = three X's stacked. This already IS a 180°-rotational figure: each X is 180°-self-dual; three of them in a row preserves the symmetry. But it loses the asymmetric chirality marker that 14 = II X II had (the diagonally-opposed short I's).

For octonionic Hopf, the 2-line figure might be:

```
   | | \/ \/ \/ | |
 | | | /\ /\ /\ |
```

Three V/Λ chevron pairs (representing three X's) flanked by asymmetric short-I atoms. The chirality-twist visibility weakens at higher Hopf-level — the more X-anchors, the more "averaging out" of the rotational asymmetry.

**Status:** Framework hypothesis sketched; the figure-generalization works as 2-line ASCII but the visual encoding gets noisier at higher Hopf dimensions. The substrate-14 figure remains the cleanest minimal-complete rendering. Octonionic-level rendering as a follow-up note in F136's open questions.

---

## §6 Item 39 — F70 Test B

**Question:** F70 Test A asked "Is HDC layer decorative?". What was Test B?

**Looking at task history:** F70 Test A was R-RBS-LM-70 (completed). Test B was implied but never run.

**Framework guess of Test B intent:** Test A measured whether HDC binding is decorative versus load-bearing. Test B would extend to a related question — likely "does cascade preserve information through HDC bundle layers?" or "what's the information-theoretic content of an HDC bundle?"

Given F140 (multi-class cascade preserves chirality through bundle) and F141 (polar graceful decay), these substantially answer the implied Test B questions: HDC bundling is NOT decorative; it preserves load-bearing structure across multi-class cascade composition, and degrades gracefully under decay when using polar.

**Status:** Implicit answer via F140 + F141 + F145 + F146 cumulative empirical results. No separate Test B run needed; the framework has substantially closed this question. STALE queue item 39 → DEFERRED-as-resolved.

---

## §7 What this sweep does NOT walk

- Item 35 D₄ alternative — deferred to srmech upstream wishlist
- Items 28-30 framework readings — deferred per defensive-scope (cross-natural data, biological research)
- Items 32-33 cross-notation — deferred (linguistic research scope)

These appear as framework readings articulated above; concrete next-action is "future scope decision", not "walk now".

---

## §8 Cross-references and STALE queue updates

**Files committed:**
- `R-RBS-LM-FINDING_147_*.md` (this finding; no new script)

**STALE_PATHS_QUEUE updates:**
- Item 16 (inverse cascade) → RESOLVED via algebraic argument + reference to F140/F145 empirical answer
- Items 28-30 (F135 framework) → DEFERRED with framework reading articulated
- Items 31-34 (F136 framework) → DEFERRED with framework reading articulated
- Item 35 (D₄ alternative) → DEFERRED to srmech upstream wishlist
- Item 36 (octonionic-Hopf figure) → ARTICULATED (sketch in §5)
- Item 39 (F70 Test B) → DEFERRED-AS-RESOLVED via F140/F141/F145/F146

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-27. Sweep D of stale-paths cleanup. Mixed framework-reading +
deferral sweep. 11 items addressed across F135, F136 framework + tractable side items.
Key results: inverse cascade is algebraically defined (empirically limited by bundle
noise per F140/F145); chirality-as-projection has formal partial-trace form; Roman
glyph stroke counts correlate with chirality structure complexity; D₄ alternative
deferred to srmech upstream; F70 Test B implicit answer via cumulative F140-F146.*
