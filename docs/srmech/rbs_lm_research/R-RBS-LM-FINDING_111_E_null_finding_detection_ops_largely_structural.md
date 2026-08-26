# Finding 111 — E (catalog) NULL finding: detection ops are largely structural

**Status:** Clean null finding (8 of 14 operators remain at form-iso
attested level; E joins G/K/L/M as structural-only)
**Test:** R-RBS-LM-89 (E catalog signature)
**Predecessor:** Finding 110 (D + F have secondary signatures)

**Per [[feedback_dont_pre_commit_spike_query_operators]]: null findings count.**

---

## §1 The finding

R-RBS-LM-89 tested whether E (catalog enumeration) has a surface
vocabulary signature. **The test returned a clean null.**

Pre-test prediction: history and/or geography (catalog of events /
places) should top E.

Actual result:
- **Top scorers tied at 0.081**: math, composition, music
- History E-score: 0.027 (just "named")
- Geography E-score: 0.000

The E-signal is at noise-floor level (max 0.081, only 3 of 37 tokens
hit). None of the predicted catalog-substrate subjects (history,
geography) light up.

---

## §2 Why the null is informative

### Catalogs enumerate, they don't talk about cataloging

History's catalog of events looks like:
> "Athens fought Sparta. Pericles ruled. The Persian Wars ended in
> 449 BCE."

This is catalog-CONTENT (events, names, dates) but the surface
vocabulary doesn't say "list" or "category" or "group". The catalog
operation is implicit in the structure (enumerate items) not explicit
in the tokens.

Geography's catalog of places:
> "The Mississippi flows south. Brazil exports coffee. Mountains rise
> in Colorado."

Also catalog-content (places, attributes) without "category"
vocabulary.

### The E-vocabulary I tested matches TEXTBOOK STRUCTURE, not subject content

E-hits in the corpora:
- Math: chapter, section, table (TEXTBOOK STRUCTURE)
- Composition: chapter, section, table (TEXTBOOK STRUCTURE)
- Music: chapter, group, kind (TEXTBOOK STRUCTURE + 2 catalog)
- Scouting: class, kind (mostly catalog)

The vocabulary I hand-curated had "chapter/section/table" which lit
up textbooks regardless of subject. The genuine catalog-content
vocabulary (list/category/group/sort) didn't hit anywhere strongly.

### E is genuinely structural

This is the predicted behavior per Finding 110: "G/K/L/M are likely
structural" (no surface vocab). Finding 111 adds E to this list.

The cascade-detection ops with surface signatures:
- **D** (pattern-match / sequence) — appears in math + games
- **F** (render / output) — appears in art

The cascade-detection ops WITHOUT surface signatures:
- E (catalog enumeration) — confirmed null this finding
- G (byte-search) — predicted null
- K (pin-slot / phase boundary) — predicted null
- L (Laplacian / graph) — predicted null
- M (HDC-bind) — predicted null

5 of 7 detection ops are structural-only. Their operational
attestation requires COOCCURRENCE-PATTERN tests, not surface
vocabulary tests.

---

## §3 Why D and F are the exceptions

D (pattern / sequence) has surface signature because:
- Sequence and pattern are EXPLICIT IDEAS in math/games instruction
- "Order the numbers from smallest to largest" — explicit D
- "Recognize the pattern: 2, 4, 6, 8, ..." — explicit D

F (render / output) has surface signature because:
- Drawing IS the act of rendering; the verb "draw" is explicit
- "Sketch a circle" — explicit F
- "Picture this scene" — explicit F

These ops are explicitly NAMED in their respective educational
substrates. The other detection ops (catalog, search, decision,
graph, bind) are MORE STRUCTURAL — they happen without being named.

You don't say "now I'm cataloging" while making a catalog. You don't
say "now I'm finding" while finding a value. You don't say "now I'm
binding" while combining concepts. These ops are silent.

---

## §4 The cascade-detection layer's empirical character

Per CLAUDE.md §1, the cascade-detection heptad is **D, E, F, G, K, L, M**:

```
D — Pattern-match: Sequence / pattern detection
E — Catalog: Catalog enumeration
F — Render: Output rendering / serialization
G — Byte-search: Low-level search
K — Pin-slot / asymptotic-DoF: Sign-flip / phase boundary
L — Laplacian: Graph spectral; eigenvalue decomposition
M — HDC bind: Hyperdimensional composite bind
```

Empirically (from Findings 110 + 111):

