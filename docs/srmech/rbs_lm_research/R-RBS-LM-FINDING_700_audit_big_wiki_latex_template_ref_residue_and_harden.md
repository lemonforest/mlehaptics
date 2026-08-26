# Finding 700 — was the big-wiki kernel stripped of LaTeX? NO. Audit + harden.

**Script:** `R-RBS-LM-WIKISTRIP_audit_big_wiki_latex_template_ref_residue_and_harden.py`
**Status:** VERIFIED — the worry is confirmed; the fix is built (srmech 0.6.0rc8 runtime)
**User catch:** *"also if big wiki was not recently encoded, are we sure it was not stripped of latex and things?"*

## The honest answer: NO, we were not sure — and the worry is correct

Two compounding gaps in F690's `strip_wiki_markup`:

1. **It is a DEMO stripper** that does only three things — `[[a|b]]`→b (links: OK), `{{…}}`→drop (templates: **single-level
   only**), and `<…>`→drop the **tag**. That last one is the leak: it drops the `<math>` **tags** but **leaves the LaTeX
   content** — `<math>v=\sqrt{\frac{GM}{r}}</math>` becomes raw `\sqrt{\frac{GM}{r}}`, so `sqrt`/`frac`/`displaystyle`
   become **vocab tokens**. A **bare** `<ref>Hubble 1929…</ref>` likewise leaves its citation text. Tables (`{| … |}`),
   ext-links (`[http://… label]`), and nested templates all leak too.
2. **It was only ever RUN on the clean hand-written demo corpus** (galaxy/shell/helix sentences) — which contains **no**
   `<math>`, no `<ref>`, no tables, no nested templates. **The LaTeX/markup path was never exercised.** The clean F690/F697
   numbers are clean *only because the demo corpus had nothing for the stripper to fail on* — the logic is sound, the
   cleaning was not tested.

## Why it matters — grounding honesty (F640/F688)

A kernel built from un-cleaned wiki text carries **unattested junk tokens** (`displaystyle`, `cite`, `wikitable`, `http`) in
its vocabulary. Those are **not words** — so every Class-L association formed with them is **spurious** (co-occurrence with
*markup*, not with *meaning*). The story would "ground" a beat in markup noise — breaking the chord (F658) at the
corpus-cleaning layer. This is the same grounding honesty the whole Story Teller rests on, one level down.

## The fix — a hardened stripper (verified)

Remove the **content** of content-bearing blocks (not just their tags), in order:
1. `<!-- … -->` comments (DOTALL)
2. `<math>/<ref>/<code>/<syntaxhighlight>/<score>/<chem>/<hiero>/<gallery>/<timeline> … </…>` — **whole element incl. inner
   text** (+ self-closing `<ref … />`)
3. wiki tables `{| … |}` (iterate to fixpoint)
4. templates `{{ … }}` — **iterate to fixpoint** so nested `{{a{{b}}c}}` fully clears
5. `[[a|b]]`→b ; `[http://x label]`→label ; bare ext-link→drop
6. any remaining tag (now safe)
7. emphasis `'''`/`''`, headers `==`, list/table bullets

**Verified** on a real markup sample (`<math>` LaTeX + a **bare** `<ref>` + a template-wrapped `<ref>{{cite web}}</ref>` +
`{| wikitable |}` + `<!-- comment -->` + `== header ==` + `[http ext-link]`):

| stripper | tokens | distinct junk markup tokens |
|---|---|---|
| F690 demo | 56 | **9** — `citation, class, displaystyle, footnote, frac, http, hubble, sqrt, wikitable` |
| hardened | 32 | **0** |

(Honest detail: the *template-wrapped* `<ref>{{cite web}}</ref>` happened to be caught by the `{{…}}`-drop — but the
**bare** `<ref>Hubble plain citation…</ref>` leaked as `hubble`/`citation`/`footnote`, which is the real-world leak the
audit had to actually exercise. I'd initially over-claimed the wrapped-ref leaked; corrected the sample to demonstrate the
true path — F573.)

## Consequence + the real target

- **The big-wiki kernel must be RE-ENCODED with the hardened stripper before its vocab is trusted.** F690/F697's
  conclusions about the *mechanism* (gap → query → grounded beat) stand; only the *corpus cleaning* was untested.
- **The real target is the F579/F607 wiki-formatting-language kernel** (the dev session) — the full form-tier
  (`[[link]]` 98% / `{{template}}` 94% / emphasis / header / `<ref>` / table) plus the determinative-routed sub-language
  family (`{{lang|xx}}`, `{{IPA}}`, `<code>`, `<chem>`, `<score>`, `<hiero>`). This script is a reference scaffold, per
  F690's own docstring.

**Composes:** F690/F697 (the big-wiki kernel — this audits its cleaning) · F698 (the Unicode tokenizer used here) ·
F640/F688 (no-magic / grounding honesty) · F573 (the honesty audit — and the corrected over-claim) · F579/F607 (the real
formatting-language-kernel target) · F695 (the bone). Backlinks F690 (`→ cleaning audited + hardened by F700`).

*Held open (F394). Reference scaffold; not a package edit.*
