# Language-agnostic glyph-stream tokenizer — design note

**Status:** design only. No production code changed in this branch.
**Branch:** `srmech-rc287-glyph-tokenizer` (from `origin/main` @ `95ccc2f5f`, v0.9.0rc282).
**Date:** 2026-07-19.
**Generating code:** `glyph_stream_tokenizer_{fetch_corpus,q1_tables,eval,conservation,derived_units}_script.py`, this directory.
**Ledger:** `glyph_stream_tokenizer_design.ndjson`.

User direction: *"what do we need to change to make tokenizer language agnostic,
using the same glyph/byte representation as siona has been working to bring?"* —
and, on the breaking consequence, **"breaking means fixing."** So this note
designs the correct representation and states the migration cost. It does not
design a compatibility shim.

---

## §0 Summary — what this spike settled

| Question | Answer | Evidence |
|---|---|---|
| **Q1** vendor UAX #29 tables, or derive from `unicodedata`? | **Vendor.** Deriving is not merely lossy — it is *impossible* for two of the three required properties. | §3 |
| **Q1 cost** | **9,459 bytes** (1,051 ranges) of static table in `c/src`. ADR-0005 permits it; precedent is the SHA-256 FIPS constants header. | §3.4 |
| **Q2** emit a glyph stream with no word decision? | **Yes** — but *not* because derived units replace words. Because the glyph cluster is the only unit that is well-defined across all scripts. | §4 |
| **Q2** can units be *derived*? | **Not reliably.** Branching entropy beats random 2.2–2.7× but F1 ≈ 0.55, precision < 0.52. Real signal, not a segmenter. **Stays open.** | §4.3 |
| **Q2 scale** | **Tractable, and smaller than today.** Vocabulary *shrinks* ~5×; co-occurrence edges *shrink* ~40%. Stream is 6.7× longer. | §4.2 |
| Storage layer already path-shaped? | **No — the brief's premise is false.** Storage is bag-shaped *by pinned contract*. | §6 |
| Six language assumptions | 4 confirmed, **2 corrected** (okina, Greek). | §2 |

Two things in the brief were wrong and are corrected here: assumption 3 (§2.3)
and the storage-layer claim (§6). Both corrections change what the work is.

---

## §1 The anchor — one path, read across 80 substrates

The notebook already contains the reading this design implements
(`srmech_research_notebook.md` §8.1 / **F704**):

> **Vanuatu sand drawing (sandroing)** — geometric designs traced with *one
> finger as a single continuous meandering line on an imagined grid*, used as a
> *means of communication among some 80 different language groups*… Structurally
> this is a Class-L **walk made physical** — a single continuous traversal of a
> lattice that *encodes and communicates* knowledge — and simultaneously a
> **cross-language translation layer**: one path, read across 80 substrates.

Attested: UNESCO Representative List of the Intangible Cultural Heritage of
Humanity, inscribed 2008 (proclaimed 2003), ref. **00073**, tier B (UNESCO
primary record). §8.1 also states the operative principle: *thinking is a PATH,
not a TRACE*.

The design consequence is narrow and literal. Sandroing is language-agnostic
because **the primitive is the stroke, and the stroke is the same stroke in all
80 languages**. It does not first decide what a *word* is in each of the 80.
A tokenizer that must know what a word is in each language is not the same kind
of object. The glyph is our stroke.

This is an anchor, not a proof. It tells us which primitive to reach for; §3–§5
are what decide whether it works.

---

## §2 The six language assumptions — confirmed or corrected

Measured against the tokenizer at
`python/srmech/amsc/text.py` (verified loaded from this worktree; the pure
path — `HAS_NATIVE=False` — which is the parity oracle for the compiled
projection). Generating code: `glyph_stream_tokenizer_eval_script.py` §A2.

### 2.1 Assumption 1 — L/M runs are words → **CONFIRMED, and worse than stated**

| input | current `tokenize` |
|---|---|
| `语言是人类交流的工具` | `['语言是人类交流的工具']` — 1 token |
| `ภาษาไทยเป็นภาษาราชการ` | `['ภาษาไทยเป็นภาษาราชการ']` — 1 token |

The severity is not the long token; it is what the long token does to the
vocabulary. Measured over real Wikipedia prose (§A):