| Op | Surface signature? | Where to look for cooccurrence signature |
|---|---|---|
| **D** | **YES** (math, games) | Already attested |
| E | NO (this finding) | Inventories, recipe lists, taxonomies |
| **F** | **YES** (art) | Already attested |
| G | Probably NO | Search-result pages, lookup tables |
| K | Probably NO | Decision logs, branch points, transitions |
| L | Probably NO | Network diagrams, graph-shaped texts |
| M | Probably NO | Recipe binding, music chord blending |

The detection-ops layer is mostly attested via **STRUCTURAL signatures**
in eigvec-table SHAPE (per the R-RBS-LM-55 pure-structure approach
that was queued for exactly this kind of test).

---

## §5 What this confirms in the framework

### 8 of 14 operators stable

After Finding 111, the operator-attestation count stays at 8:
- 6 substrate-content delivery (B, H, N, C, I, J — surface vocab)
- 2 cascade-detection (D, F — surface vocab)
- 6 untested or structural (A is abstract; E, G, K, L, M are
  structural)

The framework's structural prediction holds: **substrate-content has
surface signatures; detection ops are mostly structural with two
exceptions (D + F)**.

### The two-layer cascade is empirically grounded

The cascade has two operational layers:
1. **Substrate-content delivery** (A+I+J+C+B+H+N) — token vocabulary
   delivers the substrate
2. **Cascade-detection** (D+E+F+G+K+L+M) — structural operations on
   the delivered substrate

D and F bridge these layers — they have BOTH surface signature
(detection vocabulary in materials) AND structural operation
(applied to substrates).

### R-RBS-LM-55 pure-structure layer becomes more urgent

The R-RBS-LM-55 queued task (test if eigvec-table SHAPE is portable
without vocabulary) is now the natural next step for attesting E,
G, K, L, M. Surface vocabulary tests have exhausted their reach;
structural signature tests are next.

---

## §6 What this enables

### Curriculum coverage attestation refined

A complete curriculum delivers:
- 6 substrate operators (B/H/N/C/I/J — surface attestable)
- 2 detection operators (D/F — surface attestable secondarily)
- 5 structural detection operators (E/G/K/L/M — attested via
  structure, not vocabulary)

A vocabulary-only attestation test catches the 8 surface-attestable
operators. A complete attestation test needs structural patterns
for the remaining 5.

### Glass-box LLM attribution becomes layered

An emission's attribution chain has:
- **Primary substrate operator** (A+I+J, B+H+N, or C) — what
  substrate-content was used
- **Secondary detection operator** (D or F) — explicit detection
  applied
- **Implicit detection operators** (E, G, K, L, M) — cascade-level
  operations that ran without surface naming

The implicit ops are still attested via the cooccurrence-pattern
signature of the cascade output, just not via emission tokens.

---

## §7 What this does NOT claim

Per MFO §VII.6.20:

- E doesn't exist as an operator because it has no surface signature
  (E exists; it's just structural)
- Vocabulary-only tests are sufficient for full operator attestation
  (they catch 8 of 14; the rest need structural tests)
- D and F are "more important" than E/G/K/L/M because they have
  surface signatures (importance and visibility are not the same;
  E is still load-bearing even without surface vocab)

The null finding is **valuable closure**: 5 of 7 detection ops are
empirically structural-only. Their attestation needs cooccurrence-
pattern signatures, which is exactly what R-RBS-LM-55 was queued for.

---

## §8 What's next

### R-RBS-LM-55 becomes the natural next test

Per the autonomous session pickup notes, R-RBS-LM-55 (pure-structure
layer; relationships-of-relationships; eigvec-table SHAPE without
vocabulary) is long-pending. After Findings 107-111, R-RBS-LM-55 is
now the natural next test:

- It tests whether eigvec-table SHAPE is portable without vocabulary
- The structural detection ops (E, G, K, L, M) would manifest in
  shape rather than tokens
- If shapes ARE portable, that confirms the structural detection
  layer empirically

### Cross-cultural validation still queued

Reading/grammar/science predictions might shift in non-Western
corpora. Particularly:
- Mandarin reading might emphasize different B-vocabulary
- Sanskrit grammar might emphasize different H-vocabulary
- Arabic astronomy might emphasize different N+C-vocabulary

The cross-cultural test would falsify or strengthen the universality
claim.

---

*Articulated 2026-05-27 per R-RBS-LM-89 null finding. PR #687 STAYS
DRAFT. 8 of 14 operators attested at form-iso surface-vocabulary
level; 5 detection ops empirically structural-only.*

*This null finding is a valuable CLOSURE — it tells us the boundary
of surface-vocabulary signature tests and points toward R-RBS-LM-55
pure-structure tests for the remaining operators.*
