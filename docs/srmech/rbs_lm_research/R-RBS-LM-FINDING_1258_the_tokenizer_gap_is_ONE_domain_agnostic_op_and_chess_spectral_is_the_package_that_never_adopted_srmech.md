# F1258 — the Siona tokenizer is **five fused concerns**, and srmech already delivers the only one that is genuinely universal. Composing `glyph_stream` + one declared predicate reproduces Siona's segmentation **5/5 exactly** on the prose it was built for. There is exactly **ONE real upstream gap** (accent/confusable folding), one **inherited defect** Siona still carries after srmech retired it (`len>2`), and two concerns that are correctly local but undeclared. **+ the cross-domain measurement the bet needs: `chess-spectral` never adopted srmech at all — 11 private `_dense_laplacian` sites, 0 srmech-Laplacian — while `ephemerides-spectral` is already on it (13).**

**User (2026-07-20):** *"can we prefer srmech tokenizer tooling? we brought our research from here to srmech so that our tooling can be as domain agnostic as possible … once we find the correct pattern in things, we should be able to ride any other domain whose cascade patterns have been recognized with the same type of tooling of different coherency/perspectives … before doing re-encode, find out what parts of srmech does not deliver what we use in our siona tokenizer things."*

Harness `R-RBS-LM-TOKGAP_…py`, srmech **0.9.0rc288**.

## The tokenizer is not one op — it is five, fused
| # | concern | Siona site | srmech equivalent | status |
|---|---|---|---|---|
| 1 | **SEGMENT** | `_native._tokenize_spans_py` (byte scan) | **`glyph_stream`** | **DELIVERED** — and better |
| 2 | **CASEFOLD** | `_native.tokenize` `.lower()` | `str.lower` | **DECLINED** upstream (per-locale, rc287) |
| 3 | **FOLD** | `context_shape.fold_accents` (NFD, drop Mn) | *(none)* | **GAP — the one real one** |
| 4 | **FILTER** | `anchor._words` `len(w) > 2` | *(retired by rc287)* | **INHERITED DEFECT** |
| 5 | **MORPH** | `asl._lemma_variants` (English suffixes) | *(none)* | **LOCAL**, correctly |

Fusing them is why "can we prefer srmech tooling?" had no yes/no answer: **1 should move, 3 should move upstream, 4 should be deleted, 2 and 5 should stay but be declared.**

## Concern 1 — srmech already delivers it, and the composition is exact
`glyph_stream` + one named boundary predicate over grapheme clusters (`category(base)[0] in L|M|N`) reproduces Siona's own tokenizer **5/5 exactly** on ASCII prose, including punctuation, contractions, digits, CamelCase and whitespace edges. **The private tokenizer is replaceable, not merely approximable.**

## The correction that matters — a word predicate CANNOT fix scriptio-continua
I expected the byte scan (`_is_word_byte`: `c >= 0x80` makes every non-ASCII byte a word byte) to be the cause of the CJK/Thai run-together defect. **It is not, and my own replacement reproduces the defect exactly:**

| script | Siona tokens | glyph-words | |
|---|---|---|---|
| Japanese `日本語のテキストです。` | 1 (11-char) | **1** | both collapse |
| Chinese | 1 (9-char) | **1** | both collapse |
| Thai | 1 (18-char) | **1** | both collapse |

Any word-grouping predicate collapses these, **because there is no word boundary in the text to find.** `glyph_stream` returns the 11 units that actually exist (`日 本 語 の テ キ ス ト で す 。`). So this is not a tokenizer bug to be fixed at the word layer — **it is the argument for the glyph unit itself**, and it independently re-derives rc287's reasoning from our side. It also means the ~89 %-singleton degeneracy rc287 measured is *not* avoidable by improving Siona's tokenizer; only by changing the unit.

