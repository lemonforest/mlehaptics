# Finding 722 — srmech 0.7.5rc49 ships R3 U1, but it fails the §40 acceptance bar 3/3; R3 U1 stays OPEN

**Script:** `R-RBS-LM-U1ACCEPTANCE_rc49_tokenize_cooccurrence_vs_section40_bar.py`
**Status:** VERIFIED (srmech 0.7.5rc49, TestPyPI, numpy-free venv)
**User direction:** *"srmech 0.7.5rc49 is ready on test.pypi.org"* — run the §40 acceptance bar.

## The verification (MPM — this is exactly why §40 exists)

rc49 ships `tokenize` + `cooccurrence_edges` in `srmech.amsc.laplacian` (Option 3; §40 recommended `amsc.text`).
The **format is correct** — `cooccurrence_edges` returns `(n, edges, weights)` with edges as **2-tuples** straight
into `dense_laplacian`, and `tokenize` has a `stopwords=` param — so for **English / single-document / small-vocab**
it works and retires the hand-rolled `Counter()`. But against the §40 bar (written from the wiki kernel's *real*
requirements), it **fails all three points**:

| §40 bar | rc49 behavior | verdict |
|---|---|---|
| **1. Unicode-aware tokenize (F698)** | `tokenize("café Москва naïve 日本語 hello world")` → `['caf','na','ve','hello','world']` — accents stripped, **Cyrillic + CJK dropped entirely** | **FAIL** — ASCII-only; cannot tokenize non-English |
| **2. No silent vocab cap (F708)** | default **`vocab_size=1000`**; a 1500-word stream → **silently capped to n=1000**; no `None`/`all` sentinel | **FAIL** — the exact F708 pre-encode quantization, re-introduced *as the default* |
| **3. Document-boundary window-reset** | flat `tokens` arg, **no `boundaries=`/`docs=` param** | **FAIL** — co-occurrence bleeds across article boundaries |

**Genome storage surface (F716–F721): regression PASS** — rc49 did not break the chromosomal storage we built on.

## Why each failure is disqualifying for our actual use

- **Unicode** is not cosmetic here: R6 (the multilingual corpus, #846/#847) is the whole point of the
  truth-filter's independence — an ASCII-only tokenizer **cannot represent** the non-English renders, so it defeats
  R6 at the door. (It also silently corrupts English: `café`/`naïve` → `caf`/`na`+`ve`.)
- **The `vocab_size=1000` default** is the F708 bug wearing a default value. A naive caller building the full-wiki
  kernel gets **silently quantized to the top 1000 words** — the precise pre-encode quantization the user caught
  and we ripped out. Overridable (`vocab_size=len(vocab)` works), but a *default that quantizes* violates
  no-magic/no-silent-cap; the cap must be an **explicit, logged opt-in**, never the default.
- **No boundary reset** means feeding concatenated articles forges spurious **cross-article co-occurrence edges**;
  our kernel's invariant is *one article = one window reset* (F690/F700).

## Disposition

- **R3 U1 is NOT closeable.** It shipped a version that re-introduces F708 (as a default), can't do multilingual
  (defeating R6), and bleeds across documents. #855 R3 U1 stays unchecked.
- **The wiki kernel does not adopt the shipped ops yet.** We *could* call `cooccurrence_edges` safely only by
  always passing `vocab_size=len(full_vocab)` AND calling it **per-article** then merging edges — but `tokenize` is
  unusable for us at all (ASCII-only), so we keep our F698/F700 `content_words` + `build_edges_topk` until the
  fixes land.
- **The three required fixes** (now in UPSTREAM_NOTES §40): (1) Unicode tokenize (`unicodedata` L/M categories, not
  `\w+`); (2) default = **no cap** (`vocab_size=None`/`0` → all; a cap is an explicit logged opt-in); (3) a
  `boundaries=`/`docs=` param so the window resets per document.

**Honest note:** this is a *constructive* verification, not a rejection — the op is a real start with the right
return shape; the three gaps are well-scoped and fixable, and the genome surface is solid. The value is that the
§40 spec caught the F708-regression-as-default **before** it silently quantized a full-wiki encode (the exact
failure mode the user flagged in the original reckoning).

**Composes:** §40 (the spec this checks) · F708 (the vocab-cap bug, here re-found as a default) · F698/F700 (Unicode
tokenize + markup discipline) · F690 (one-article-one-window-reset) · F716–F721 (genome surface, regression-clean) ·
R6/#846/#847 (the multilingual corpus the ASCII tokenizer defeats). srmech 0.7.5rc49. Held open (F394).
