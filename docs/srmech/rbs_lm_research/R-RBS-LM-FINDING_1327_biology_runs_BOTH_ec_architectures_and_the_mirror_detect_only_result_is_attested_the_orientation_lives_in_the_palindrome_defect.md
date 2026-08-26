# F1327 — **biology runs BOTH error-correction architectures, and they are structurally different — which settles F1325's open question with more precision than we asked for.** Three targeted attested-research passes (topology / inversion+repair / reading machinery) return one convergent result: **Hopfield kinetic proofreading is ONE criterion applied twice** (buys sensitivity `ε → ε²` at an energy cost, adds *no* new witness), while **methyl-directed mismatch repair is two genuinely independent channels** — and its mismatch channel **detects but cannot correct** (*"MutS and its eukaryotic homologs do not perform strand discrimination"*). The disambiguating bit rides a **chemically separate, non-sequence channel** (Dam hemimethylation), and the recognition site `GATC` **is itself a perfect palindrome** — so the site carries *no* orientation at all. That is F1325's mirror result and F1326's borrowed-anchor result, attested in a real system. Second convergent result: across every inversion/recombination mechanism, **orientation lives in the palindrome DEFECT**, not the palindrome — invertase crossover cores are *"never symmetrical"*, `dif` repeats are *"imperfect, not a perfect palindrome"*, and the shufflon gives the causal proof (**engineering the site symmetric UNLOCKED the wrong branch**). Third: `cwf_consistency_mod2` is not a coarse integer-`Lk` approximation — it is **exactly the single-strand-passage parity channel**, structurally blind to every type-II (ΔLk = ±2) event.

**User (2026-07-25):** *"what we're after now is this other mechanisms and machinary that don't normally surface when we talk about genome to augment our existing surface for srmech."*

Research by three targeted sub-agents (opus; the `sonnet`-alias ban respected). MPM discipline enforced in-brief: primary-source fetch, paywalled-DOI rejected, dataset licences recorded, textbook-vs-active flagged, mandatory *"could not attest"* section. **Everything below that is a number on our own data I re-verified myself.**

---

## 1 — the k=2 / k=3 question, answered `[ATTESTED]`
F1325 established that a perfect mirror **detects but cannot correct** (k=2 parity), and that correction needs a third independent read. Biology has both shapes and *keeps them distinct*:

| architecture | independent witnesses | what it buys |
|---|---|---|
| **Kinetic proofreading** (Hopfield 1974; ribosome) | **ONE** — the *same* criterion re-applied after an irreversible energy-dissipating step | sensitivity `ε → ε²`. **Not** a new evidence source. |
| **Methyl-directed MMR** (E. coli MutS/MutL/MutH) | **TWO** — (a) strand-vs-strand disagreement, (b) hemimethylation state | detection **and** correction |

The ribosome confirms the first mechanistically: initial selection and proofreading both act through *the same* induced-fit coupling of the decoding centre (Pape/Wintermeyer/Rodnina 1999, PMC1171457). **More stages ≠ more witnesses.**

And the second is F1325's exact shape:
- `mismatch(i)` — a **symmetric** predicate. Detects; **cannot say which strand is wrong**.
- `mark(j)` — hemimethylation at the nearest `GATC`. A **separate physical channel** with its own timescale.
- **`GATC` is a perfect palindrome.** The site is symmetric and carries no orientation; *all* the asymmetry is in the mark.

> **The mirror detects. Correction arrives on a channel the mirror cannot see.** That is F1326's "the 4 comes from the perspective" in a wet system: the symmetric object plus a component supplied from outside it.

**Honest**: the "two distinct information sources" split is the researching agent's structural reading of attested mechanism, not a quoted claim. And the layers **do not compose multiplicatively in vivo** — in a proofreading-defective *E. coli*, removing MMR adds only **1.5×** (Niccum 2018, PMC6063229), i.e. MMR saturates under load. Any `fidelity_stack` op that multiplies stage factors will overstate.

Attestation: Hopfield PNAS 1974 (10.1073/pnas.71.10.4135); Putnam 2016 (PMC4740232); St Charles 2015 (PMC4465240); Niccum 2018 (PMC6063229); Lee 2012 (PMC3478608).

