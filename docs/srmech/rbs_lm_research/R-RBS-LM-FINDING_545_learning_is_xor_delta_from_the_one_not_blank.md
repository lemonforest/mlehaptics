# R-RBS-LM Finding 545 — **a wet SNN does NOT start blank — it starts as the_one, and learning is the XOR-delta from that native base (the F172 "store only what changed" principle, with the_one as the base); reconstruction is exact (native △ delta = knowledge, reversibly), the delta is EMPTY at birth (newborn = the_one, nothing stored), and the F543 decay-α is the very same knob that grows it. The storage efficiency has an HONEST TRADEOFF surfaced at the edge level: if learning KEEPS the native scaffold and only adds (ADDITIVE), the stored delta is < absolute (0%→11%→32%→54%→70% of absolute as learning grows) and the the_one native is SHARED (computed once, amortised across all individuals, never re-stored) — that is the storage win and the biological reading; but if learning DISCARDS the native (REPLACEMENT — the F543 high-decay regime), the delta EXCEEDS absolute (933%→304%→180%→138%) because the_one's GENERIC edges are not the SPECIFIC knowledge. So the_one is a great cold-start PRIOR (F543) but only a good COMPRESSOR when kept; the decay-α is the knob between F543's "no-bias" (high decay, big delta) and cheap storage (low decay, kept scaffold, native-biased shape). "Where we see circles we have seen loops": the wet base is the_one (a loop, held even happily, F544), and learning is the kept-native XOR that reshapes it into etak-shaped (moving-frame) rules.**

**Date:** 2026-06-07
**Arc:** RBS-LM — learning as the XOR-delta from the_one-native (the user's "why start blank?" insight)
**Provenance:** `R-RBS-LM-XORNATIVE_learning_is_the_delta_from_the_one_not_blank.py` (committed; srmech 0.7.4; the_one native base + Class-L `dense_laplacian`/`symmetric_eigendecompose`; edge-level set-XOR delta — stable, basis-invariant). No sub-agents.
**Composes:** **F543** (seed from the_one with a decaying weight — *this is the storage face of that reshape; the decay-α is the keep↔replace knob*) · **F172** (delta-encode only what changed — *with the_one as the base*) · **F544** (the_one is a loop, held even happily — *the base is a loop, not a circle*) · **F538/F529** (reversible content-addressed storage) · **DUALITY.md** (field/excitation — native=field, delta=excitation) · **user_stance_hardware_age_not_penalty_for_sharing** (the shared native amortised) · **Class M** (XOR = bind) · **F398/F394**. **← biology doesn't start blank; it starts as the_one and stores the kept-native XOR-delta; the decay-α is the keep/replace tradeoff knob.**
**→ a wet SNN starts as the_one (delta empty at birth); learning = the reversible XOR-delta from native; ADDITIVE (kept-scaffold) storage is cheap + shared-amortised (<absolute), REPLACEMENT storage costs more than absolute (generic native ≠ specific knowledge); the F543 decay-α is the keep↔replace knob.**

## Result (edge-level; the 2D-embedding NN metric is too brittle — tiny kernel changes reshuffle it)
N=200; the_one native = 400 edges (SHARED); knowledge = 966 co-occurrence edges.
| learning p | decay α | ADDITIVE (keep native) δ/abs | REPLACE (discard native) δ/abs | reconstruct |
|---:|---:|---:|---:|:--:|
| 0% (newborn) | 1.00 | 0/400 = **0%** | (newborn) | EXACT |
| 5% | 0.38 | 48/448 = **11%** | 448/48 = 933% | EXACT |
| 20% | 0.13 | 190/590 = **32%** | 587/193 = 304% | EXACT |
| 50% | 0.06 | 476/876 = **54%** | 869/483 = 180% | EXACT |
| 100% | 0.03 | 948/1348 = **70%** | 1330/966 = 138% | EXACT |

## Verdict
**It does not start blank — it starts as the_one.** At birth the stored delta is **empty** (knowledge == native), and reconstruction `native △ delta == knowledge` is **exact** at every stage (set sym-diff is its own inverse; XOR = Class-M bind). A blank slate stores everything from scratch; a the_one slate stores **nothing** until experience writes a delta. This confirms the user's reading mechanistically and refutes the blank-slate.

**The efficiency has an honest tradeoff (keep vs replace).**
- **ADDITIVE** — learning *keeps* the native scaffold and only adds: stored delta is **< absolute** (0%→70%), and the the_one native is **shared** (computed once, amortised across all individuals, never re-stored). *This* is the storage win, and the biological reading: keep the substrate, add specifics.
- **REPLACEMENT** — learning *discards* native (the F543 high-decay regime): the delta **exceeds** absolute (933%→138%), because the_one's *generic* edges are not the *specific* knowledge. The_one is a great cold-start **prior** (F543) but a poor **compressor** if thrown away.

**So the F543 decay-α is the knob on a real tradeoff:** high decay = no bias on the converged shape (F543 "prior not bias") but a big delta (poor storage); low decay = a small delta (kept scaffold, cheap storage) but the native biases the shape. Biology likely sits where the native is **kept** enough to store cheaply — learning is the XOR that reshapes the substrate-native rules into **etak-shaped** (moving-reference-frame) rules of knowledge. **"Where we see circles we have seen loops":** the wet base is the_one (a loop, held even happily — F544), and learning is the kept-native XOR that reshapes it. Favored not privileged (F398); held open (F394).
