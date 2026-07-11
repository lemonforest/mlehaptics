# F1204 (#226/#225) — the embedded FORMAL sublanguages get their own COMPREHEND-not-strip kernels (LaTeX/convert/chem → relationship graphs), and a reusable RULESETS-vs-DATASETS blind-spot ratchet converges each ruleset against real data without fitting to it (LaTeX unrecognized-command 23%→2%, a 10.5× ratchet; chem 98% species coverage)

**Date:** 2026-07-10 · **srmech:** 0.9.0rc209 (native, ABI 4) · **Corpus (attested, not committed):** enwiki-latest-pages-articles.xml.bz2 (24GB, CC-BY-SA; local research use). numpy-free; plain-dict; no Python `abs` builtin; no `Counter`. · **Composes:** [[feedback_no_doctoring_ssot_use_sublanguage_kernels]] (F567/F764/F819 — a strip HIDES a missing kernel; comprehend, surface the gap), the F764 `understand_markup` `markup` chromosome (this extends it to the embedded formal sublanguages), F1203 (the mass/count determinative — the convert kernel harvests it directly), [[feedback_relational_not_dense_distributional]] (rulesets=relational vs datasets=distributional). **The pivot off the bigwiki-encode: before any full encode, the sublanguages must be COMPREHENDED, not stripped.**

## What happened
Working the bigwiki Class-L genome, the user corrected the approach three times in sequence, converging on the real architecture: (1) **don't strip markup** — comprehend each sublanguage; (2) **markup is a formal/programming language** in its own family, not NL; (3) **the LaTeX etc. sublanguages are not genome-encoded yet**. A census confirmed the gap: the wikitext *outer* grammar is a kernel (`understand_markup`/F764, the `markup` chromosome), but the embedded FORMAL sublanguages — LaTeX `<math>`, `{{convert}}`, `<ce>` chem, IPA, `<score>` — were removed-as-form, i.e. the strip-hides-a-missing-kernel anti-pattern (confirmed via the F819 GAPMAP + the genome surface).

## Result — three comprehension kernels, each NOTATION → typed relationship graph
| kernel | file | comprehends | example |
|---|---|---|---|
| **LaTeX/math** | `R-RBS-LM-LATEXKERNEL_…` | `<math>`/`{{math}}` → symbol+relation graph | `E=mc^2` → symbols {E,m,c^2}, edges (m,**mul**,c^2)+(E,**equals**,m) — operators preserved, no false `E=c^2` |
| **convert** | `R-RBS-LM-CONVERTKERNEL_…` | `{{convert}}` → typed quantity (value,unit,**dimension**) | `2000\|ft\|m` → 2000 **length**; the F1203 mass/count determinative harvested from the markup |
| **chem `<ce>`** | `R-RBS-LM-CHEMKERNEL_…` | mhchem → reaction graph (species→products) | `Ra-226→Ra-227→Ac-227 [β⁻;42.2 min]` — a nuclear decay CHAIN; `N2+3H2⇌2NH3` equilibrium |

Each is a Class-B/F FORM grammar (a notation parser, no numeric primitive), sibling to `understand_markup`; the graph it emits feeds the **3-representation triality** the user framed (① distributional holographic fold / ② relational Class-L spectral communities / ③ responsion-EC), which together rebuild the dense shape GPU LLMs lean on — three sparse encodings, not one.

## The methodology finding — a per-kernel RULESETS-vs-DATASETS blind-spot ratchet (the user's proposal)
A hand-authored ruleset built from a ~12-sample keyhole IS blind to what it never saw. We do NOT fit it to data (the distributional way). We run it over a large real corpus and **census what it fails to comprehend** — that names the missing rules (the F819 gapmap applied to the kernel itself). Measured over **60,701 real `<math>` expressions** (15k enwiki articles):

| | v2 (12-sample ruleset) | v3 (census-closed) |
|---|---|---|
| unrecognized `\command` tokens | 24,351 = **23%** | 2,313 = **2%** |
| distinct blind-spot commands | 263 | 124 |
| symbol coverage | 93% | 94% |

**10.5× reduction in blind spots** from ~8 rule-groups the *dataset named* (functions, environments, delimiters, ellipses, number-sets, logic, set-ops, fraction-variants — plus a `\d?frac` regex bug that never matched `\dfrac/\cfrac`). The remaining 2% tail is *surfaced and counted* (led by `\ce` = chemistry-in-math = the chem kernel's job — sublanguages nest). Chem's own ratchet (1,120 real exprs): **98% species coverage**, 2% hard-fail (mostly legitimately-empty arrow/condition fragments), 32% reaction rate (a data property — most `\ce{…}` is a single formula, not a reaction). The ratchet also surfaced that the sublanguages **share a formatting layer** (`\mathit/\text/\displaystyle` appear in chem too) → a shared FMT-unwrap base for the router.

## Verdict / next
**DONE — the embedded formal sublanguages now have COMPREHEND-not-strip kernels (LaTeX/convert/chem, notation→relationship-graph, discipline-clean), and the rulesets-vs-datasets blind-spot ratchet is proven reusable per kernel (LaTeX 23%→2% unrecognized, 10.5×; chem 98% species) — sparse/relational kernels reach dataset-level coverage WITHOUT becoming datasets (rules give comprehension, the dataset gives completeness, the two never merge). Honest limits: LaTeX is linear-adjacency not a full expression tree (nested-paren precedence unresolved); the 2% math tail + the small chem refinement list (stacking `\atop/\overset`, `^\circ`, more arrows, shared FMT-unwrap) are surfaced-not-hidden. NEXT: IPA + score kernels (same pattern), then the ROUTER (#225, Class-D dispatch composing all kernels' edges + the shared FMT base), then genome-encode the `latex`/`convert`/`chem`/… chromosomes sibling to `markup` — after which the sharded tome tower (`R-RBS-LM-WIKITOWER_…`, built + validated: 2 shards, 231k/238k vocab, ~270s/5k-arts, 4GB peak, resumable) re-runs on COMPREHENDED content. Read-independent-verified (coverage deltas + blind-spot census, no downstream read); enwiki-attested (not committed). → the sublanguages become languages Siona understands, not noise she deletes.**

Sources: enwiki dump (Wikimedia, CC-BY-SA-4.0; local research use — not redistributed). mhchem/LaTeX notation reference: standard TeX + mhchem package syntax.