*(Siona is better than pre-rc287 srmech in one respect: `siona_tokenize("中 国")` → `['中','国']` where srmech's `tokenize` returned `[]`. It loses on the run-together case instead. Neither was right.)*

One genuine divergence: **emoji**. Siona keeps them (`c >= 0x80`); my L|M|N predicate drops them (category `So`). `glyph_stream` handles them correctly as single clusters (`👨‍👩‍👧‍👦` is ONE unit). A replacement predicate must decide this explicitly rather than inherit it.

## Concern 3 — the one real gap, and it is domain-agnostic
`fold_accents` = NFD → drop `Mn` → lower. rc287 explicitly declined this ("case folding and confusable normalisation are per-locale concerns that belong downstream"). **That framing is right for casefold and arguably wrong for mark-folding**: dropping combining marks is a *projection that discards a chirality-like coordinate* — structurally the same operation whether the marks are Greek macrons, Vietnamese tone marks, or (by analogy) any per-datum modifier a sister domain carries. It is a Class-K-shaped projection with a text costume. **Upstream candidate**, worth proposing as `text.fold_marks(s)` distinct from casefold.

## Concern 4 — Siona still carries the defect srmech just deleted
`anchor._words` / `register._words` apply `len(w) > 2`. Live behaviour today:

```
anchor._words("a cat in a hat")     -> ['cat', 'hat']
anchor._words("I am")              -> []
anchor._words("to be or not to be") -> ['not']
anchor._words("中 国")              -> []
```

This is the **same `_MIN_LEN` floor rc287 removed**, and F1257 measured that the tokens it deletes (`a`, `I`, `to`, `be`, `or`, `in`) are **exactly the operator layer that IS the conserved core (94/94)**. srmech fixed this because of our finding; **Siona has not applied its own finding to itself.** This is a live defect in shipped code, not a research artefact.

## The cross-domain bet — measured, and it splits the portfolio
| package | files touching srmech | srmech Laplacian uses | **private `_dense_laplacian`** |
|---|---|---|---|
| `siona` | 32 | 17 | 0 |
| `ephemerides-spectral` | 24 | 13 | 0 |
| **`chess-spectral`** | **3** | **0** | **11** |
| `antikythera-spectral` | 2 | 0 | 0 |

**`chess-spectral` never adopted srmech.** It carries its own `_dense_laplacian` (`chess_spectral/tables_4d.py:800`) with 11 call sites across `direct_orthogonality.py`, `analyze_fiber_rank_4d.py`, `staged_cosine.py`. So the user's read — *"early research, not necessarily organized coherently"* — is **confirmed for chess and false for ephemerides**: ephemerides is already riding the shared tooling; chess is the outlier.

That makes the ride-into-other-domains bet concrete and *testable rather than aspirational*: chess is the one package where adopting srmech's Class-L surface would be a genuine change of substrate rather than a rename. And it is the package that would have been exposed to the **#1440 `mat_eigvals` defect class** with no ratchet to catch it — a private Laplacian gets none of the invariant testing rc285 added (λ_min = 0, relabelling invariance). **Its spectra have never been checked against that invariant.**

## Verdict / next
"Prefer srmech tokenizer tooling" resolves to four different actions, not one. **NEXT, in order:** (1) delete concern 4's `len>2` floor — a live defect our own F1257 condemns; (2) replace concern 1 with `glyph_stream` + a *declared, emoji-explicit* predicate; (3) propose `fold_marks` upstream as the one genuine domain-agnostic gap; (4) declare concerns 2 and 5 as locale-local rather than leaving them implicit. **Then** the re-encode — because re-encoding before (1) and (2) would bake the retired floor into the new genome. Separately: run the rc285 invariant (λ_min = 0, relabelling invariance) against `chess-spectral`'s private `_dense_laplacian` before trusting any lodged chess spectrum.

Composes **F1257** (the operator-spine finding that drove rc287 — and which Siona has not yet applied to itself), **F1256/F1255**, **#1440** (fixed rc285; the ratchet chess has no access to), `[[feedback_introspect_srmech_before_python_dispatch]]`, `[[feedback_no_doctoring_ssot_use_sublanguage_kernels]]` (concern 4 IS a strip), `[[user_stance_cross_substrate_cascade_matching_as_research_method]]`, #231/PKG-3.