## 2 — orientation lives in the palindrome DEFECT `[ATTESTED — the convergent primitive]`
Every inversion/recombination mechanism surveyed needs the same integer:
```
palindrome_defect(word) -> int      # Hamming distance from word to its reverse complement
```
- serine invertases: *"the orientation of the recombination sites is determined solely by the identity of the nucleotides within the 2 bp crossover region"*; *"in native DNA invertase recombination sites, the sequence of the core nucleotides is never symmetrical"* (Johnson 2015, PMC4384473).
- `dif`: *"the inverted repeats are imperfect, not a perfect palindrome"* (Castillo 2017, CC-BY).
- **the causal proof** — R64 shufflon: *"Rci-dependent deletion … was observed [with] two direct **symmetric** sfx sequences, suggesting that **asymmetry** of R64 sfx sequences **inhibits** recombination between direct sfx sequences"* (Gyohda 2006, PMID 16723350). **Making the site symmetric unlocked the branch the machine normally forbids.**

So symmetry is the *carrier* and asymmetry is the *content* — a graded quantity, not a binary. This is the same object as the "graded come-home distance" proposed for the RegulonDB test, reached independently from the biology side.

## 3 — our own `cwf_consistency_mod2` has a named blind spot `[ATTESTED + verified in-repo]`
```
type I topoisomerase   dLk = +-1  -> flips a mod-2 read
type II (gyrase/TopoIV) dLk = +-2  -> INVARIANT: invisible
XerCD/dif unlinking     dCa = -1   -> flips
Topo IV decatenation    dCa = -2   -> invisible
```
*"Type I and II topoisomerases yield products that differ in DNA linking number (Lk) by 1 and 2, respectively"* (Dekker 2002, PMC129409, verbatim); gyrase ΔLk = −2/cycle (Klostermeier 2018, PMC5983639, CC BY 4.0).

srmech's docstring already carries the honest bound (*"a finite group (Q₈) pins Lk only mod 2 … NOT the unbounded integer Gauss linking number"*). What is new is **which operation class falls in the blind spot**. Measured on our own side: our fold's parity channel is **defined only at even step counts** and flips once per full beat — the odd/half-beat positions are exactly where the holonomy is non-central and the read is *undefined*.

**Explicitly NOT claimed**: that our 1-vs-2 step structure *is* the topoisomerase quantum. Both having a 2 is not evidence. Noted as a lead.

## 4 — the shipped codon table, re-verified by me `[DEMONSTRABLE — our own attested data]`
On `srmech.amsc.attested.genetic_code` (MPR v1, `response_sha256 ddda97af…`, NCBI transl_table 1):
```
16 roots -> 8 fully-degenerate / 8 split       full : AC CC CG CT GC GG GT TC
                                               split: AA AG AT CA GA TA TG TT
split signatures: 6 x (2,2)  +  TG (1,1,2)  +  AT (1,3)
synonymous single substitutions: pos1 = 8/192   pos2 = 2/192   pos3 = 128/192
Rumer involution T<->G, C<->A on the root:
   involution: True | fixed-point-free: True | full -> split: 8/8
```
Two things matter here. **Position 2 is almost perfectly non-redundant (2/192) while position 3 carries 128/192** — the redundancy is not spread, it is concentrated on one slot. And **a fixed-point-free order-2 involution on the 4-letter alphabet exchanges the two octets exactly** — that is a **Class C** chirality on the root alphabet, not a Class I rotation.

**Honest**: the 8/8 bisection is real and checkable arithmetic on an attested table, but it *"sits at the edge of mainstream molecular biology and has attracted a lot of numerological work that is not attestable."* **Use the computation; do not import the numerology.**

## 5 — the methodological catch that constrains this whole arc `[the most important negative]`
The reading-machinery agent, unprompted, partitioned its own report against the brief's framing:

> *"Items 7, 9, 10 and 11 are properties of the **stored object**, not of a reader — GC skew, macrodomains, NAP sites and gene overlaps are all in the sequence/annotation. Only items 1, 5, 12 (and arguably 8) are genuinely process/reader layers. **Do not let the second group get relabelled as the first.**"*

That directly checks the premise I briefed under ("machinery that doesn't surface when we talk about genome"). Much of what looks like process is stored structure a reader *exploits*. The genuinely reader-imposed item is the **ℤ₃ reading frame** — nothing in the strand marks it — which srmech's own `codon_read` docstring already states correctly.

