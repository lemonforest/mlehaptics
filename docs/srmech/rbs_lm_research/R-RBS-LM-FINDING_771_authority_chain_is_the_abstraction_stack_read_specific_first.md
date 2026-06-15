# F771 — the resolver's authority chain IS the abstraction-layer stack read specific-first: glyph is lowest *because* it is the universal (all-languages) base

**Date:** 2026-06-15 · **srmech:** 0.7.5rc155 · **Composes:** F769 (the USAGE > LOCALE > GLYPH resolver — this finding explains WHY that order), F761 (the ni-Vanuatu glyph base = the language-AGNOSTIC layer every language projects from — confirmed: `GLYPHS` is "the universal base", `_word_hv` builds from `_glyph`), F770 (declare the structure — the chain should be a declared ordered list), F759 (the running-context = the USAGE layer), DUALITY.md (universal field vs local excitation) · **User direction (2026-06-15):** "glyph is lowest authority because it is the first layer that we can abstract into all languages. that should mean that authority is an ordered chain and this is how we sit en_US or en_GB at the language layer, before the simple wiki … it only looks at other locales if it's missing from knowledge structure (wiki)."

## The realization (and it checks out)
The resolver's precedence is NOT arbitrary — it is **the abstraction-layer stack of the language, read most-specific-first.** Authority is **inverse to universality**: the more universal a layer (the more languages it spans), the LESS authority it has for resolving a *specific* token; the more specific/immediate (this conversation), the more.

**The stack (built bottom-up) vs the authority (read top-down):**
```
   build-up (foundational → surface)          AUTHORITY (most-specific wins)
   ─────────────────────────────────          ──────────────────────────────
   conversation / USAGE   (most specific)  ▲   1. USAGE      (the user's own words, F759)
   knowledge / WIKI       (content)        │   2. KNOWLEDGE  (routable in the store)
   language / LOCALE      (en_US/en_GB)    │   3. LOCALE     (language-specific convention)
   ni-Vanuatu / GLYPH     (all languages)  │   4. GLYPH      (the universal base — lowest)
```
**Glyph is lowest precisely because it is the ni-Vanuatu universal base** (F761) — the very property that makes it the language-agnostic pivot (every language projects from it) is what makes it the least authoritative for a specific word: it knows *shape across all languages*, not this-language-this-context truth. Its universality = its last-resort-ness.

## Confirmed against the build
- **GLYPH = the universal base, literally.** `_word_hv` → `_glyph` over `GLYPHS` ("the ni-Vanuatu abstract glyph alphabet (the universal base)"). The glyph resolver matches in the language-agnostic substrate. ✓
- **LOCALE sits at the language layer, consulted only on a knowledge-miss.** `_resolve_canonical` reaches the locale tier only for tokens that are NOT routable (not in the wiki/knowledge store). So in authority, **KNOWLEDGE > LOCALE** (wiki checked first, locale is the fallback) — exactly "only looks at locale if missing from wiki." In the STACK, locale/language is *beneath* the knowledge expressed in it; in authority (specific-first) knowledge outranks it. ✓
- **USAGE is the resolver's top tier.** `_resolve_canonical` checks the running context + learned store before locale/glyph. ✓

## The one honest nuance (where the build doesn't yet fully match the ideal)
In the CURRENT pipeline the **knowledge (routable) check runs BEFORE the usage tier** — the resolver only fires for *unroutable* tokens. So the realized order is **KNOWLEDGE > USAGE > LOCALE > GLYPH**, whereas the ideal "USAGE is the most-specific, absolute top" would be **USAGE > KNOWLEDGE > LOCALE > GLYPH**. The two **coincide for typo-resolution** (usage > locale > glyph, all beneath knowledge-routing). They **diverge only** for the case where the user's recent usage should override a token that IS a valid store word (e.g., the user consistently writes "colour", route it as their canonical even though "color" is the store key) — the **display/routing split queued in F769**, not yet built. So the model is right; the build realizes it everywhere except that one top-of-chain override.

## The structural lesson (composes F770)
The precedence is currently three hardcoded `if`-branches in `_resolve_canonical` plus the routable pre-gate. The realization says it should be a **declared, ordered chain of layers** (specific → universal), each with a resolve attempt — exactly the F770 move (*declare the structure*; the chain IS the operator-grammar of resolution). Making it explicit would (a) match the architecture 1:1, (b) be extensible (insert a layer = insert in the chain — e.g. a future per-user dialect layer between USAGE and LOCALE), (c) be legible/introspectable. The ordering is the abstraction stack; the code should say so.

## Verdict
**Yes — it makes sense, and it's a real principle, not just a precedence.** The resolver's authority chain IS the language's abstraction stack read most-specific-first: **USAGE > KNOWLEDGE(wiki) > LOCALE(en_US/en_GB) > GLYPH(ni-Vanuatu)**. Glyph is lowest *because* it is the universal all-languages base (confirmed literally in code); locale sits at the language layer and fires only on a knowledge-miss (confirmed); usage is the resolver's top, with the full "usage overrides a valid routable word" override still queued (F769 display/routing split). Next inch: make the chain a **declared ordered list of layers** (F770 — declare the structure) rather than hardcoded branches.
