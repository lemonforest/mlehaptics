# F761 — the LANGUAGE LAYER made real in the genome: ni-Vanuatu abstract translation base + SignWriting (same level) + English built on top

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** R-RBS-LM-25 (byte/glyph-level LM — strip English privilege), R-RBS-LM-54 (Rosetta shared-translation layer), F735 (SignWriting accessibility chromosome), the genome strand (F584/§41–§46) · **User correction (2026-06-15):** "all language kernels are supposed to be built with Ni-Vanuatu as the abstract translation layer … the byte/glyph-level LM such that any language can do inference, and then the english kernel on top of that. SignWriting at the same level as Ni-Vanuatu, such that the same abstract translations also equal their SignWriting form." + "explicit language layer."

## The gap this fixes (I had the dependency inverted)
The genome built `signwriting`, `dict-en-1600`, `dict-en-2026` as **flat, independent random-HV chromosomes**. English words were fresh random leaves (`_leaf("dict-en-2026/nice")`) — **not** built from any base; SignWriting sat flat (not positioned at the abstract level); **ni-Vanuatu was absent entirely.** The layered architecture (designed in R-RBS-LM-25/54) was never encoded in the genepool. (Same class of gap as the wiki-side-store mislabel — designed-in-research, not realized-in-genome.)

## The layer, now in the strand
`build_genepool` now emits the language layer as real chromosomes:
- **`ni-vanuatu` (29)** — the ABSTRACT TRANSLATION base: one Klein-4 vector per glyph (`a–z` + `'`, `-`, space). The language-AGNOSTIC substrate every language projects from (the byte/glyph-level pivot).
- **`signwriting` (7)** — the SAME LEVEL as ni-Vanuatu: the *signed* form of the same abstract translations (the 7 SignWriting symbol classes).
- **`dict-en-1600` / `dict-en-2026`** — SURFACE English, each word now **built FROM the ni-Vanuatu base**: `_word_hv(w)` = `klein4_bundle` of position-bound (`klein4_bind` with a position role) glyph vectors. A word is a **projection of ni-Vanuatu**, not an independent random token.

## Verified
- The genome strand now carries `ni-vanuatu(29), signwriting(7), dict-en-1600(5), dict-en-2026(5), mfo_notebook(16), srmech_notebook(44)` — the language layer is *in the genome*, not a side-store.
- **English is genuinely built from the base:** `sim(nice, mice) = 0.62` (share `i,c,e` → shared substrate) vs `sim(nice, xyzqw) = 0.17` (no shared letters → near-random). Words sharing letters share substrate — the "any language projects from ni-Vanuatu" property, concretely.
- Retrieval intact: `define nice` → the dict-en etak-walk still resolves (`nice → agreeable → pleasant …`); the F739 era-resolution is unaffected (it routes on payload text, not the leaf HVs).

## Honest scope
- This realizes the **genome representation** of the layer (ni-Vanuatu base, signwriting sibling, English glyph-projected). It does **not** yet make *inference itself* run through the abstract layer (any-language byte-level inference + SignWriting read-out of the same abstract translation) — that's the deeper R-RBS-LM-25/54 build (the surface tiers still answer in English text).
- `_word_hv` is a position-bound glyph bundle (order-preserving via `_posrole`); it is a faithful glyph-composition, not a learned morphology.
- The "abstract translation layer" is named `ni-vanuatu` per the user's architecture (Vanuatu = Earth's most language-dense place → the natural language-agnostic pivot); the glyph alphabet is my concrete realization of "byte/glyph-level base" — confirm if a different base set is intended.

## Verdict
The language layer is now explicit in the genome: **ni-Vanuatu = the abstract glyph translation base, SignWriting = its same-level signed sibling, English = a surface projection built from the base** (verified: shared-letter words share substrate). Live on the rc155 server. Next: inference *through* the abstract layer (cross-language + SignWriting read-out of the same abstract HV) — the R-RBS-LM-25/54 deep build.