| language | tokens | **types** | types/tokens | longest token |
|---|---|---|---|---|
| Chinese | 1,838 | **1,643** | **89.4%** | 45 |
| Japanese | 768 | **680** | **88.5%** | 69 |
| Thai | 183 | 162 | 88.5% | **96** |
| English | 12,815 | 2,513 | 19.6% | 29 |

In scriptio-continua scripts **~89% of "words" occur exactly once**. A
co-occurrence graph over a vocabulary that is 89% singletons carries almost no
association mass. The tokenizer is not merely mis-segmenting these languages —
it is *manufacturing* a degenerate vocabulary. See §5.2 for why this matters to
F1253.

### 2.2 Assumption 2 — universal `casefold()` → **CONFIRMED for Turkish; CORRECTED for Greek**

Turkish confirmed, and it is a vocabulary split, not a cosmetic issue:

| upper | → | lower | → | match? |
|---|---|---|---|---|
| `IŞIK` | `['işik']` | `ışık` | `['ışık']` | **✗** |
| `İSTANBUL` | `['i̇stanbul']` | `istanbul` | `['istanbul']` | **✗** |
| `DİYARBAKIR` | `['di̇yarbakir']` | `diyarbakır` | `['diyarbakır']` | **✗** |

`'İ'.casefold()` returns **two codepoints** (`i` + U+0307 COMBINING DOT ABOVE).
`'I'.casefold()` returns `i`, colliding with Turkish dotless `ı`'s distinct
identity. The same word in two cases yields two types.

**Correction to the brief — Greek final sigma is not the failure.** `casefold`
*correctly* unifies ς→σ (`'ς'.casefold() == 'σ'.casefold()` → `True`), which is
the desirable behaviour. The real Greek break is **uppercase accent loss**,
which no casefold policy can repair:

| upper | → | lower | → | match? |
|---|---|---|---|---|
| `ΓΛΩΣΣΑ` | `['γλωσσα']` | `γλώσσα` | `['γλώσσα']` | **✗** |

### 2.3 Assumption 3 — apostrophes vs ʻokina → **INCORRECT AS STATED**

The brief says ʻokina (U+02BB) is a letter and implies the tokenizer mishandles
it. **It does not.** U+02BB is category `Lm` (MODIFIER LETTER TURNED COMMA), so
the L/M rule keeps it. `tokenize('Hawaiʻi')` → `['hawaiʻi']` — correct.

The real Hawaiian failure is a **homoglyph** problem, and it is a genuine bug:

| input | codepoint | current `tokenize` |
|---|---|---|
| `ʻokina` | U+02BB (`Lm`) | `['ʻokina']` ✓ |
| `’okina` | U+2019 (`Pf`) | **`['okina']`** — okina **deleted** |
| `Hawaiʻi` | U+02BB | `['hawaiʻi']` |
| `Hawai’i` | U+2019 | `["hawai'i"]` — **a different type** |

`_APOS = "'’"` contains U+2019, which is mapped to ASCII `'` and then removed by
`_emit`'s `strip("'")` word-initially. U+2019 is extremely common as an okina
substitute in real-world text. So Hawaiian breaks — but for a reason the brief
did not name, and the fix is different (normalize confusables, or stop treating
U+2019 as punctuation) than the fix for a category error.

### 2.4 Assumption 4 — `_MIN_LEN = 2` → **CONFIRMED**

`tokenize('中 国')` → `[]`. Both single-codepoint CJK content words vanish.
`'a cat'` → `['cat']`; `'I am'` → `['am']`.

### 2.5 Assumption 5 — 146 English function words applied to all languages → **CONFIRMED**

`DEFAULT_STOPLIST` is 146 English words and is the default for every language.
In non-English text it is mostly inert but not harmless: it silently removes any
token that happens to collide with an English function word (Turkish `o`, `bu`;
Dutch `over`; etc.).

There is also a **documented self-contradiction**, confirmed. The `stoplist`
docstring promises raw mode *"keep all content words"*; `_emit` applies
`len(word) >= _MIN_LEN` unconditionally. The parameter cannot deliver what it
documents.

### 2.6 Assumption 6 — the content/function split → **CONFIRMED, and it is backwards**

F1257 found the operator layer IS the conserved core (94/94 tokens entering the
core were stoplist members). The default configuration therefore **discards
precisely the layer the science found to be load-bearing**. `tokenize('the cat
sat on a mat')` → `['cat','sat','mat']` under the default stoplist: every
operator gone.

### 2.7 Bonus failure not in the brief — the orphaned-mark token

