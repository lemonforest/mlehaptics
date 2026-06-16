# F791 — the smallwiki is now WALKABLE: the tome-TREE (paths) + cut-edge WEB are persisted, and etak navigation (FIND→RIDE→ZOOM→WEB-HOP) is wired into Siona — the F780 clumps-of-clumps + webs, live as a navigation command

**Date:** 2026-06-16 · **srmech:** 0.7.5rc166 · **Composes / completes:** F789 (#1 — the full-vocab native clump; this adds tree+web persistence + the navigation), F780 (clumps-of-clumps + webs — both now PERSISTED + WALKED), F778, F786 (de-lensing) · **User direction (2026-06-16):** "(1) persist the tree (parent pointers) + the inter-tome web; (2) wire it into Siona's loopshelf routing — etak FIND→RIDE→WEB-HOP; (3) quality tuning — fresh windowed co-occurrence source, MAXTOME, H_DROP." · **Provenance:** `R-RBS-LM-FULLCLUMP_…py` (persist) + `R-RBS-LM-SIONAGENEPOOL_…py` (nav).

## (1) Persist the tree + web — DONE
`R-RBS-LM-FULLCLUMP` now persists, beyond the flat leaf partition: **`paths`** (each leaf's L/R tree address — so the PARENT clump = sibling leaves sharing `path[:-1]`, the zoom-out) and **`web`** (per tome, its top-3 bridge tomes by aggregated cut-edge weight + the strongest bridge word-pair). Full run: 90,370 words / 681,866 edges → **11,481 tomes in 19.6 s, 440 MB; 423,787 web tome-pairs**; persisted `simplewiki_tome_tree.json` (2.9 MB, OUTSIDE the repo, CC-BY-SA). This is F780's clumps-of-clumps (the tree) + webs (the cut edges), made durable.

## (2) Wire into Siona — DONE
A **NAVIGATE frame** (`navigate / explore / what's near / cluster of / walk …`) loads the tome-tree at startup (word→tome index) and answers with an etak walk:
- **FIND** the subject's leaf tome; **RIDE** = the clump's members; **ZOOM OUT** = the parent clump (sibling leaves sharing the path prefix); **WEB-HOP** = the strongest cut-edge bridge to another tome (+ the bridge word-pair).
- Live results: `explore star` → `{distances, stellar, bessel, catalogues, flamsteed, parallax}` → **WEB-HOP `bessel~dorpat` → {observatory, dorpat, stellarum}** (Bessel measured stellar parallax at Dorpat); `what's near dog` → canid genera `{chrysocyon, speothos, cerdocyon, maned}` → ZOOM `{lycaon, nyctereutes, cuon, dhole, tanuki}`; `navigate volcano` → `{eruption, mauna, kilauea, haleakala}` (`kilauea~dacite`); `navigate planet` → `{neptune's, triton}` → `triton~deuteron` (the moon↔nucleus polysemy bridging to physics).
- **Subject-selection fix (the F787 operator-leak class, again):** `navigate/explore/near/around/cluster/walk` were being picked AS the subject (they're in the tome vocab) — stoplisted, and the NAV subject now prefers a real gloss/relation word over a noise token. (`explore star` → *star*, not *explore*; `what's near dog` → *dog*, not *what's*.)

## (3) Quality tuning — partial (artifact filter done; fresh source = the remaining lever)
- **Artifact filter** added to the source: drop concatenation junk (overlong tokens, word+month merges like `bouncedecember`) + the rare floor (in-degree < 3). Cleaner than F789's first cut.
- **The honest limit:** coherence is **good for clearly-connected words** (astronomy, canids, volcanoes, instruments) and **noisy for others** — the ZOOM/web frequently surfaces other-language or tangential tokens because the SOURCE is the pre-built **assoc top-K**, which carries extraction noise and isn't a clean windowed co-occurrence. **A fresh windowed co-occurrence source graph (the user's #3) is the real quality lever and is NOT done here** — it is a dedicated multi-minute corpus pass (240k articles × the content-band vocab); flagged as the next focused/backgrounded run. MAXTOME (12) and H_DROP (300) are the other dials.

## Honest scope
- The navigation is real and end-to-end (FIND→RIDE→ZOOM→WEB-HOP over the persisted tree+web), coherent for well-connected subjects; the noise is inherited from the assoc source, not the method — the fresh-source rebuild is the named fix.
- Not yet redeployed to the live server (the running rc166 process predates the F790/F791 edits; a by-port restart makes the entity-resolve + navigation live).
- srmech-native (rc166 §51 for the clump; Class-L stores for nav); no numpy/abs/CAD; tome-tree OUTSIDE the repo (gitignored guard).

## Verdict
The smallwiki is now **walkable**: the tome-tree (paths/zoom) + cut-edge web are persisted (F780 made durable), and Siona answers a NAVIGATE command with an etak FIND→RIDE→ZOOM→WEB-HOP over them — coherent for clear subjects (Bessel/Dorpat parallax, canid genera, Hawaiian volcanoes), with meaningful polysemy bridges (triton↔deuteron). Items (1) persist and (2) wire are delivered; (3) tuning is partial (artifact filter in; the **fresh windowed co-occurrence source** is the remaining quality lever, a dedicated run). The uncapped, spectrally-navigable smallwiki is real and navigable end-to-end.
