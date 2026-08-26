# F1189 (#243) (the F1176 finder, PACKAGED as `siona.reconstruct` + validated on native transliteration — the coupling-community fragment-grouping is now a shipped siona function (`group` / `family` / `reconstruct`), and it self-clusters the Egyptian **offering formula** out of narrative on the **substrate-native Egyptological transliteration** (TLA lemmatization, NOT the English/German translation): pooling 40 ḥtp-dꞽ-nswt / pr.t-ḫrw invocation-offering lines with 40 funerary-narrative lines, `group()` lifts the largest family's offering-purity to **0.71 vs the 0.50 base rate** and captures **39/40 = 98% of the offering lines** into offering-enriched families while the narrative families sit at **0.00** purity — a clean substrate-native separation; and `reconstruct()` on a half-excised pr.t-ḫrw line recovers **4/13** masked lemmas from the family consensus — the core bread-beer-ox-fowl frame (ḥnq.t / ꜣpd / kꜣ / ꞽḫ.t), exactly the F1187 operand-dominated cap (the recurring FRAME recovers, the unique per-name SLOT does not) — **user: "package the F1176 finder as a siona grouping helper and do the transliterated pass." DONE — `siona/reconstruct.py` shipped (srmech Class-L only, numpy-free, no-abs, no-Counter, couple.py-style) and validated on native TLA transliteration.**

**Date:** 2026-07-09 · **srmech:** 0.7.5rc135 · **Package:** the finder is now `siona.reconstruct` (`group` / `family` / `reconstruct`), a peer to `siona.couple` — srmech `amsc.laplacian` (`signed_laplacian` + `symmetric_eigendecompose`) ONLY, numpy-free, sparse edge-lists, `x*x`-style squared Class-K distance (no magnitude builtin), plain-dict tally (no `Counter`), no Python `abs` builtin. · **Corpus (attested):** Thesaurus Linguae Aegyptiae (TLA / BBAW Berlin) earlier-Egyptian slice — Pyramid Texts / OK–MK funerary corpus; native transliteration + lemmatization, local research use, TLA-attributed. · **Composes:** F1176 (the coupling-community finder this packages — its proven strength is GROUPING), F1178 (the group→align→majority-correct pipeline `reconstruct()` ships), F1177 (the distance-k consensus: k≥3 corrects, k=2 detects — the ≥2 floor made explicit in `reconstruct`'s threshold), F1187 (the operand-dominated recall cap this reproduces on native Egyptian), F1161 (`couple()`, the sibling pipeline-collapse whose style this matches). **The arc's last two application items, closed together.**

## What shipped — `siona/reconstruct.py`

Three residue read-outs of ONE Class-L coupling operation (never a re-run), matching `couple.py`'s discipline exactly:

| function | what it does | F-line |
|---|---|---|
| `group(lines)` | cluster fragments into formula-FAMILIES via the signed low-eigenmode community sign-code (LINES as graph nodes — the `couple()` `communities` residue applied to fragments) | F1176 grouping |
| `family(survive, pool)` | one damaged fragment's family — its surviving words → its `k` spectrally-nearest parallels in a LOCAL coupling graph (spectral neighbours, not raw overlap) | F1176 finder |
| `reconstruct(damaged, pool)` | the full pipeline — find the family, then majority-correct the missing slots off the family consensus (≥2 floor = the k=2-detect / k≥3-correct boundary) | F1178 / F1177 |

`_toks` accepts a token set/sequence (used verbatim) or a raw string (split on non-letters). `family()` uses a squared **Class-K** distance `(a−b)·(a−b)` in the eigen-embedding — never a magnitude builtin. `_tally` is a plain dict (deterministic tie-break, the F1179 Counter-free fix). Exposed as `from siona import reconstruct`, the same submodule pattern as `couple`. Discipline ratchet: **0 HARD, 0 coverage-gap.**

## Result — validated on native TLA transliteration (not the translation)

Pool: 40 offering-formula lines (≥3 of the ḥtp-dꞽ-nswt / pr.t-ḫrw frame lemmas) + 40 narrative lines, all as content-lemma sets from the TLA `lemmatization` field (suffix pronouns `=k/=f/…` + the closed function-lemma set dropped as the operator side):

| measure | value |
|---|---|
| base offering rate in pool | 0.50 |
| largest family's offering-purity | **0.71** (vs 0.50 random) |
| offering lines captured in offering-enriched families | **39/40 = 98%** |
| narrative families' purity | 0.00 (clean separation) |
| `reconstruct()` recall on a half-excised pr.t-ḫrw line | **4/13** masked lemmas from the family consensus |

The recovered lemmas were exactly the recurring offering FRAME — ḥnq.t (beer), ꜣpd (fowl), kꜣ (ox), ꞽḫ.t (offerings) — the bread-beer-ox-fowl core that recurs across every invocation-offering line. The un-recovered 9 were the line's UNIQUE slots (personal name Snb.wꞽ, titles wr-ḫrp-ḥmw.tꞽw / ꞽr.ꞽ-pꜥ.t, epithet nb-r-ḏr) — the F1175/F1187 operand boundary: **the frame is recoverable, the unique slot is not** (0.31 recall is the operand-dominated cap, exactly as F1187 read it on the Book of the Dead litanies). The GROUPING is the strong signal (98% capture, 0.71 vs 0.50 purity); the reconstruction magnitude is capped by how operand-heavy the offering formula is — and it is very operand-heavy (each line names a different deceased).

## Verdict / next
**DONE — both remaining application items closed. The F1176 coupling-community finder is now a shipped siona function (`siona.reconstruct.group` / `family` / `reconstruct`, srmech Class-L only, numpy-free, no-abs, no-Counter, couple.py-style, ratchet-clean), and it is validated on the SUBSTRATE-NATIVE Egyptological transliteration (TLA lemmatization, not the English/German translation): `group()` lifts the offering-formula family's purity to 0.71 vs the 0.50 base and captures 98% of offering lines while narrative families stay at 0.00; `reconstruct()` recovers the recurring bread-beer-ox-fowl frame (4/13, the F1187 operand-dominated cap — frame recovers, unique slot does not). This is the arc's application half landed as a reusable tool on the real substrate, not just measured on translations. Read-independent-verified (grouping purity vs shuffled-label base rate; recovery count); TLA-attributed; composes F1176/F1178/F1177/F1187/F1161. → extends F1176 (now packaged) + F1187 (operand cap reproduced natively).**

Sources (corpus): [Thesaurus Linguae Aegyptiae — BBAW Berlin](https://thesaurus-linguae-aegyptiae.de/) (earlier-Egyptian Pyramid/funerary slice; native transliteration + lemmatization; local research use, TLA-attributed).