## 6 — licences, corrected `[ATTESTED — several against my own earlier claims]`
| source | status |
|---|---|
| **Rfam** | **CC0** ✅ |
| **Blow 2016 prokaryotic methylome** (GEO GSE69872) | **CC0** ✅ strongest here |
| **SkewDB** (Dryad 10.5061/DRYAD.G4F4QRFR6) | **CC BY 4.0** ✅ |
| NCBI RefSeq / GEO / genetic-code tables | public domain ✅ |
| **RegulonDB** | **CC BY-NC** — *I told the user "CC-BY" twice; the NC restriction is real* |
| **REBASE** | *"All rights reserved"* + custom no-charge redistribution grant. **NOT** CC0/CC-BY |
| **KEGG** | restrictive — paid academic subscription for bulk |
| **EcoCyc / BioCyc** | restrictive — licence required, **≥ $5,000** for BioCyc files |
| GtRNAdb, MODOMICS, TransTermHP predictions | data-file licence **not stated / unverified** |

## 7 — one claim to keep out `[CONTESTED]`
The "genetic code is one in a million / error-minimising" result is **matrix-dependent and contested by its own field**. Minimisation percentage moves **91% → 80%** just by swapping similarity matrices (Novozhilov 2007, PMC2211284, CC BY). Koonin & Novozhilov, verbatim: *"Statements like 'the genetic code is one in a million' … can be easily misconstrued should one overlook the fact that there is a huge number of possible codes that are significantly more robust than the standard code, that sits on the slope of an unremarkable local peak in an extremely rugged fitness landscape."* Textbooks state it flatly; the specialist literature does not. **Any srmech op here must take the similarity and misreading matrices as required, named, attested arguments — a default would reproduce the defect.**

The clean adjacent result worth keeping instead: **Itzkovitz & Alon 2007** (PMC1832087) — the code is near-optimal for carrying *parallel* codes inside protein-coding sequence, over an ensemble of exactly **1,152** codes (`4!×4!×2`), and *"the ability to abort translation after frame shift is closely related to the ability to include arbitrary parallel codes"* (r = 0.8). Multiple simultaneous information channels in one ordered word is our problem exactly.

## Honest scope
- `[DEMONSTRABLE]`: §4 only — re-verified by me against the shipped MPR row, exhaustive over all 64 codons and 576 single substitutions. §3's in-repo half (our fold's parity channel) likewise.
- `[ATTESTED]`: §1, §2, §3's biology, §6, §7 — verified by sub-agents against primary sources with DOI/PMCID, **not** re-verified line-by-line by me. Treat as good secondary sourcing, not as my own measurement.
- **Not built.** No srmech op from any of this exists yet. Every "proposed op shape" in the three reports is a proposal.
- **Known gaps carried forward**: primary Călugăreanu/White/Fuller not retrieved (so our `relative_writhe`'s "Fuller single-integral" attribution is secondary-only — *a provenance gap in shipped code*); σ ≈ −0.06 unattested; no topological data of any kind for *M. genitalium* or JCVI-Syn3.0; no genome-wide PRF prevalence figure exists in the literature; the ">90% of Type II enzymes are palindromic" figure is **unattested** and should be computed from REBASE rather than cited.
- **Nothing here is a discovery about biology.** Every mechanism is published work, most of it textbook. The framework reads structure that is already established (`[[feedback_no_lineage_claims_in_notebook]]`).

## Verdict
The k=2/k=3 question is answered and the answer is sharper than the question: **biology distinguishes "the same check twice" from "a second independent channel," and only the latter corrects.** The mirror-detects-only result stands, attested. And the one primitive every mechanism needs — `palindrome_defect` — is the graded quantity we independently proposed. Generating code: `R-RBS-LM-CODONSTRUCT_*.py` (exit 0).

Composes **F1325** (the mirror is a k=2 check, not a carrier — *confirmed in a wet system*), **F1326** (the borrowed anchor / perspective-supplied component — *`GATC` symmetric + methyl mark is the same shape*), **F1324/F1323** (half vs full beat — *the ΔLk quantum is a lead, not a match*), **F1322** (the gauge ratchet), **F291** (k=2 detects, k=3 corrects), **F1154** (`op(x)operand(x)EC`), `[[project_ec_subharmonic_arc_intrinsic_fractal_not_single_bolted_on]]`, `[[feedback_pdf_extraction_citation_discipline]]`, `[[feedback_paywalled_doi_cannot_be_attested]]`.