```
'1️⃣'  =  U+0031 (Nd) + U+FE0F (Mn) + U+20E3 (Me)
tokenize → ['️⃣']
```

The digit is dropped (not `L`/`M`); the two combining marks survive *as a token
with no base character*. The L/M rule can emit a "word" made entirely of marks.
All other emoji vanish entirely: family-ZWJ, flag, and skin-tone sequences all
return `[]`.

---

## §3 Q1 — the table question

### 3.1 What `unicodedata` actually exposes (verified, not assumed)

Python 3.14.3, `unicodedata.unidata_version` = **16.0.0**:

```
bidirectional, category, combining, decimal, decomposition, digit,
east_asian_width, is_normalized, lookup, mirrored, name, normalize,
numeric, ucd_3_2_0, unidata_version
```

**There is no grapheme-break property, and no Extended_Pictographic, and no
InCB.** The brief's premise holds.

### 3.2 UAX #29 needs *three* data sources, not one

Implementing GB1–GB999 correctly and scoring against the official
`GraphemeBreakTest.txt` (**1,093 cases**) established the true dependency:

| source | property | why |
|---|---|---|
| `auxiliary/GraphemeBreakProperty.txt` | GBP (13 values) | GB3–GB13 |
| `emoji/emoji-data.txt` | `Extended_Pictographic` | **GB11** (emoji ZWJ sequences) |
| `DerivedCoreProperties.txt` | `InCB` (Linker/Consonant/Extend) | **GB9c** (Indic conjuncts, added Unicode 15.1) |

With all three: **1,093/1,093 pass (100.00%)**. Omitting InCB alone drops it to
1,086/1,093 — that is how the third dependency was found. This is worth stating
plainly because GB9c is recent and easy to miss.

### 3.3 How wrong is a `unicodedata`-only derivation? — measured

The derivation is a genuine best effort, not a straw man: CR/LF/ZWJ as
constants; Regional_Indicator by block arithmetic; **Hangul LV/LVT by the UAX
#29 §3 syllable algebra** (`(cp−SBase) % TCount`) and jamo L/V/T via
`unicodedata.name()` prefixes; Control from `Cc/Cf/Zl/Zp`; Extend from `Mn/Me`;
SpacingMark from `Mc`.

**Conformance suite (adversarial by design):**

| tables | pass | rate |
|---|---|---|
| TRUE (vendored UCD) | 1093/1093 | **100.00%** |
| DERIVED (`unicodedata` only) | 954/1093 | **87.28%** |

Failures by cause: 58 Extend/SpacingMark/Control edges · 56 **Prepend** · 13
**InCB/GB9c** · 12 **Extended_Pictographic/GB11**.

**Real prose (the decision-relevant number).** Boundary-set symmetric difference
over 345,983 glyphs of Wikipedia text:

| language | glyphs | mismatched boundaries | error |
|---|---|---|---|
| Arabic, Bislama, Greek, English, Hawaiian, Hebrew, Japanese, Khmer, Korean, Russian, Tamil, Turkish, Chinese | — | **0** | **0.0000%** |
| Lao | 707 | 5 | 0.7072% |
| Thai | 3,603 | 30 | 0.8326% |
| **Devanagari** | 11,580 | 922 | **7.9620%** |
| **Bengali** | 11,100 | 1,025 | **9.2342%** |
| **Burmese** | 3,221 | 617 | **19.1555%** |
| **TOTAL** | 345,983 | 2,599 | **0.7512%** |

The aggregate 0.75% is misleading and must not be quoted alone. The error is
**exactly zero** for Latin, Greek, Cyrillic, Arabic, Hebrew, CJK, Korean and
Hawaiian, and **concentrated in Brahmic scripts** — the scripts that most need
correct grapheme clustering, because that is where a "character" is most
strongly not a codepoint. A derivation that is perfect on the scripts that
barely need it and ~19% wrong on Burmese is not an approximation we can ship as
language-agnostic. Shipping it would rebuild the English-privilege problem in a
new place.

### 3.4 Decision — VENDOR, and what it costs

**The drift argument that motivated "never vendored" does not apply here.**
`srmech_text.c:25–32` and `text.py:110` justify caller-provided tables as making
native==pure byte-identical *by construction*, with "no vendored Unicode data to
drift against the host's". That reasoning depends on the table being derivable
from the running interpreter. **Extended_Pictographic and InCB are not derivable
from `unicodedata` at any fidelity** — there is no source to build them from.
So the choice is not "vendored vs interpreter-derived"; it is **"vendored vs
absent"**. Absent means no GB11 and no GB9c, i.e. broken emoji and broken Indic.

