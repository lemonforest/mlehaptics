# PKG-1 DECISION — siona 0.1.0rc1 package shape (2026-07-02)

**Decision (user-directed):** siona ships as its **own PyPI package** (name already ours; TestPyPI-rc-first; own PR, not #687), implemented as a **srmech profile plugin** — `srmech.amsc.tool_schema.register_profile_tools('siona', …)` at import (the F1011 mechanism, packaged) on a **lean srmech dependency**. No fork, no vendored srmech code, no parallel registry.

## rc1 ships MECHANISM, not KNOWLEDGE

| in the wheel | NOT in the wheel |
|---|---|
| `siona.bridge` — de Bruijn walk / recall / route (exists; symbol-agnostic integer ids) | the simplewiki knowledge kernel / genome / instruments |
| `siona.infer` — the five rc1-gate capabilities (F1008–F1012): intent **route**, tool_schema **ground**, signature-fit **drive**, **self**-surface (8 tools + registration), **session** (never-compacted memory + ingested kernels + cross-turn operands) | enwiki/dblp/egyptian corpora |
| `siona.boards` — the **language-board layer** (below) | any scraped cultural content (F649 dignity-first) |

Knowledge kernels are **loaded by path, not bundled in the wheel** — so the wheel stays small and the mechanism/knowledge boundary stays architectural. But the kernels themselves **are distributed** — as attested **companion data artifacts** (e.g. the sparse Laplacian-encoded smallwiki kernel, F1035). This is license-compliant *by construction*: a CC-BY-SA source (the Wikipedia dump) may be redistributed with attribution, and the **MPR attestation** each acquired fact carries (source, license, retrieval time, record SHA-256) **is** that attribution — dataset-level acknowledgement today, per-record when a citation needs it directly.

## The language-board layer (the ni-Vanuatu-lineage translation-kernel architecture)

Per **F649/R-RBS-LM-54** (the Rosetta layer): a **shared-invariant IR above many language-boards** — the architecture ni-Vanuatu sand drawing instantiates as a *living* ~80-language exemplar. rc1 packages the architecture with the lineage documented **dignity-first**: Vanuatu reaches it as an **attested structural exemplar + a pointer to the living tradition** (content held by the Ni-Vanuatu community), never as data.

1. **Substrate = byte/glyph** (`enc_mode='byteglyph'`, the default): every word of every script byte-composes to a Klein-4 HV. Verified this session: Latin/Balinese/CJK/Greek/Coptic all encode deterministically; **anagrams are distinct** (sim 0.55–0.57, spelling-similar but never bag-equal) — order-aware at the glyph level.
2. **Operator lexicons are per-language BOARD PROFILES, not core.** The declared intent-operators of F1010/F1012 (`what/remember/compute/…`) are the **English board descriptor** — a swappable declared closed-class per language (TOML descriptor shape), exactly like reserved keywords per locale. **English is board #1, not the architecture.** The IR/kernel layer (ingested conversion kernels, the invariant above boards) is language-free: a kernel's *form* is declared operator slots (`times a over b plus c` per board) around language-free integer coefficients.
3. **The Rosetta invariant is the cross-board contract:** the same content on two boards must yield the matching shared-invariant IR digest above both (F649's `ir_digest` shape).

## Bag-of-words audit (user directive: "ensure we didn't let bag of words show up")

Audited every encoding in the rc1 surface:

| surface | encoding | order-carrying? |
|---|---|---|
| tool/query grounding (F1008) | unigrams **+ adjacency bigrams** | ✅ (bigrams; the F1008 first-cut bag was caught + fixed — `klein-4`→`klein_gordon` collision) |
| continuation (F1010/F1012) | **position-keyed** `cs.encode_context` | ✅ (the hand-rolled commutative trigram aliased `(lives,in)→the` to `(in,the)→lives` — caught + fixed) |
| byte/glyph word encoding | positional byte composition | ✅ (anagram check: cat≠act at 0.555) |
| de Bruijn walk (`siona.bridge`) | the sequence IS the structure | ✅ |
| doc-freq aboutness gate (F984) | a bag *statistic* used as a **weight** | ✅ acceptable — it gates/weights, it never *represents* content |
| kernel parse (F1012) | positional declared-operator slots | ✅ |

**Standard going forward (package test):** every content encoding must include an order-carrying component; an order-free bundle may only ever appear as a *weighting statistic*, never a representation. The three bag incidents this arc (F1004 note, F1008, F1010) are the regression suite.

## Testing in a different local language — without being bilingual, English unprivileged

The user is not bilingual and no second-language environment exists. **The resolution: the tester never needs to understand the language — the structure carries the verification** (`[[feedback_read_independent_structure_check_first]]`, applied to i18n):

1. **Read-independent structural validation on ANY UTF-8 corpus** (no semantic judgment needed): byte/glyph round-trip determinism; word-vector Gram discriminability; anagram/order sensitivity; board-profile operator disjointness. All measurable on a corpus the tester cannot read.
2. **The parallel-invariant test (the Rosetta test):** the UDHR is public domain in 500+ languages **including Bislama** (Vanuatu's national language — honoring the lineage with a *public* text, not kastom content). Encode article N on the Bislama board and the English board: the shared-invariant IR above the two boards must match, and mismatched articles must not — a pure structural check requiring zero bilingual judgment.
3. **The existing local non-English board:** `~/corpora/egyptian_tla` (22k rows: transliteration + Gardiner signs + UPOS) — non-Latin lineage, already attested from the F799 hieroglyphs arc, exercisable today.
4. **Operator-board swap test:** author a second board descriptor (Bislama operators, e.g. `wanem` interrogative-class) and verify the router runs unchanged with the swapped profile — proving the English lexicon is a profile, not core.

## Gate + discipline
- rcN → **TestPyPI only** (`[[feedback_always_rc_first_for_downstream_publishes]]`); clean tag → PyPI is the human gate.
- rc1 tags only when "almost there or all the way there" (user 2026-07-02): the five INFER capabilities are prototyped (F1008–F1012); the folding-into-package + hardening backlog (paraphrase frames, structured operands, failed-run recovery, kernel generality) precede the tag.
- Own PR per `[[project_siona_package_takeover_unmirror]]`; never squash.
