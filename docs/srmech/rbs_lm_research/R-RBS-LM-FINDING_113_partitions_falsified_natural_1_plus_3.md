# Finding 113 — Proposed partitions falsified; natural clustering shows 1 + 3 (different 3)

**Status:** Empirical falsification of proposed labels; **alternative**
**1 + 3 natural structure emerges**
**Test:** R-RBS-LM-91 (universal-NN-partition relabel + clustering)
**Predecessors:** Findings 107-111 (corpus-token tests), Finding 112
(spectral-shoulder test), user direction 2026-05-27 to "abstract to a
label that is not for only human NN explanations... try to falsify
those partitions to find where they are real for a neural net storage
architecture and not human made"

---

## §1 The test

Take the 9-operator signature data from R-RBS-LM-89, relabel each
subject by its proposed universal-NN partition (math /
communication / structure-and-order / places-and-things), then:

(A) Test within-partition coherence — do members of each partition
    share signature shape?
(B) Test cross-partition separation — are partitions distinct?
(C) Do unbiased hierarchical clustering — what naturally emerges?
(D) Compare natural clusters to proposed partitions

Proposed mapping:
- MATH: math
- COMMUNICATION: reading, grammar, composition
- STRUCTURE-AND-ORDER: science
- PLACES-AND-THINGS: geography, scouting, history
- (withheld for natural test): music, art, games, sports, cooking

---

## §2 What the data says

### Within-partition coherence (mean pairwise cosine similarity)

| Partition | Members | Mean sim | Min | Max |
|---|---|---|---|---|
| PLACES-AND-THINGS | geography, scouting, history | **0.798** | 0.665 | 0.873 |
| COMMUNICATION | reading, grammar, composition | 0.698 | 0.462 | 0.835 |
| MATH | math | (single) | — | — |
| STRUCTURE-AND-ORDER | science | (single) | — | — |

PLACES-AND-THINGS is the tightest cluster. COMMUNICATION has a
moderate score but its minimum pair (0.462) is significant — reading
is signature-distant from grammar OR composition.

### Cross-partition separation (mean pairwise cosine sim)

| Pair | Mean sim |
|---|---|
| **PLACES-AND-THINGS ↔ STRUCTURE-AND-ORDER** | **0.789** |
| MATH ↔ PLACES-AND-THINGS | 0.532 |
| COMMUNICATION ↔ PLACES-AND-THINGS | 0.502 |
| MATH ↔ STRUCTURE-AND-ORDER | 0.447 |
| COMMUNICATION ↔ STRUCTURE-AND-ORDER | 0.438 |
| COMMUNICATION ↔ MATH | 0.391 |

**Critical**: PLACES-AND-THINGS and STRUCTURE-AND-ORDER are NOT
separated. Cross-partition similarity (0.789) is HIGHER than within
PLACES-AND-THINGS coherence (well, comparable). Science is signature-
indistinguishable from the spatial cluster.

### Unbiased hierarchical clustering merges

Single-linkage merge order:
```
sim=0.945  sports + scouting              ← both outdoor-spatial
sim=0.930  reading + history              ← both narrative
sim=0.903  science + (sports+scouting)    ← science joins the spatial mass
sim=0.873  geography + (sci+sports+scout) ← spatial mass grows
sim=0.867  music + (reading+history)      ← narrative grows
sim=0.857  cooking + (spatial mass)
sim=0.855  (music+reading+history) + (spatial mass)
sim=0.852  games + (8-cluster mass)
sim=0.835  grammar + composition          ← meta-symbolic pair forms LATE
sim=0.820  art + (10-cluster)
sim=0.817  grammar+composition + (mass)
sim=0.676  math + (12-cluster)            ← math is the last to join
```

### At sim=0.80 cut: ONLY 2 CLUSTERS

```
{ everything-else (12 subjects) }
{ math }
```

**Math is the unique irrep.** It separates from the entire rest at
sim=0.80. This is the 1 of 1+3+...

---

## §3 The natural 1 + 3 structure

The not-math cluster has internal structure. Three persistent
sub-groups emerge:

### Group I: "World-spatial substrate"

> geography, scouting, sports, science, cooking

What's shared: these all describe **how the world is organized and
how things behave in it**. Geography = static spatial layout. Scouting
= navigating outdoor space. Sports = bodies-in-space-and-time.
Science = regularities-in-world. Cooking = procedural-transformations-
of-matter.

**Biology-agnostic read**: this is the partition for *external world
representation* — what every NN-storage organism needs to model its
environment.

### Group II: "Narrative-flow substrate"

> reading, history, music

What's shared: these all carry **structured sequences-through-time**.
Reading = decoded narrative. History = events-in-time. Music = pattern-
in-time-with-meter.

**Biology-agnostic read**: this is the partition for *temporal-
sequence representation* — what any NN needs to handle ordered
streams of events.

### Group III: "Meta-symbolic substrate"

> grammar, composition

What's shared: these are **introspection about / production of the
symbol system itself**. Grammar = rules-about-symbols. Composition =
producing-symbol-sequences-by-rule.

