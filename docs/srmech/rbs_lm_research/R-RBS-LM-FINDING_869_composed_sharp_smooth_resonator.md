# F869 — The composed sharp+smooth resonator: reproduces seen sequences AND generalizes to novel ones, gated by the sharp match-count, float-free. The "infers AND reproduces" engine that F867 pointed to. Two memories over the byte/glyph core: **M_sharp** (octonion coupling-product key, F866 → orthogonal per ordered context → exact reproduction) and **M_smooth** (additive position-bundle key, F867 → overlapping contexts share halves → generalizes). **One `recall()` gates on the sharp key's own integer match-count:** a *seen* context lands its exact sharp key (count ≫ chance → reproduce); a *novel* context hits sharp noise (count ≈ chance → fall back to the smooth key that generalizes). On live srmech, no bag, all-integer ranking (no float): the gate cleanly separates seen (~4265–4295) from novel (~2566, ≈ chance D/4=2500); scenario A reproduces `the cat saw the dog <e>` **exactly** (every step sharp, no crosstalk on the repeated "the"); scenario B generalizes a **novel** context `the bird → sat` via the smooth fallback (sharp-count 2532 ≈ chance → gated to smooth). Reproduction and generalization in one engine.

**Date:** 2026-06-18 · **srmech:** 0.8.2 (live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Provenance:** `R-RBS-LM-869_composed_resonator.py` (`hdc.klein4_{random,bind,unbind}` + `.tolist()` match-count, `cs.pos_key/bundle_odd`, `cascade.cd_mult`) · **Composes:** F866 (sharp coupling-product = reproduction), F867 (smooth additive = generalization; the two ends), F865/F864/F863 (byte/glyph + coupling-walk), F868 (float-free / integer match-count), F838/F839 (resonator), [[feedback_never_bag_of_words_even_for_testing]], [[feedback_stay_rational_collapse_only_at_display]] · **User direction (2026-06-18):** "continue" → the composed resonator (the next build that emerged from F867).

## The mechanism (one gated recall)
```
recall(ctx):
  sharp = unbind(M_sharp, key_sharp(ctx)); top = max match-count over vocab
  if top >= GATE:  return argmax sharp          # SEEN -> reproduce (F866, no crosstalk)
  else:            return argmax over unbind(M_smooth, key_smooth(ctx))   # NOVEL -> generalize (F867)
```
- **GATE = 1.3 × chance** (chance = D/4, attested to the 4 Klein-4 sectors — not a magic number). Measured separation: seen contexts ~4265–4295, novel ~2566. The gate *is* "have I seen this exact context?" read off the sharp key's collision-freeness.
- **All-integer, float-free** (F868): ranking on the integer match-count; the gate is an integer threshold attested to `CHANCE`. No decimal collapse anywhere.

## Measured
| scenario | result |
|---|---|
| gate (seen vs novel) | seen 4265–4295, novel 2566 (chance 2500, gate 3250) — clean separation |
| A: reproduction | `the cat saw the dog <e>` **exact**, all steps via sharp (counts ~4300), no crosstalk |
| B: generalization | `the cat`→sat (sharp, 3777); novel `the bird`→sat (**smooth**, 2532≈chance) |

## Honest scope
- **Toy scale** (single/double sentences, K=2). The seen/novel sharp-count gap is clean here; at corpus scale, capacity lowers sharp match-counts (more bundled binds → more noise), so the gate must be **calibrated per store** (or made relative: top-vs-second margin) — validated as the gate-at-scale question, not assumed.
- **Generalization is structural** ("the <X> → sat" via shared position-keyed words), **not semantic** (it does not know bird≈cat). Semantic generalization needs semantically-similar word vectors (the co-occurrence/relationship axis) — separate.
- **Branching (item 2)** composes here: where a context genuinely has multiple nexts (sharp or smooth), emit the F867 exact-rational distribution instead of argmax; not re-shown.
- No bag-of-words; content is the position-keyed / coupling-product relationship memory; the gate is float-free.

## Verdict / next
The composed resonator reproduces seen sequences exactly (sharp coupling-product) AND generalizes to novel contexts (smooth additive fallback), gated by the sharp integer match-count, float-free — the "infers AND reproduces" engine. The byte/glyph inference sketch is now coherent: byte/glyph core (F864) + M-resonator no-bag (F865) + sharp/smooth composition (this) + distribution (F867) + exact-rational (F868) + coupling-walk order (F863). **Next on this path:** (item 3) port the byte/glyph `enc` into `ContextSubstrate` with its C peer (UPSTREAM §60, parity rule); (item 4) corpus scale + per-store gate calibration + chunked-M (F839 sweet-spot C); and the semantic-similarity axis for non-structural generalization. (Retrofit to native `(num,den)` returns when the srmech rational-by-default breaking change lands, UPSTREAM §61.) Framework reading + srmech measurement; evaluate by groundedness; toy-scale + structural-generalization stated honestly.
