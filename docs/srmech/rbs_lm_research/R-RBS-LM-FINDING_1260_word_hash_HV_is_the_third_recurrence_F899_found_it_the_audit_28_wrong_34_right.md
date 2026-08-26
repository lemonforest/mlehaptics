# F1260 — reaching for `klein4_random(seed=hash(word))` when you need a **Class-M content carrier** destroys morphology (everything sits at the 0.25 orthogonality floor), and **srmech's `tool_schema` says so with the worked number** — `klein4_encode_bytes` advertises *"Restores MORPHOLOGY (sim('cat','cats') ≈ 0.6)"*, measured here at **0.6597**. The information was discoverable. **The honest headline is worse than a discoverability gap: F899 found this a month ago, logged it as UPSTREAM §68, and its own title says "we forgot it, twice over" — this is the THIRD recurrence.** Audit: **28 word-hashed sites (wrong), 34 per-byte (correct), 26 state-address (legitimate).** + a correction to F1259's DERIVED category.

**User (2026-07-20):** *"this needs to be HV abstract, not genome centric. this would have been how we were supposed to learn to not use random seed HV when we need class-M … audit which sites are content vs roles."*

## The discriminator (D=8192, Klein-4)
| pair | `klein4_random(seed=sha256(w))` | `klein4_encode_bytes(w, D)` |
|---|---|---|
| cat / cats | **0.2552** | **0.6597** |
| walk / walked | 0.2593 | 0.7072 |
| nation / national | 0.2560 | 0.7428 |
| run / running | 0.2524 | 0.5643 |
| the / then | 0.2520 | 0.6548 |
| **cat / dog** (control) | 0.2426 | **0.2517** ✓ correctly at floor |

Hash-seeding puts **every** pair on the Klein-4 orthogonality floor: `cat/cats` (0.2552) is statistically indistinguishable from `cat/dog` (0.2426). Deterministic, reproducible — and an **arbitrary code** carrying zero sub-word structure. The composed encoder separates related from unrelated cleanly.

**Why, and it links to the sha256/glyph_stream question:** hash avalanche was measured at **48.77 %** of output bits per 1-character edit. That avalanche is *exactly* what destroys morphology — one character changes and the vector fully re-randomizes. **High diffusion is what makes a good ADDRESS and what disqualifies it as a REPRESENTATION.** Same axis, opposite requirement.

## THE CORRECTION TO F1259
F1259 classified `seed=sha256(content)` as **DERIVED — "not random at all, load-bearing."** That is right about *reproducibility* and **wrong about structure.** A hash-seeded HV is deterministic **and structureless**. The three-regime split needs a fourth distinction inside DERIVED:

| regime | reproducible? | structure-bearing? | correct use |
|---|---|---|---|
| **COMPOSED** `klein4_encode_bytes(data, D)` | yes | **yes** — morphology survives | **content** |
| **ADDRESSED** `klein4_random(seed=hash(x))` | yes | **no** — arbitrary code | **state/identity addressing**, never content |
| **ROLE** `klein4_random(seed=pos/role idx)` | yes | n/a — structurelessness is the *point* | position / role keys |
| **DRAWN** `klein4_random(seed=1080)` | yes | no | an unattested constant |
| **STOCHASTIC** `klein4_random(rng=…)` | **no** | no | a defect in a cascade |

So ADDRESSED is not wrong *per se* — it is wrong **for content**. Seeding by content-hash to get an *identity* is legitimate; seeding by content-hash to get a *representation* throws the content away.

## The audit — content vs roles
Scoped to our code (srmech internals and its tests excluded), classified by what the seed *is*:

| bucket | sites | verdict |
|---|---|---|
| **WORD-HASHED** — a whole lexical unit → one code | **28** | **morphology lost; the defect** |
| **PER-BYTE** — `seed=b` over the byte vocab | **34** | **correct** — this is what the composed op does internally |
| **COMPOSITE/state address** — `digest(tuple of numbers)` | **26** | **legitimate** — addressing a *state*, not representing a word |

**The split is not "47 wrong."** Roughly a third are genuinely wrong, and the majority are correct or legitimate.

**And the pattern in *which* arcs are wrong is diagnostic:** the entire **F864–F918 byte-glyph series does it right** (34 per-byte sites — the ni-Vanuatu base arc, exactly what F899 pointed at). The **word-level and genome-adjacent work regressed** to word-hashing. So the fix was applied in one arc and not carried across.

**Shipped code is affected.** `siona/siona/bridge.py:10` documents its design as `klein4_random(seed=hash(token))` recomputed on demand; `siona/infer.py:68` caches per-word vectors the same way. That is the F899 defect still live in the package.

## The recurrence — the part that actually matters
**F899 (2026-06-21, srmech rc13) measured this exact thing**: *"packaged encode is WORD-HASH (`sha256(whole word)` → one random vector), NOT the byte/glyph LM object … near-words are orthogonal (cat/cot 0.257, walk/walked 0.259 ≈ chance 0.25) vs the byte-composed core (0.560, 0.710)."* Logged as **UPSTREAM_NOTES §68**. Its title: *"FOUND (we forgot it, twice over)."*

So: found, measured, logged — **three times now**, and re-derived from scratch today. This is **F552 / TRIALITY §5 "we keep re-deriving the same structure at a different coherence"** made concrete a second time (F1211 was the first), and it says the failure is **not** discoverability of srmech's surface but **retrieval of our own finding record**. A STOP-list row fixes the reach; the breadcrumb-web is what should have surfaced F899 before I re-measured it.

## Was it discoverable in srmech? Yes — by exactly one route
| introspection route | would it have stopped the reach? |
|---|---|
| `describe()` | **No** — category counts only |
| docstrings on the consuming op | **No** — `the_one : HV`, "coupling invariant"; correct, but silent on *how to build one* |
| shipped examples | **No** — only `_carrier_examples.py`; no worked HV-for-content example |
| `dir(hdc)` | **Partially** — `klein4_encode_bytes` is visible; nothing says prefer it |
| **`tool_schema` registry summary** | **YES** — states the composition *and* the expected similarity |

**The trap is in the primitive's own doc.** `klein4_random`'s summary reads *"Pass an integer `seed` for a DETERMINISTIC vector (bit-exact / attestation discipline)"* — true, and the sanctioned path for role keys, but it advertises exactly the property (determinism + attestation) that a user seeking content-addressing discipline is hunting for, and never says a content-derived seed lands at the orthogonality floor.

## Verdict / next
The reach is fixed by a **point-of-action STOP-list row** (landing in `CLAUDE.md` §2 with this finding), not by a principle — the §2 preamble already documents why: a declarative "use srmech" loses to reflex at code-writing speed. **NEXT:** (1) repair the 28 word-hashed sites, `siona/bridge.py` + `infer.py` first since they ship; (2) upstream ask — a *see-also* from `klein4_random` to `klein4_encode_bytes`, since the registry is the one route that carried the answer; (3) the recurrence itself: F899 → §68 → F1260 is three passes on one defect, and the backlink web is the mechanism that should have caught it.

Composes **F899** (the same finding, a month earlier — this is its third occurrence; UPSTREAM §68), **F865/F612** (the byte/glyph core that does it right), **F1259** (its DERIVED category corrected here), **F1258**, **F552 / TRIALITY §5** (the re-derivation pattern), **F1211** (the previous instance of that pattern), `[[feedback_introspect_srmech_before_python_dispatch]]` (the miss, again), `[[feedback_name_the_encode_sense]]` (this IS the overloaded-"encode" problem at the HV layer), #231/PKG-3.
