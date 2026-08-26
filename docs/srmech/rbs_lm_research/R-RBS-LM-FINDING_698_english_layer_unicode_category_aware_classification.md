# Finding 698 — the english layer must CLASSIFY Unicode characters (not just support other scripts)

**Script:** `R-RBS-LM-UNICHARS_english_layer_unicode_category_aware_classification.py`
**Status:** VERIFIED (srmech 0.6.0rc8 runtime)
**User catch:** *"right but the english layer also needs to know what unicode characters are."*

## The point — sharper than F696

F696 added **per-script** seen-rules (a Latin rule, a CJK rule, …). But the **english/latin rule itself was still
ASCII-only**: it used `", "` / `". "`, `.strip(".,:;()")`, and `.split()`. **English text is not ASCII.** It is full of
Unicode — accented borrowings (*café, naïve, résumé, Zürich, Gödel*), smart quotes (`" "`), em-dashes (`—`), ellipses
(`…`), emoji. So **every** script rule, the English one *first*, must **classify characters by their Unicode category**,
not by ASCII membership. The seen-rule layer has to *know what each Unicode character is*.

## The fix — `unicodedata.category` (stdlib character metadata)

| category family | meaning | role |
|---|---|---|
| `L*` (Lu/Ll/Lt/Lm/Lo) | letter | word char — covers `é`, `ï`, `λ`, `字`, `ا` |
| `M*` | combining mark | word char (an accent on a base letter) |
| `N*` | number | word char (digits) |
| `P*` (Pc/Pd/Ps/Pe/Pi/Pf/Po) | punctuation | boundary — incl. `—` `…` `" "` `« »` `。` `،` (not just ASCII) |
| `Z*` (Zs/Zl/Zp) | separator | boundary — incl. NBSP `U+00A0`, em-space |

A Unicode-aware tokenizer keeps runs of letter|mark|number and treats everything else as a boundary.

**Verified** — on `She sipped a café, "naïve" she said—résumé in hand…`:
- ASCII tokenizer: `['She','sipped','a','café','"naïve"','she','said—résumé','in','hand…']` — **`said—résumé` fused**, `hand…`
  keeps the ellipsis, smart-quoted word keeps `" "`.
- Unicode-category tokenizer: `['She','sipped','a','café','naïve','she','said','résumé','in','hand']` — **correct**: `café`/
  `naïve`/`résumé` whole (é/ï are Unicode letters), the em-dash/ellipsis/smart-quotes are boundaries.
- Classification: `é`→Ll(letter), `"`→Pi(punct), `—`→Pd(dash), `…`→Po(punct, sentence-terminator), NBSP→Zs(space),
  `字`→Lo(letter), `5`→Nd(number), `🌀`→So(symbol).

Updated `storyteller_bone/descriptors/script_rules.toml`: every script gains `word_segmentation = "unicode"` (runs of
Unicode letter|mark|number, *not* `.split()`) + a `sentence_terminators` set in Unicode (`.!?…` / `。！？` / `؟۔` / …).

## Why this is the framework's own discipline

This is **R-RBS-LM-25 "strip English privilege" at the character level**: the ASCII assumption *was* the English privilege.
The **byte foundation** (F613, content-address over UTF-8) is unicode-*complete*; the **seen-rule layer** must be unicode-
*character*-aware (this, F698) **and** per-script (F696). Both are needed.

**Dignity (F282/F398/F650/#847):** we scaffold the *mechanism* (which characters are letters/punctuation/space) only — the
per-script *grammar* belongs to that script's speakers.

**Composes:** F696 (per-script rules — F698 makes each one Unicode-character-aware) · R-RBS-LM-25 (strip English privilege,
now at the character level) · F613 (the byte foundation) · F398/F610/F645 (no-privilege / glyph universality) · F695 (the
bone — updates `script_rules.toml`) · `unicodedata` (character metadata). → extended by F699 (the word-meaning rung).

*Held open (F394). Reference scaffold; not a package edit.*
