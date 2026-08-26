# Finding 714 — the etak walk stays specific: a three-layer fix (function-word stoplist + IDF + hub exclusion)

**Script:** `R-RBS-LM-ETAKIDF_inverse_frequency_hop_weighting_keeps_the_walk_specific.py`
**Status:** VERIFIED on the uncapped kernel (srmech 0.7.5rc28)
**User direction:** *"the etak-walk stoplist/inverse-freq fix."*

## The F709 artifact and what actually fixed it (honest, F573)

F709's etak walk drifted into hub words (`planet → earth → sun → around → world → war`). I tried the obvious fixes and they
each caught a **different class** — and only together do they keep the walk specific:

1. **Inverse-frequency hop weighting** — `hop_score = edge_weight × IDF(nbr)`, `IDF(w)=log(total/freq(w))`. This **sharpened
   the beats** (surfaced specific neighbours: `dwarf`, `eclipse`, `vapor`) but **did not stop the drift** — `around` still
   got walked. IDF alone is half the fix.
2. **Frequency-derived hub-stoplist** (exclude the top-40 by frequency) — but in this corpus the top-40 are *corpus-specific*
   stubs (`actor`/`footballer`/`american`/`british`…), so it **missed** the generic mid-frequency function word `around`.
3. **The real leak: `around` was a function word missing from `DEFAULT_STOPLIST`.** Adding `around` (+ the other prepositions
   I'd missed: `across/along/toward/onto/within/among/against/throughout`) to the language stoplist was the single biggest
   fix.

**Verified after the three layers** — the `planet` chapter now stays in astronomy even *plain*:
> the planet is seen with the earth, the solar, the system →
> the earth is seen with the sun, the water, the moon →
> the sun is seen with the earth, the planets, the moon →
> the planets is seen with the solar, the system, the earth →
> the solar is seen with the system, the planets, the **eclipse**

No more `around → world → war` drift. With IDF the beats sharpen further (`dwarf`, `eclipse`).

## The principle

The three layers catch three distinct classes of "uninformative hop":
- **language function words** (`around`, prepositions) → the **stoplist** (a language-level fix, now in `DEFAULT_STOPLIST`);
- **corpus-specific hubs** (biography stubs) → **frequency hub-exclusion** (a corpus-level fix);
- **everything else generic** (`world`, `people`) → **IDF down-weighting** (a soft, principled re-scale — a Class-N rational
  re-weight of the Class-L co-occurrence; it's a *ranking* weight, not a stored cascade value, so plain `log` is fine).

The chord (F658) and the attested edges are unchanged — only the **hop choice** is sharpened; nothing is invented
(F640/F688). This is more principled than the crude single hub-stoplist F690 started with.

**Composes:** F709 (the artifact) · F708 (the uncapped kernel) · F704 (the etak walk) · F690 (the kernel; `DEFAULT_STOPLIST`
extended) · F658/F661 (chord / asking-state) · F640/F688 (no-magic / no-invention). srmech 0.7.5rc28. Held open (F394).
