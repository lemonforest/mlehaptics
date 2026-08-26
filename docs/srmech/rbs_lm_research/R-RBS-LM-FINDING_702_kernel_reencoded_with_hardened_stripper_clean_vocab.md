# Finding 702 — the big-wiki kernel re-encoded with the hardened stripper (clean, trustworthy vocab)

**Script:** `R-RBS-LM-WIKIREENCODE_kernel_reencoded_with_hardened_stripper_clean_vocab.py`
**Status:** VERIFIED — re-encode done, vocab clean (srmech 0.6.0rc8 runtime)
**User direction:** *"The kernel must be re-encoded before its vocab is trusted for big wiki."*

## Done — the build path is fixed and the re-encode is exercised

F700 proved F690's demo stripper leaked LaTeX/ref/template/table markup into the vocabulary, and that the demo corpus never
exercised the path. This **wires the fix into F690's build path** and **re-encodes**:

- **`stream_articles` now uses `strip_wiki_markup_hardened`** (F700 — removes the *content* of
  math/ref/code/score/chem/table/comment blocks + clears nested templates to a fixpoint) **+ `content_words`** (F698 —
  Unicode-aware, so `café`→`café` not `caf`, and non-Latin scripts survive), instead of the leaky demo + the old ASCII
  `[A-Za-z][A-Za-z']+` tokenizer.
- The leaky `strip_wiki_markup` is **kept** (renamed in spirit, marked ⚠ NOT-for-build-path) so F700's leak demonstration
  stays valid.
- **`SYNTHETIC_WIKI` gained a real-markup article** (article 7: `<math>v=\sqrt{\frac{GM}{r}}</math>`, a bare `<ref>`, an
  `{{Infobox}}`, a `{| wikitable |}`, an HTML comment) so the hardened path is **actually exercised** — the gap F700 named.

(F690 edited in place, per the F695 precedent of fixing the reference directly.)

## Verified at the vocab level

Building the kernel two ways over the same markup-bearing corpus:

| build | vocab size | distinct markup junk tokens in vocab |
|---|---|---|
| **old** (demo stripper + ASCII tokenizer) | 53 | **7** — `citation, class, displaystyle, frac, hubble, sqrt, wikitable` |
| **re-encoded** (hardened + Unicode) | 42 | **0** |

`assoc('galaxy')` on the re-encoded kernel → `[coils 3.0, spiral 2.0, shell 2.0, turns 1.0]` — grounded in **meaning**, not
markup co-occurrence. There is no spurious `galaxy ↔ displaystyle` edge. The script `assert`s the re-encoded vocab carries
zero junk.

## Why this matters

Every edge of a Class-L co-occurrence kernel is a co-occurrence. If the vocab contains `displaystyle`/`wikitable`, the
kernel forms associations with *markup*, and a story built on it (F697) would ground a beat in markup noise — breaking the
chord (F658) at the corpus-cleaning layer. After the re-encode the vocab is **trustworthy**: associations are co-occurrences
of real content words only (F640/F688 grounding honesty).

## Scope (honest)

- This re-encodes the **reference** on the synthetic corpus. A **real enwiki re-encode** is the dev session pointing
  `stream_articles` at the dump (the hardened cleaner is now in place); the real cleaner is the **F579/F607
  wiki-formatting-language kernel**.
- Two residues remain and are **honest, not markup junk**: a near-stopword (`where`) the minimal demo stoplist misses (the
  dev session swaps a fuller stoplist), and an un-lemmatised possessive (`galaxy's`) — both real word-forms, handled by the
  dev session's normaliser. No silent cap (F640).

**Composes:** F700 (the hardened stripper) · F698 (the Unicode tokenizer) · F690/F697 (the kernel + its inference, now
re-encoded) · F640/F688/F658 (grounding honesty) · F573 (the audit that found it) · F579/F607 (the real target). Backlinks
F700 (`→ requirement satisfied by F702`) and F690 (`→ build path re-encoded by F702`).

*Held open (F394). Reference scaffold; not a package edit.*
