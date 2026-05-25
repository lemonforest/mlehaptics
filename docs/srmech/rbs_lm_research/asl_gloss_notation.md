# R-RBS-LM-27 — ASL gloss notation spec (slash-wrapped; context-aware)

A textual ASL representation designed to be:

1. **Byte-stream-renderable** — pure ASCII (mostly) + Unicode where needed; survives the OpenAI-API wire format
2. **Downstream-render-ready** — a renderer maps `/sign-name/` tokens to actual visual representations (SignWriting glyphs, 3D-avatar animation poses, video clip references)
3. **Context-disambiguating** — polysemous English words (like "beat" → ~12 distinct ASL signs) get a disambiguator suffix
4. **Cascade-friendly** — bounded vocabulary; consistent delimiters; no nested escapes; suitable for byte-level RBS-LM encoding

Per `[[user_stance_ai_is_not_a_substrate]]`: this notation is RENDERING surface preparation, not substrate. The cascade learns byte-transitions in this notation when paired against English text; downstream tools turn the rendered output into visual ASL.

---

## §1 Token-level conventions

### §1.1 Explicit signs

```
/SIGN-NAME/
```

The sign name is upper-case hyphen-separated. Multi-word signs use hyphens internally:

- `/HELLO/` — single-word sign
- `/THANK-YOU/` — multi-word sign (one ASL sign for "thank you")
- `/I-LOVE-YOU/` — single ASL sign even though it's three English words

### §1.2 Polysemy disambiguators

When an English word maps to multiple ASL signs depending on context, append a disambiguator:

```
/word-disambig/
```

Examples for "beat":
- `/beat-egg/` — beat eggs (rapid downward-circular hand motion as if whisking)
- `/beat-defeat/` — defeat someone (fist striking palm)
- `/beat-pulse/` — heart beats (rhythmic chest tap or finger pulse on wrist)
- `/beat-rhythm/` — musical beat (steady hand-clap or tap-on-surface)
- `/beat-hit/` — to physically strike (fist motion downward)

Examples for "run":
- `/run-jog/` — physical running (alternating fist motion)
- `/run-machine/` — a machine runs / operates (rolling motion with both hands)
- `/run-flow/` — water runs (flowing finger motion)
- `/run-manage/` — run a business (two hands directing/organizing motion)
- `/run-candidate/` — run for office (forward index-finger pointing)
- `/run-late/` — run late (finger tapping wrist or hurry motion)

Examples for "light":
- `/light-bright/` — illumination (open hand fingers spreading down from above)
- `/light-weight/` — not heavy (open palms lifting easily)
- `/light-color/` — pale color (open hand near face with light motion)
- `/light-fire/` — to ignite (striking motion with thumb)

Examples for "right":
- `/right-correct/` — correct (thumb-index L-shape touching)
- `/right-direction/` — right side (pointing right with index)
- `/right-now/` — immediate (pointing down sharply)
- `/right-privilege/` — civil right (vertical right-hand chop with palm out)

### §1.3 Fingerspelling

Words without a dedicated sign get fingerspelled letter-by-letter:

```
[fs:F-O-O-D]
```

The brackets distinguish fingerspelling from sign sequences. Letters are hyphenated upper-case. Names, technical terms, proper nouns, and rare words are common fingerspelling candidates.

### §1.4 Classifier predicates

ASL classifiers describe handshape + motion for object/action descriptions:

```
cl:HANDSHAPE-{movement-description}
```

Examples:
- `cl:1-{person-walks-left}` — index finger represents a person walking left
- `cl:3-{vehicle-stops}` — 3-handshape (thumb + index + middle) represents a vehicle
- `cl:B-{flat-surface}` — flat hand represents a flat surface
- `cl:C-{cup-shape}` — C-hand represents a cylindrical object

### §1.5 Repetition / inflection

`+` marker for repetition (plurality, continuous aspect, iteration):

```
/HOUSE/+        single-word: "houses" (plural)
/RUN-JOG/++     continuous: "running and running" (iterative)
/AGAIN/+        again and again
```

### §1.6 Non-manual markers (NMM)

