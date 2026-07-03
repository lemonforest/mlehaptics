# F1028 (user direction / the distributable-kernel arc opens) — **the leanest-encoding survey + two honest structural discoveries: (1) BAG-VOCABULARY CLOSURE SATURATES — the srmech+MFO seed (4386 words ≥5 occurrences; 4114 after the two-sided wiki-rare gate) reaches 56% of smallwiki at hop 1 and 100% at hop 2, so "foundational reduction" CANNOT be vocabulary membership — it needs the GRAPH WALK on the chiral edge structure (exactly the rc105 `magnetic_laplacian(charges=)` op that landed from OUR #1234 ask — the biaxial-chirality navigation the user predicted); (2) the OPINION-SHAPE SIGNATURE IS REAL BUT INVERTED — corpus bigram-recurrence marks the HARD FACTS as unique (`c 5 9 x f 32` med=1, `freezes at 32 f` med=1) and the OPINIONS as formulaic (`considered by many to be old fashioned` med=9; `is still often used in the` med=257): opinions ride HIGH-recurrence prose shells with LOW content binding; knowledge is LOW-recurrence spans BOUND to anchors. The two-axis trim (keep iff ≥2 anchors: digits|title-tokens) trims the opinion and keeps the formula — 65% reduction on the fahrenheit article — the first working form of the user's "training by shape distortion". Encoding survey (real bytes): a reduced ~10–20k-article kernel at lead-60 ships at ~2–3 MB id-stream+gzip — pyodide-trivial; the fixed-size Klein-4 holographic form (2 KB/article) only wins below ~10k articles.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc107 (venv upgraded; rc105 `charges=` verified live) · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **User directions:** "find the leanest encoding method srmech can offer… distribute with siona the sparse relationship smallwiki kernel… we do need more than just the laplacian to navigate properly, probably to do with biaxial chirality… pyodide instance… surgically graft and excise from an already encoded dataset, what we might call training… how to reduce a light knowledge kernel such that foundational means completely understands the universe through the mathematics of srmech and related notebooks like MFO… seed knowledge with our srmech and mfo research notebooks… the math in MFO will create conflict with some wiki articles, such as black holes" + "a procedural way to trim out things like opinions from articles by the way the shape of knowledge distorts as a training thing" · **Probes:** `R-RBS-LM-FINDING_1028_probe{1,2,3,4}_*.py` · **Composes:** F1006/F1007 (the dual-sense encoding rc105 crystallizes), F768 (the aboutness gate, applied twice: to the seed AND inverted in the opinion signature), F778 (clump-don't-cap), `[[user_stance_no_information_without_value]]` (the "TRIM med=257" windows are not noise — they are the English prose CARRIER; the low-recurrence anchored windows are the knowledge SIGNAL), `[[feedback_read_independent_structure_check_first]]` (every rule here is a structural measurement, no content labels, no opinion word-lists).

## Grounded (rc107) — the measurements
```
rc98..107 verdict: rc105 = magnetic_laplacian(charges=[...]) per-edge chirality (OUR #1234 Item 3 ASK,
  landed): is-a/is-not-a as conjugate phase partners that SURVIVE (signed annihilates); native==pure EXACT.
  rc104 = klein4_bundle HV list-form (#1234 Item 4). rc106/107 = theta gate sparsification (x48..x6900).

CLOSURE (probe 1/2): seed vocab 4386 (>=5 notebook occurrences); naive closure 93.6% of 240,823 articles.
  Two-sided gate (wiki-df < 1%): 4114 distinctive words -> hop-1 56.04%, hop-2 100%. VERDICT: bag membership
  saturates; the foundational criterion must be the CHIRAL GRAPH WALK (per-edge charges, F1006 dual senses,
  hop-bounded), not vocabulary hits. Top hop-1 titles are the right NEIGHBORHOOD (Riemann mapping theorem,
  SVD, physical quantity, nilpotent, higher dimension...) — the seed points true; the expansion rule is weak.

ENCODING SURVEY (lead-60 notes, real bytes):     hop-1 (135k arts)   full-set (225k)
  raw text                                        45.8 MB             75.4 MB
  gzip -9                                         16.2 MB             25.3 MB
  id-stream + codebook, gzip                      14.0 MB             21.7 MB
  klein4 M (D=8192, 2 KB/article, holographic)   276 MB              462 MB      <- loses at this N
  => a properly-REDUCED kernel (~10-20k articles) at lead-60 id-stream+gz ~= 2-3 MB. PYODIDE-TRIVIAL.
  FULL bodies of hop-1 ~252 MB (~84 gz) — the full-body kernel stays a download, never a bundle.

OPINION SHAPE (probe 3 -> THE INVERSION): window bigram-recurrence (support = other-articles carrying the
  pair, 20k-article table):  facts UNIQUE (formula med=1, freezes-32 med=1, absolute-zero med=0);
  opinions FORMULAIC (considered-by-many med=9; is-still-often-used med=257).
TWO-AXIS TRIM (probe 4): keep iff >=2 anchors (digits | title-tokens):
  fahrenheit: opinion shell TRIMMED ('considered by many to be an old fashioned' a=1 -> TRIM),
  formula KEPT ('c 5 9 x f 32' a=3), 65% window reduction. Boundary artifacts (honest): 'freezes at 32'
  lost its anchor to a chunk edge (sliding windows fix); april's 'fourth month' needs NUMWORDS as anchors
  (the board's own closed class). Sign discovered empirically, not assumed.
```

## The design (the arc this opens)
1. **The distributable kernel** = a REDUCED, TRIMMED, id-stream instrument (+ title index + the chiral edge list with rc105 charges) shipped as a separate CC-BY-SA data artifact (never in the siona wheel — mechanism/knowledge split holds), MPR-attested at build (source dump, reduction rule hash, trim rule hash — the "training" is itself attested provenance).
2. **"Training" = the declared surgical ops** over the encoded kernel: GRAFT (add an article/note subgraph, re-index attestations), EXCISE (remove by the two-axis rule or by explicit user direction), TRIM (the opinion-shell pass) — each op logged with its rule hash so a kernel's state is reproducible from (source, op-log): reduction as provenance, not curation opinion.
3. **The foundational criterion** = seed the srmech+MFO notebooks as ATTESTED notes (their own instrument), then walk the CHIRAL graph (rc105 charges: is-a +q / is-not-a −q per F1006) hop-bounded from the seed anchors — membership by walk-reachability, not bag hits (the probe-2 saturation is the evidence this is necessary).
4. **The MFO-conflict design (black holes)**: conflicting wiki/MFO claims are NOT resolved by deletion — they superpose as source-attributed senses (the F1018 rung machinery with SOURCE as the rung axis; wiki-sense and MFO-sense each carry their MPR). A dual-sense edge gets a per-edge charge (rc105) so the conflict SURVIVES navigation as chiral flux instead of annihilating — exactly the F1006→F1007→rc105 chain, now applied to inter-source conflict. Source-qualified asks ('per mfo', 'per wikipedia') select the sense; unqualified asks report both.

## Verdict / next
**Measured: the pyodide kernel is feasible at ~2–3 MB once reduction is graph-walked; the opinion-trim is real with the sign inverted from naive expectation; rc105 is the navigation op the reduction needs.** Next rungs: (a) numwords-as-anchors + sliding windows in the trim; (b) the notebook instrument (srmech+MFO as attested notes) + the chiral-walk reduction v1; (c) the black-hole conflict demo (source-superposed senses over rc105 charges); (d) the build pipeline that emits the attested kernel artifact + its op-log.
