# Finding 117 — Arts capture RELATIONSHIPS-between-elements as dominant axis (vs THINGS for substrate corpora)

**Status:** Empirical partial support for transmission-function hypothesis
**Test:** R-RBS-LM-94 (arts-corpus eigenstructure comparison)
**Predecessors:** User's earlier question — "are all of the Arts all
about sharing internal imagery and the abstract with others as a means
of sharing knowledge?"

---

## §1 What was tested

Combined arts corpus (drawing_easy + perspective_art + music_theory)
vs substrate-content corpora (Sherlock / OpenStax / McGuffey). Compare:
- Spectral concentration (cumvar at top eigvec)
- Top-3 eigvec content

---

## §2 What emerged

### Spectral shape is NOT distinctive

| Corpus | cumvar top-1 | top-3 | top-10 |
|---|---|---|---|
| **ARTS combined** | 0.045 | 0.100 | 0.214 |
| Substrate: OpenStax | 0.045 | 0.099 | 0.232 |
| Substrate: Sherlock | 0.049 | 0.091 | 0.186 |
| Substrate: McGuffey | 0.050 | 0.093 | 0.194 |

Arts cumvar sits WITHIN substrate range. No clear concentration
distinction. The transmission-function hypothesis "arts has multi-
coupled smear vs substrate's sharp anchor" — NOT supported at
concentration level.

### Content IS structurally distinctive

**Arts eigvec[0]:**
> interval, between, step, squares, what, many, here, should

These are **relationship-measurement vocabulary** — words about
INTERVALS (music), BETWEEN (perspective distance), STEPS (drawing
progression), SQUARES (geometric subdivision).

**Substrate eigvec[0]s:**
- Sherlock: `again, went, st, put, too, having` — action verbs
- OpenStax: `per, her, his, hours, miles, he, she, would` — rate-problem context
- McGuffey: `thy, thee, o, thou, say, lord` — archaic narrative voice

Substrate corpora capture **content-in-use** (things/actions). Arts
captures **relationships-between-content** (intervals/steps/distances).

---

## §3 What this means

### Partial support for transmission-function hypothesis

The arts-as-transmission-function reading predicted arts would look
spectrally different. The CONCENTRATION test fails (arts isn't
spectrally smearier or sharper than substrate). But the CONTENT test
suggests arts encodes RELATIONSHIPS rather than THINGS.

This is consistent with arts being about externalizing internal STATE
STRUCTURE (the relationships between mental elements) rather than
externalizing content directly.

To transmit an emotional state via music, you encode INTERVALS
(relationships between pitches). To transmit a 3D scene via drawing,
you encode DISTANCES (relationships between viewing points and
elements). To transmit a procedure via dance, you encode STEPS
(relationships between body positions in time).

**Arts encode the relational structure that constitutes the internal
state** — and this surfaces as the dominant coupling axis being about
relationships (interval/between/step) rather than about things.

### Refines the user's framework reading

User's question: "are all of the Arts all about sharing internal
imagery and the abstract with others as a means of sharing knowledge?"

Empirical answer: arts DO have a distinctive coupling axis content
that captures relationships-between-elements. This is what transmission
of internal state structure would need — to share what's inside, you
share the relationships between mental elements.

But arts are NOT spectrally distinct from substrate corpora at the
concentration level. The "transmission function" lives in WHAT the
dominant axis captures (relationships) not in HOW the spectrum is
shaped.

---

## §4 What this does NOT claim

Per MFO §VII.6.20:

- Arts ARE purely transmission-functions (the corpus IS substrate-
  content at one level; the relational-axis is one of arts' multiple
  functions)
- Relationship-axis IS the universal arts signature (we tested 3
  arts corpora; broader corpora needed)
- This validates the cross-species "arts = social transmission"
  reading (it's consistent with that reading; doesn't prove it)

---

## §5 Connects to

- **Finding 96** (arts as cross-domain coupling cascades) — confirmed
  at a deeper level; arts couple to multiple substrates via their
  relationship-axis
- **Finding 115** (cross-species partition) — arts correspond to the
  social-transmission/inter-individual layer; relationship-encoding
  IS the social-transmission medium
- **Finding 116** (per-token sequence asymmetry) — arts'
  relationship-vocabulary may also show distinctive asymmetry
  patterns; untested

---

*Articulated 2026-05-27 per R-RBS-LM-94. PR #687 STAYS DRAFT.*

*Arts have a distinctive eigvec[0] CONTENT (relationships-between-
elements) without distinctive spectral SHAPE. Partial support for
transmission-function reading: arts encode relational structure, not
just substrate content.*