Facial expressions + body language as bracketed sentence-level annotations:

```
[furrowed-brow]      yes/no question or topic marker
[head-tilt]          conditional clause
[head-shake]         negation
[head-nod]           affirmation
[eyes-wide]          surprise / emphasis
[pursed-lips]        compact / small / careful
[topic]              topic marker over the marked phrase
[rh-q]               rhetorical question
[wh-q]               wh-question
```

NMM apply to the immediately-following phrase. The renderer overlays the facial expression on the avatar/SignWriting during that span.

### §1.7 Spatial reference / role shift

ASL uses 3D space for pronouns + discourse referents:

```
{loc:left}/PERSON/   establish referent at left location
ix:left              point to left referent (pronoun)
{rs:left}            role-shift to the left referent (taking their perspective)
```

### §1.8 Sentence delimiters

```
. — sentence-end (closes any open NMM scope)
| — phrase-break within a sentence
```

---

## §2 Composition examples

| English | ASL gloss |
|---|---|
| Hello! | `/HELLO/.` |
| I love you. | `/I-LOVE-YOU/.` |
| I beat the eggs. | `[fs:I] /beat-egg/ /EGG/+.` |
| I beat him in chess. | `[fs:I] /beat-defeat/ /HIM/ /CHESS/ /WIN/.` |
| My heart beats. | `/MY-HEART/ /beat-pulse/.` |
| The drum has a steady beat. | `/DRUM/ /HAVE/ /STEADY/ /beat-rhythm/.` |
| She runs fast. | `/SHE/ /run-jog/ /FAST/.` |
| The machine runs all day. | `/MACHINE/ /run-machine/ /ALL-DAY/.` |
| Water runs from the tap. | `/WATER/ /run-flow/ /FROM/ /TAP/.` |
| She runs the company. | `/SHE/ /run-manage/ /COMPANY/.` |
| Are you happy? | `[wh-q]/YOU/ /HAPPY/[/wh-q]?` |
| If it rains, I stay home. | `[head-tilt]/IF/ /RAIN/[/head-tilt] [fs:I] /STAY/ /HOME/.` |
| The cat walks across the floor. | `/CAT/ {loc:right} cl:1-{walks-left-to-right} /FLOOR/.` |
| I don't know. | `[head-shake][fs:I] /KNOW/[/head-shake].` |
| Right! That's correct. | `/right-correct/! /THAT/ /right-correct/.` |
| Turn right at the corner. | `/TURN/ /right-direction/ /AT/ /CORNER/.` |

---

## §3 Why this format is cascade-friendly

| Property | Why it matters for byte-level cascade encoding |
|---|---|
| ASCII-dominant | Each sign-token is ~6-15 bytes; encodes efficiently |
| Bounded markup | `/` `[` `]` `{` `}` `+` `cl:` `ix:` `fs:` — small fixed vocabulary of structural tokens |
| No nested escapes | Brackets don't recurse; cascade doesn't need to track depth |
| Consistent delimiters | `/` always opens/closes a sign; `[` always opens a bracket annotation |
| Disambiguator pattern | `word-disambig` lets the cascade learn that "beat " context predicts different post-`/` byte sequences |

This is the format the byte-level cascade learns to produce when paired against English in the (English, gloss) corpus.

---

## §4 What this notation does NOT do

- **Not Sutton SignWriting** — SignWriting is the canonical Unicode visual notation (R-RBS-LM-26 §3.2 reserved `response_format: "signwriting"` for that). The gloss notation here is a **text-render-ready intermediate** that downstream tools can map to SignWriting, to a 3D avatar, to video clips, or to whatever visual surface the consumer needs.
- **Not authoritative ASL linguistic notation** — published ASL linguistics uses varied conventions across research groups (ASL-LRP, Stokoe, HamNoSys, glossing in upper-case English). Our slash-wrapped form is a **practical engineering choice** that's cascade-friendly + render-ready, not an academic standard.
- **Not a translation engine** — the format is one half of the story. The cascade has to be TAUGHT this notation via a parallel English↔gloss corpus (§3.2 of the partition REPORT). Until then, the format is documentation + scaffolding.