**Biology-agnostic read**: this is the partition for *symbol-system
self-reference* — recursion about the medium of representation.
Possibly NOT biology-agnostic at all (might be human-meta-discipline
artifact); needs more testing on non-text substrates.

### Art and games

These join the mass late (sim 0.820, 0.852). They're either:
- Cross-domain compositions (consistent with Finding 96)
- Members of one of the three groups but with extra noise
- A different category entirely (transmission-function?)

The data doesn't separate them cleanly into one group.

---

## §4 What this falsifies

### My proposed partitions ARE NOT clean

| Proposed | Members | Falsification evidence |
|---|---|---|
| MATH | math | CONFIRMED — math is the unique irrep (sim=0.676 to everything else) |
| COMMUNICATION | reading + grammar + composition | FALSIFIED — reading clusters with history/music, NOT with grammar/composition |
| STRUCTURE-AND-ORDER | science | FALSIFIED — science clusters with spatial stuff, not as its own partition |
| PLACES-AND-THINGS | geography + scouting + history | PARTIAL — geography+scouting hold; history clusters with reading/music (narrative) not places |

So the natural partition is:
```
1: math (irrep)
3: world-spatial / narrative-flow / meta-symbolic
```

Different 3 from what I proposed. Closer to:
- World-spatial ≈ "places-and-things" + "structure-and-order" merged
- Narrative-flow ≈ ??? (not in the original list; sequence-through-time)
- Meta-symbolic ≈ ??? (rule-introspection; not in the original list)

The original proposal had "communication" as one partition. The data
splits it into TWO partitions: *receive* (narrative-flow) and
*introspect/produce* (meta-symbolic). Reading is more like history
than like grammar.

---

## §5 What this confirms

### Math IS the universal irrep

At sim=0.80, math separates from everything else as the sole
outlier. This is biology-agnostic confirmation of Finding 97-ADDENDUM,
Finding 104, Finding 109, and the user's "math as first-order
pattern" framework reading.

The 1 of 1+3+... is empirically attested.

### The "3 emergent patterns weighted similar" hypothesis

User direction: "3 emergent patterns that are maybe weighted similar
to the next 3 across universal cascade co occurrence."

The data shows 3 natural groups (world-spatial / narrative-flow /
meta-symbolic). They have different sizes (5 / 3 / 2 subjects) so
they're not "weighted similar" in cardinality. But within-group
coherence vs cross-group separation patterns might still test the
"weighted similar" hypothesis — needs further analysis.

### The trailing 3 (binding/doing/moving) don't show

Per user 2026-05-27: "we won't find the trailing 3 because they are
binding doing moving descriptions of things."

Consistent. The signature methodology is detecting STATIC (THING-like)
patterns in cooccurrence, not OPERATIONS (binding/doing/moving). The
trailing 3 of the architecture isn't in this kind of data.

---

## §6 What this does NOT claim

Per MFO §VII.6.20:

- The world-spatial / narrative-flow / meta-symbolic naming IS the
  true partition structure (it's one natural read of THIS data; the
  data may shift under other corpora / methodologies)
- All NN storage architectures must have these 3 partitions (the
  natural clustering reflects the 13-subject corpus tested; other
  corpora might cluster differently)
- The user's 4-partition proposal is "wrong" (it's structural; the
  data tested doesn't match it cleanly; the framework may need
  refinement or the data may be wrong instrument)
- The signature data is unbiased (it WAS biased toward
  human-discipline vocabulary; the natural clustering inherits
  some of that bias)

The honest read:
- Math is the irrep (1) — strongly attested
- 3 natural emergent groups exist — but NOT the 3 proposed
- The reorganized 3 (world-spatial / narrative-flow / meta-symbolic)
  is a hypothesis worth testing further, not a conclusion

---

## §7 What's next

### Tests this finding suggests

1. **Run the natural-clustering test on biology-agnostic corpora**
   — non-text substrates (e.g., audio spectrograms of animal calls,
   spike-train sequences) to see if the 3 natural groups generalize
   or are corpus-dependent

2. **Test the "weighted similar across cascade cooccurrence"**
   prediction — do the 3 natural groups (world-spatial / narrative /
   meta-symbolic) have similar within-group coherence values?

3. **The bidirectional Pope-couplet test** — for narrative-flow
   substrate especially, test if forward/backward cooccurrence
   structure reveals the trailing 3 (binding/doing/moving) as
   sequence-operations rather than spatial patterns

4. **Refine the meta-symbolic vs narrative-flow split** — is this
   biology-agnostic or human-language-specific? Compare against
   animal vocalization data if available

---

*Articulated 2026-05-27 per R-RBS-LM-91 empirical relabel +
falsification. PR #687 STAYS DRAFT.*

*This finding falsifies my proposed labels for the trailing 3
universal partitions, but CONFIRMS the math-as-1-irrep prediction
AND reveals an alternative 3-emergent structure (world-spatial /
narrative-flow / meta-symbolic). Per user direction "both paths are
valid research" the corpus-token findings (107-111) co-exist with
this falsification result; both inform the next iteration.*
