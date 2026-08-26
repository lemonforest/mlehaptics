# Finding 723 — srmech 0.7.5rc50 closes R3 U1: tokenize + cooccurrence_edges meet the §40 acceptance bar 3/3

**Script:** `R-RBS-LM-U1CLOSED_rc50_meets_section40_bar.py`
**Status:** VERIFIED (srmech 0.7.5rc50, TestPyPI, numpy-free venv) — **supersedes F722** (the rc49-fails record)
**User direction:** *"check on rc50."*

## rc50 fixed all three F722 failures — and moved to the §40 Option-1 site

rc50 relocated both ops to **`srmech.amsc.text`** (the landing site §40 recommended) and addressed every acceptance
point. Re-running the same §40 bar:

| §40 bar | rc49 (F722) | rc50 (this) | evidence |
|---|:--:|:--:|---|
| **1. Unicode tokenize (F698)** | ❌ ASCII-only | ✅ **PASS** | `tokenize("café Москва naïve 日本語 hello world")` → `['café','москва','naïve','日本語','hello','world']` (accents/Cyrillic/CJK kept) |
| **2. No silent vocab cap (F708)** | ❌ default cap 1000 | ✅ **PASS** | default `vocab_size=None` → 1500 words = n=1500 (no cap); explicit `vocab_size=500` → n=500 (opt-in) |
| **3. Doc-boundary window-reset** | ❌ flat, bleeds | ✅ **PASS** | `docs=[[alpha,beta],[gamma,delta]]`, window 2 → edges `{(0,1),(2,3)}` only; no cross-boundary `(1,2)` |

New signatures:
- `tokenize(text, *, stoplist=<default incl. the F714 prepositions: around/along/toward/onto/within/among/against/
  throughout/across…>, unicode_normalize=True) -> List[str]` — Unicode-aware, configurable stoplist with a real
  default (matches §40's "not a bare boolean").
- `cooccurrence_edges(docs, *, window=2, vocab=None, vocab_size=None) -> (n, edges, weights)` — `docs` is a sequence
  of token-sequences (per-document window reset); `vocab_size=None` is no-cap by default; edges are 2-tuples
  straight into `dense_laplacian`.

## Disposition — R3 U1 is genuinely closed

- **The §40 spec did its job end-to-end:** it specified the requirements from the wiki kernel's real lessons
  (F698/F708/F714/F690), F722 caught rc49 shipping the F708-regression-as-a-default, and rc50 closed all three
  against the spec — including adopting the recommended `amsc.text` site. This is the no-leaning / MPM loop working:
  *specify → falsify the premature ship → verify the fix.*
- **#855 R3 U1 is now checkable** (the audit's `amsc.text` probe resolves FOUND; the Counter() idiom is genuinely
  retired and K1 is an authorable pure-TOML composite end-to-end). The other R3 boxes (U2/U3/U4/§17.1) remain open.
- **Next (the §17.1 ours-side migration):** the wiki kernel can now migrate off the hand-rolled F698/F700
  `content_words` + `build_edges_topk` onto `srmech.amsc.text.{tokenize, cooccurrence_edges}` — modulo our
  corpus-specific wiki-markup strip (F700), which correctly stays in our adapter (the §40 boundary: markup-strip is
  not `tokenize`'s job). A parity check (our edges vs the shipped op's edges on the same article stream) is the
  clean migration gate.

**Composes:** F722 (the rc49 fail this supersedes) · §40 (the spec, now met) · F698/F700/F714 (the Unicode/stoplist/
markup lessons that became the bar) · F708 (the no-cap requirement) · F690 (one-article-one-window-reset) · #855 R3
U1 / §17.1 (the migration this unlocks). srmech 0.7.5rc50. Held open (F394).