**ADR-0005 permits it.** The ADR's scope is *imports and links*
("srmech source **imports** NO external mathematics library"; "The C side
likewise **links** no external math/bignum library"), enforced by an AST
import-walk that cannot see a static array. Its stated purpose is that a bare-C
host runs the same math with no third-party library — which vendoring serves.
Precedent is direct and strong: `c/src/srmech_sha256_constants.h` vendors the
FIPS-180-4 round constants *with an MPR v1 attestation block in the comment*
("the MPM discipline applied to a CODE CONSTANT rather than a catalog datum"),
and srmech already vendors full JSON and TOML parsers after explicitly
superseding its own anti-vendoring stance.

**Cost, measured:**

| item | ranges | bytes packed `(lo:u32, hi:u32, tag:u8)` |
|---|---|---|
| GBP, Hangul removed (done by arithmetic) | 570 | 5,130 |
| Extended_Pictographic | 78 | 702 |
| InCB | 403 | 3,627 |
| **total** | **1,051** | **9,459 B (9.2 KiB)** |

Storing Hangul as data instead of arithmetic would cost 16,713 B — the
LV/LVT alternation is 798 ranges of pure arithmetic. Deriving it is worth 7.3 KiB.

**What vendoring genuinely costs, stated honestly:**

1. **A version-drift surface that did not exist before.** The vendored table is
   pinned to UCD 16.0.0; the host interpreter's `unicodedata` may be another
   version. Mitigation follows the SHA-256 precedent: a committed test that
   re-derives the vendored table's *derivable* subset from the running
   `unicodedata` and fails on divergence, plus an explicit recorded
   `UCD_VERSION`. The non-derivable subset (ExtPict, InCB) cannot be checked
   this way — that residue is unguarded and must be named as such.
2. **A recurring maintenance obligation.** Unicode ships annually; GB9c arrived
   as recently as 15.1. Someone must re-vendor. This is a real, ongoing cost.
3. **The MPR attestation is mandatory**, per the SHA-256 template. Recorded in
   the ledger: `GraphemeBreakProperty.txt` sha256
   `c29360bd…89dc1`, `emoji-data.txt` `f1365a51…696a`,
   `DerivedCoreProperties.txt` `39d35161…dabd`,
   `GraphemeBreakTest.txt` `ee2b9354…3cb5`.

**ADR-0003 is satisfied either way**, and this is the point the brief correctly
identified as making the design tractable: `srmech_text.c:32` — *"A bare-C host
supplies its own tables (they are inputs, like the stoplist)."* The table stays
a **caller-provided input**; srmech ships a *default* table as static data that
both projections load. A bare-C host may use the shipped default or supply its
own. The C host must *run* the segmentation, not *derive* Unicode.

---

## §4 Q2 — do we segment at all?

### 4.1 The proposal

Emit the **glyph stream**: NFC-normalize, then split into UAX #29 extended
grapheme clusters. No word decision, no casefold, no stoplist, no length floor.

This deletes assumptions 1, 3, 4, 5 and 6 simultaneously, because each of them
is a *property of the word decision*. It answers R-RBS-LM-25 §3.5's blocker
directly: a grapheme cluster never splits a codepoint or a combining sequence,
so a partial multi-byte sequence cannot arise and U+FFFD cannot be rendered.
Assumption 2 (casefold) is deleted by *not casefolding* — case becomes a
downstream, per-locale concern rather than a front-door one.

Worked behaviour:

| input | current | glyph stream |
|---|---|---|
| `语言是人类交流的工具` | `['语言是人类交流的工具']` | `['语','言','是','人','类','交','流','的','工','具']` |
| `IŞIK` / `ışık` | `['işik']` / `['ışık']` (≠) | `['I','Ş','I','K']` / `['ı','ş','ı','k']` |
| `’okina` | `['okina']` (lost) | `['’','o','k','i','n','a']` |
| `中 国` | `[]` | `['中',' ','国']` |
| `👨‍👩‍👧‍👦` | `[]` | `['👨‍👩‍👧‍👦']` — **one cluster** |
| `🇻🇺` | `[]` | `['🇻🇺']` — **one cluster** |
| `1️⃣` | `['️⃣']` (orphan) | `['1️⃣']` — **one cluster** |
| `क्षि` | `['क्षि']` | `['क्षि']` — one cluster (GB9c) |
| `한국어` | `['한국어']` | `['한','국','어']` |

The emoji rows are where codepoint-level and glyph-level answers differ
maximally, and they are the clearest demonstration that the cluster is the right
primitive: a 7-codepoint family sequence is **one** thing a human sees and
**one** cluster.

### 4.2 Scale — measured, and it goes the *helpful* direction

365,194 chars across 18 languages, `cooccurrence_edges(window=5)`:

| granularity | tokens | **types** | tokens/type | segment (s) | **edges** | density |
|---|---|---|---|---|---|---|
| WORD | 51,787 | **20,775** | 2.5 | 0.269 | **199,553** | 0.00092 |
| GLYPH | 346,000 | **4,294** | 80.6 | 0.917 | **118,869** | 0.01290 |

Ratios (glyph/word): types **0.207×**, tokens **6.68×**, edges **0.596×**,
segmentation time **3.41×**.

**The naive worry — that glyph granularity explodes the store — is false.** The
stream is 6.7× longer, but the *vocabulary shrinks ~5×* and the *edge count
shrinks ~40%*, because the graph is bounded by vocabulary, not stream length.
Density rises 14×, which is the point: association mass concentrates instead of
scattering across singletons.

**Projection to the measured field store** (1,100,189 types / 18,376,459 turns /
323.7 MB / 11.1 min `plasmid_extract`):

| metric | word (measured) | glyph (projected) |
|---|---|---|
| types | 1,100,189 | **~227,000** |
| turns | 18,376,459 | **~123,000,000** |
| size | 323.7 MB | **~193 MB** |
| rebuild | 11.1 min | **~74 min** |

**Bounding caveat, stated because it matters.** The 0.207× type ratio comes from
an 18-language balanced corpus. simplewiki is ~monolingual English, where the
glyph alphabet is *far* smaller — English alone measured **119 glyph types vs
2,513 word types (0.047×)**. So for the actual field store the type collapse is
likely *more* extreme than 0.207×, not less; ~227,000 is a conservative upper
bound. The turn-count growth (6.68×) is the number to trust least in the other
direction: English glyphs/word ≈ 6.66 here, close to the multilingual figure, so
~123M turns is a reasonable estimate. **Verdict: tractable.** A ~74-minute
rebuild is ~6.7× the 11.1-minute one — the same order, not a different regime.

### 4.3 Can the units be DERIVED? — tested, and the answer is "not reliably"

rc272 partitions "by the DATA'S OWN STRUCTURE"; F1254 derived `k` rather than
choosing it. The corresponding move here is to let the units emerge. The
classical derivation is Harris's hypothesis: a boundary sits at a local maximum
of successor (branching) entropy.

This is testable with ground truth — in space-separated scripts, the spaces
*are* the boundaries. Hide them, run branching entropy over the glyph stream,
score recovered boundaries against true ones, and compare to a
frequency-matched random baseline. **This test can come back FALSE.**

Context order n=4:

| language | glyphs | true b. | pred b. | precision | recall | F1 | random F1 | lift |
|---|---|---|---|---|---|---|---|---|
| English | 72,019 | 13,227 | 20,602 | 0.466 | 0.726 | **0.568** | 0.222 | **2.55×** |
| Turkish | 69,586 | 10,230 | 19,265 | 0.390 | 0.734 | 0.509 | 0.191 | 2.66× |
| Greek | 14,500 | 2,523 | 3,321 | 0.444 | 0.585 | 0.505 | 0.202 | 2.50× |
| Russian | 19,902 | 2,951 | 4,437 | 0.301 | 0.452 | 0.361 | 0.180 | 2.01× |
| Hawaiian | 4,405 | 1,071 | 1,002 | 0.518 | 0.485 | 0.501 | 0.231 | 2.17× |

**Verdict: real signal, not a segmenter.** 2.0–2.7× over the null is decisively
above chance — the structure genuinely is in the data. But precision < 0.52 means
more than half of proposed boundaries are wrong, and F1 ≈ 0.55 is far from
usable. Derived units do **not** replace word segmentation at this corpus scale
with this method.

**This does not weaken the glyph-stream design; it separates two claims that
should never have been bundled.** The glyph stream is correct because the
cluster is well-defined in every script — that stands on §3 and §4.2 alone. Unit
derivation is a *downstream research question* on top of it, and it stays open
(fermata F-A, §8). The design must not ship implying units are solved.

---

## §5 Capabilities — stated implementation-neutrally (ADR-0009)

Per ADR-0009 the capability is the invariant and each implementation is a
coherency projection; neither is primary. Vocabulary per ADR-0009 §3 — no
"C peer", no "pure fallback", no "accelerates".

| # | Capability (the invariant) | scripting-coherency projection | compiled-coherency projection |
|---|---|---|---|
| C1 | **Segment text into UAX #29 extended grapheme clusters** over the full Unicode domain, given a break-property table | `srmech.amsc.text.glyph_stream` over the shipped default table | `srmech_text_glyph_stream`, same table as a caller-provided arena input |
| C2 | **Load a grapheme-break table from its packed range form** | reads the same packed blob the compiled projection reads | reads the packed blob; no interpreter present |
| C3 | **Derive the Hangul LV/LVT/L/V/T classification arithmetically** (no table) | UAX #29 §3 syllable algebra | identical integer algebra |
| C4 | **Emit the glyph stream as an ordered walk** (`Sequence[str]` / offset+length pairs over the source buffer) | list of cluster strings | offset/length pairs into the caller's buffer |
| C5 | **Verify a table against the official conformance suite** | runs `GraphemeBreakTest.txt` | runs the same fixture, byte-identical verdict |

Notes on the contract:

- **Byte-identical is required** (ADR-0009 §1.3): both projections must return
  the same cluster boundaries for every input, verified by a committed
  differential test whose oracle role rotates.
- C1's table is an **input** (ADR-0003, `srmech_text.c:32`), so a bare-C host is
  fully served: it may load srmech's shipped default blob or supply its own.
- **No decline is designed in.** Every codepoint sequence has a defined cluster
  segmentation, so neither projection has a domain it cannot serve. If an
  implementation ever declines, ADR-0009 §5 requires a tracked ledger gap, not a
  changelog note.
- ABI: this is **additive** (new symbols, no callback typedef), so it does not
  bump `SRMECH_ABI_VERSION`.

---

## §6 The storage-layer claim — the brief's premise is FALSE

The brief asks this to be checked and corrected if wrong. It is wrong, on both
halves. Evidence gathered by direct code read.

**Half 1 — "coupled turns along a strand are already a walk."** They are not.
A turn is coupled to a *shared global invariant*, not to its neighbour:

```python
# python/srmech/amsc/genome.py:770
def quad_turn(turn, coupling):
    return _klein4_bind(turn, coupling)
```

Its docstring (genome.py:758) says so: *"`coupling` is the shared invariant
present in every turn's coupling"*. `chromosome()` applies it as a pure
per-element map (genome.py:2475) and `recall()` inverts it per-element,
independently (genome.py:2627). Across all eleven `quad_turn` callsites, **not
one binds a turn to another turn**. The topology is a **hub/star**, not a chain.
Falsification: delete turn *i* and turn *i+1* still decodes, because decoding
consults only `coupling` — impossible in a genuine walk.

**Half 2 — "the tokenizer is the only layer imposing bag-of-words."** It is not;
the tokenizer is the layer that best *preserves* order. `tokenize()` returns an
ordered `List[str]`. Order is destroyed downstream, at one line —
`plasmid.py:235` calling `cooccurrence_topk`, which symmetrizes
(`text.py:857–860`) and canonicalizes each pair to `u < v` (`text.py:880`).

Worse for the premise: order-independence is a **pinned contract**, not an
accident. `plasmid.py:848–851`:

> *"Equivalence contract (pinned by the rc279 test): … emits them in canonical
> sorted order, so it is **independent of the order in which sections were
> accumulated**."*

**Consequence for this design.** A path-shaped tokenizer would feed order into a
layer that discards it at `plasmid.py:235` and then *guarantees* it does not
matter. The glyph stream is still right for §3/§4 reasons, but it will **not**
make the two layers consistent, and this note must not claim it does. Making
them consistent is separate, larger work at the co-occurrence layer: a
directed/positional mode reaching `cooccurrence_topk` (which today has no
`directed` parameter at all — `cooccurrence_edges` has one, defaulting `False`,
with **no caller in `srmech/` passing `True`**), plus an explicit fiber store.
`laplacian.py:3855` already names that requirement: *"the fiber must be stored
explicitly"*, and `order_fingerprint` is documented as *"A VERIFIER (lossy by
pigeonhole), NEVER a store."* Eulerian machinery exists on main (`laplacian.py:3550`)
but has zero references from `plasmid.py`, `genome.py`, or `text.py`.

Logged as fermata **F-B** (§8) — a conductor decision, not mine.

### 6.1 What this means for F1253 — measured, and F1253 SURVIVES

Given §2.1 (the front door manufactures 89% singletons in scriptio continua), it
was worth asking whether F1253's "no natural antimode" was a property of
language or an artefact of the front door. Tested; it can come back either way.

Singleton share and successive-ratio spread (a knee would show as spread > 3):

| corpus | granularity | singleton | ratio spread | verdict |
|---|---|---|---|---|
| simplewiki (F1253 reference) | word | 64.6% | 1.78 | smooth |
| English | word | 54.2% | 1.44 | smooth |
| English | **glyph** | **23.5%** | 1.23 | **smooth** |
| all 18 languages | word | 69.9% | 1.50 | smooth |
| all 18 languages | **glyph** | **25.6%** | 1.24 | **smooth** |
| scriptio continua | word | **92.8%** | 2.65 | smooth |
| scriptio continua | **glyph** | **28.9%** | 1.55 | **smooth** |

**F1253 stands untouched.** Glyph granularity does not produce a characteristic
scale; every curve remains smooth/scale-free, so `conserved_core`'s decline to
derive a `k` is a real property of the distribution, not a tokenizer artefact.
This is a null result and it is the honest one.

What *does* change is the singleton mass: 64.6%→~24%, and 92.8%→28.9% in
scriptio continua. That is a large improvement in available association mass
without being a change in the *shape* of the distribution. Both facts are true
and neither should be quoted without the other.

---

## §7 Falsifiers

Each must be able to come back FALSE, and none closes by construction. (The
project's `Lk − Tw − Wr = 0` precedent — vacuous because it is a theorem — is
the standard being avoided.)

| # | Falsifier | FALSE if | Status |
|---|---|---|---|
| **F1** | The vendored table reproduces UAX #29 exactly | any of the 1,093 official `GraphemeBreakTest.txt` cases fails | **passes now** (1093/1093); would have failed before GB9c was added |
| **F2** | A `unicodedata`-only derivation is not an acceptable substitute | derived-vs-true real-prose error is < 0.5% in **every** script tested | **holds** — Burmese 19.16%, Bengali 9.23%, Devanagari 7.96% |
| **F3** | Glyph granularity is tractable at corpus scale | projected types, edges, or rebuild time exceed the word-granularity figures by > 2× | **holds** — types 0.21×, edges 0.60×, rebuild 6.7× *(NB: rebuild fails a 2× bar; the claim that survives is "same order", not "not larger")* |
| **F4** | Units can be derived from the glyph stream | boundary F1 ≤ 1.2× the random baseline | **survives as signal, FAILS as a segmenter** — lift 2.0–2.7×, but F1 ≈ 0.55, precision < 0.52 |
| **F5** | Glyph granularity does not manufacture a derivable `k` | any glyph-granularity conservation curve shows ratio spread > 3 (a knee) | **holds** — all spreads 1.23–1.55 |
| **F6** | Both coherency projections agree byte-identically | any input yields different cluster boundaries between projections | **untested — no implementation exists yet.** This is the gate for the implementing rc |
| **F7** | The glyph stream never emits a partial codepoint or split combining sequence (R-RBS-LM-25 §3.5) | any cluster boundary falls inside a codepoint or between a base and its Extend | **holds by UAX #29 construction + F1** — weak as a falsifier; retained only because §3.5 named it |

F3 is recorded as *partially failing its own stated bar* rather than being
restated to pass. F4 is recorded as failing the useful half.

---

## §8 Migration cost, and what breaks

**Everything stored breaks.** This is a front-door representation change, so
every stored corpus is invalid.

| what | breaks? | detail |
|---|---|---|
| stored vocabularies / type ids | **yes, totally** | ids are word strings; they become cluster strings |
| co-occurrence edge stores | **yes** | vertex identity changes |
| plasmid / genome stores built from text | **yes** | built on those ids |
| the 323.7 MB / 1,100,189-type field store | **yes** | full re-encode |
| `GENOME_FORMAT_VERSION` | **no** | container unchanged; contents differ |
| C ABI | **no** | additive symbols only |
| non-text genome paths | **no** | unaffected |

**Cost of the re-encode: ~74 minutes** (§4.2), against the 11.1 minutes the field
paid for the last full rebuild — 6.7×, dominated by the 6.7× longer stream.
Yes, this forces another full rebuild.

**House policy supports doing it.** There is no ADR on breaking changes; the
doctrine is recorded in practice — CHANGELOG rc142: *"This is a breaking on-disk
change … **pre-1.0, no shipped on-disk-genome consumers**"*; and the cited
precedents rc260 (**BREAKING for large kernels**), rc271 (**BREAKING at the value
level**), and the carrier consolidation's hard removals (user: *"hard removals,
breaking is fine"*). The house pattern for softening, when used at all, is an
**opt-in presentation/alias layer that never touches storage, format or ABI**
(rc271 Part B) — never a deprecation window. Per user direction here
(*"breaking means fixing"*), no shim is designed.

### Fermatas — conductor decisions, not mine

- **F-A — do we pursue derived units at all?** §4.3 shows real signal (2.0–2.7×)
  but unusable precision. Options: ship the glyph stream and leave units to
  downstream; or fund a larger-corpus/higher-order study. Not a tokenizer
  decision.
- **F-B — the order-preservation question is bigger than the tokenizer.** §6
  shows storage is bag-shaped by pinned contract. Making the layers consistent
  needs `cooccurrence_topk` to gain a directed/positional mode *and* an explicit
  fiber store (`laplacian.py:3855`). That is an architecture decision touching
  the rc279 pinned equivalence contract.
- **F-C — whitespace and punctuation policy.** The glyph stream currently emits
  spaces and punctuation as clusters (they are clusters). Whether they enter the
  co-occurrence graph, or are filtered as a separate declared step, is a
  modelling decision I did not settle. It materially affects edge counts in §4.2.
- **F-D — the co-occurrence window is now in the wrong units.** `window=5`
  spanned ~5 words; it now spans ~5 glyphs (< 1 word). Window semantics need
  re-deriving, not rescaling by 6.68.
- **F-E — case and confusable normalization move downstream.** Dropping
  front-door `casefold` fixes Turkish/Greek but means `Cat`/`cat` are distinct
  types. Where case folding and confusable mapping (U+2019 vs U+02BB, §2.3)
  belong is undecided.

---

## §9 Unknowns — what I could not determine

Named rather than filled with plausible prose.

1. **Whether ~123M turns is actually within the store's operating envelope.** I
   projected counts, not memory-resident behaviour. ADR-0006 §2.6 warns that a
   working-RAM explosion signals a missed fiber; I did not test the store at
   this turn count.
2. **The English-only type ratio's effect on the field-store projection.**
   English alone gives 0.047× vs the multilingual 0.207×. I bounded it
   conservatively but did not measure simplewiki itself.
3. **Whether the compiled projection can implement GB9c/GB11 within JPL Rule 4
   (≤60-line functions).** Both rules need lookbehind over `Extend*`. Plausibly
   fine with helper decomposition; not verified. F6 is the gate.
4. **Real-world UCD version skew.** I measured on one interpreter whose
   `unidata_version` (16.0.0) happened to match the vendored UCD exactly. I did
   **not** measure divergence against a host at a different Unicode version,
   which is precisely the risk vendoring introduces (§3.4).
5. **Native-path behaviour.** All measurements ran with `HAS_NATIVE=False`. The
   existing implementations are documented byte-identical, but I did not rebuild
   `libsrmech.so` and re-verify. Current numbers describe the scripting
   projection only.
6. **Corpus representativeness.** One Wikipedia article per language, 365,194
   chars total; Bislama is only 450 chars, Khmer/Lao under 2,600. The Vanuatu
   tie-in is anchored on a corpus too small to carry a quantitative claim, and I
   have not claimed one.
7. **Whether branching entropy converges with scale.** F1 rose with context order
   (0.495→0.568 for English, n=2→4) and English's larger corpus scored highest,
   but two points do not establish a trend. §4.3's negative verdict is stated at
   *this* scale and method, not universally.
8. **Segmentation-time ratio stability.** 3.41× was measured in the scripting
   projection with a dict-based property lookup; a packed-range binary search or
   two-stage table would change it, likely favourably. Not optimized, not
   projected.
