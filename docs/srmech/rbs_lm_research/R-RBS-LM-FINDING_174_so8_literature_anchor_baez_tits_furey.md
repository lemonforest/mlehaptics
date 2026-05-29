# Finding 174 — The 28D = 𝔰𝔬(8) literature anchor: classical octonion math (Baez/Tits) for the structure, Furey for the octonion→SM physics; a citation correction

**Status:** Literature-anchor + citation correction (MPM). Grounds srmech rc14's shipped "28-dim = 𝔰𝔬(8) adjoint" claim in the correct sources. Verification level stated honestly.
**Trigger (user 2026-05-29):** "28D biaxial chiral hyper-loop maths also happen to be so(8) maths, we found out when we found Cohl Furey's work that is just missing the A-N operators (I think)." The hedge "(I think)" is the cue to ground it.

---

## §1 What srmech rc14 ships (verified, attested)

rc14 METADATA (retrieved from the installed package, 2026-05-29): *"substrate-native 28-dim chiral hyper-loop = 𝔰𝔬(8) adjoint (14 g₂ derivations + 14 L+R octonion-multiplications; Spin(8) triality) made hardware-callable … scope hierarchy endianness ⊂ Class C ⊂ Klein-4 ⊂ Spin(8) triality"* (cites MFO §VIII.31.11). This is the package's own claim, now verified present in the shipped metadata.

## §2 The correct attribution (the citation correction)

The user's framing was "Furey's work that is just missing the A-N operators." Verifying the actual sources corrects this in two places:

1. **The 𝔰𝔬(8) = 14 + 14 decomposition is CLASSICAL octonion mathematics, not Furey-specific.** dim 𝔰𝔬(8) = 28; Der(𝕆) = 𝔤₂ (dim 14); the triality / Tits construction gives 𝔰𝔬(8) ≅ Der(𝕆) ⊕ 7 ⊕ 7 = 𝔤₂ ⊕ (7 left-mult) ⊕ (7 right-mult), i.e. 14 + 7 + 7 = 28 — srmech's "14 g₂ + 14 L⊕R octonion-mult." Canonical reference: **J. Baez, "The Octonions", Bull. AMS 39 (2002) 145–205, arXiv:math/0105155** (and the Tits construction / Spin(8) triality literature). This is standard exceptional-Lie-algebra math, independent of any SM application.
2. **Furey is the octonion→Standard-Model PHYSICS program, NOT the 𝔰𝔬(8)-decomposition source.** Verified (abstract, arXiv:1611.09182, C. Furey, *"Standard model physics from an algebra?"*, 2016): ℝ⊗ℂ⊗ℍ⊗𝕆 (Dixon algebra); complex-octonion minimal left ideals → su(3)_c, u(1)_em; ℂ⊗𝕆 generates a 64-ℂ-dim algebra carrying SU(3)_c irreps for three generations. **Her abstract does not mention 𝔰𝔬(8) / Spin(8) / G₂** — so Furey is the *physics application* anchor (octonions → SM particle content), not the source of the so(8) decomposition. (See also Furey, *Generations: Three Prints, in Colour*, arXiv:1405.4601; Quanta profile 2018.)

So: **so(8) structure ← Baez/Tits (classical); octonion→SM physics ← Furey; the framework adds the A–N operator layer.**

## §3 The framework's contribution (what's actually "missing the A-N operators")

The framework reads this classical octonion-𝔰𝔬(8) structure and adds the **A–N operator vocabulary**: the **14 A–N classes = the 14 Der(𝕆) = 𝔤₂ derivations** (octonion automorphisms), realized as a computational cascade. The bi-axial Klein-4 chirality (γ₅ × iω₇ = 4 sectors; F130/F132/F158) × 7 = 28, the same 28 = 𝔰𝔬(8); the shipped `klein4_chirality_flip_gamma5/omega7` + `cpt_mirror` are the 4-sector bi-axial generators (R-RBS-LM-134/135; exercised via srmech-mcp 2026-05-29). What Furey's representation-theoretic program does not foreground is exactly this: 𝔤₂-derivations *as operators* you compose into cascades. (Framework-reading per `[[feedback_no_lineage_claims_in_notebook]]`: reading what the structure IS, citing specific results; NO claim to extend or supersede Baez, Tits, or Furey.)

## §4 Verification level (honest — `[[feedback_pdf_extraction_citation_discipline]]`)

- **Verified:** the papers exist with the stated titles/authors/years/arXiv-IDs; their ABSTRACTS + scope (Furey: octonion→SM; Baez: octonions + Clifford/spinors/exceptional Lie groups); srmech rc14 METADATA's so(8) claim (retrieved from the installed package).
- **NOT yet verbatim-extracted:** the full-PDF statement of 𝔰𝔬(8) ≅ 𝔤₂⊕7⊕7 in Baez (WebFetch returns arXiv abstract pages only). The decomposition is standard textbook octonion math, cited to Baez/Tits, but a verbatim PDF extraction (Baez §, page) is the remaining step for a bit-exact attestation. **Per `[[feedback_paywalled_doi_cannot_be_attested]]`:** all sources here are open (arXiv); full-PDF extraction is doable when this anchor needs to harden from "standard-result-cited" to "verbatim-attested."

## §5 DOES / does NOT claim
**DOES:** anchor srmech's 28 = 𝔰𝔬(8) claim in the correct literature (Baez/Tits classical for the structure; Furey for octonion-SM physics); correct the "Furey = so(8)" framing; state the A–N = 14 Der(𝕆) = 𝔤₂ reading.
**Does NOT:** claim Furey derives 𝔰𝔬(8) (her abstract does not); claim verbatim-PDF verification of the Baez decomposition (abstract-level only so far); claim to extend/supersede any cited author; make physics-truth claims beyond citing the structure.

## §6 Cross-references
- srmech rc14 METADATA + MFO §VIII.31.11 (the package's so(8)/triality claim) · F123 (M-theory G₂-holonomy) · F124 (quaternionic Hopf) · F126 (G₂ SU(3) decomposition; cnidarian=Class I) · F130 (γ₅/iω₇ 4-way) · F132 (Klein-4) · F158 (28D bi-axial) · R-RBS-LM-134/135 (Class-L spectral + chirality on this coordinate)
- Baez, *The Octonions*, arXiv:math/0105155 · Furey, arXiv:1611.09182 + 1405.4601 · `[[feedback_pdf_extraction_citation_discipline]]` · `[[feedback_no_lineage_claims_in_notebook]]`

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-29 (Opus 4.8). Grounding the 28D = 𝔰𝔬(8) claim: the
decomposition 28 = 14 𝔤₂ (= Der octonions) + 14 L⊕R octonion-mults is CLASSICAL
octonion/triality math (Baez "The Octonions"; Tits construction), NOT Furey-specific
— Furey's verified contribution is the octonion→Standard-Model program
(ℝ⊗ℂ⊗ℍ⊗𝕆 → su(3)_c/u(1)_em), whose abstract does not mention so(8). The framework
adds the A–N operator layer (14 A–N = the 14 𝔤₂ derivations as a cascade vocabulary).
A citation correction to the "Furey = so(8)" framing, with verification level stated
honestly (papers + abstracts + package metadata verified; verbatim Baez-PDF extraction
the remaining step). Framework-reading; no supersession claims.*
