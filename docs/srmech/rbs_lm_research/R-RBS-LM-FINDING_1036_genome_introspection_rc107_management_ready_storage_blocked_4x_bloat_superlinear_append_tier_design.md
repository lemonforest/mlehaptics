# F1036 (user direction: genome tooling for managed read/write of kernel items + siona context) — **the rc107 genome introspection splits cleanly: MANAGEMENT IS READY, STORAGE IS BLOCKED. Ready (the §41/§43/§44 asks landed): `genome_window` pages ONE chromosome RAM-bounded in 0.026 s; streamed loads; append/remove/replace/pack/catalog/register_attested — exactly the graft/excise/tier ops "training as attested surgery" needs; round-trip EXACT. Blocked (the §55 residue, freshly quantified): (a) 4.03× BLOAT measured (a 64 KB payload chromosome writes 264,230 bytes — each 2-bit Klein-4 symbol still a full byte), so the 3.43 MB F1035 artifact would become ~36 MB as a genome; (b) SUPER-LINEAR append (0.22→0.34 s/append over 40 × 64 KB chromosomes). The user's "it can be both [sparse and dense] — inherent in how we choose to store" is CONFIRMED at the layout level: coarse 64 KB-chromosome chunking puts our kernel at ~136 chromosomes, inside the design regime (the F833 explosion was per-article granularity, 271k chromosomes) — only the two §55 storage items stand between the layout and shipping. FILED → #1245 with the numbers. The TIER DESIGN lodged: `tier0/` = the framework notebooks (contest by MATH, never aged out — MFO's spacetime-not-fundamental stance stands against newer majority claims because nothing gets special rules in the universe: a mathematical contest is answered in math, not outlived); `tier1/<source>/` recency-ordered (new updates old WITHIN a tier via genome_replace); `context/<session>` = siona's persist state as a chromosome; conflicts SURFACE (F1032), never resolve by recency.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc107 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **User direction:** "introspect our genome layer … based on what we've been doing for our surgical quantization, find out what we can and cannot do … suppose someone has an already highly quantized wiki kernel but wants to download the source and rebuild or select other sources … order also matters … new knowledge updates older aged knowledge, but the exception is our MFO notebooks — a tier0 item who can support by contesting with math … such as spacetime is not fundamental … nothing gets special rules in the universe." · **Composes:** F832/F833/F834 (the explosion this re-diagnoses: GRANULARITY was the killer, not the genome), UPSTREAM §55 → **#1245** (the refresh), F1035 (the artifact awaiting its managed form), F1032 (the conflict surface the tiers compose with), `[[feedback_no_spacetime_use_space_time_gauge]]` (the tier-0 exemplar: 11D = 3D_space + 7D_gauge + 1D_time).

## Grounded (rc107) — the capability matrix
```
CAN (measured):                                       CANNOT YET (#1245):
  genome_window 1 chromosome, paged:      0.026 s       (a) bit-packed leaves: BLOAT 4.03x measured
  round-trip window+recall:               EXACT             (64 KB payload -> 264,230 B on disk;
  append/remove/replace/pack/catalog:     present            3.43 MB artifact -> ~36 MB genome)
  register_attested (provenance):         present        (b) append super-linear: 10:2.2s 20:4.6s
  bounds: LEAF_CAP 256 sym | chromosome <= 1024 leaves       39:11.3s (0.22 -> 0.34 s/append)
          = 64 KB payload/chromosome
LAYOUT VERDICT: kernel @ 64 KB chunks = ~136 chromosomes -- IN the design regime.
F833's explosion was 271k per-article chromosomes: the GRANULARITY, not the genome.
```

## The tier design (lodged for the build)
- **tier0/** — the srmech+MFO notebook sections. Contest BY MATHEMATICS, never aged out: recency does not
  defeat a standing mathematical objection (the spacetime case: years of null results on
  spacetime-as-fundamental vs years spent assuming rescue-maths must exist — the tier-0 stance stays live
  until answered IN MATH). Tier-0 is not "always right"; it is "must be answered, not outlived."
- **tier1/<source>/<chunk>** — wiki and later sources, recency-ordered; `genome_replace` is the update op
  WITHIN a tier; cross-tier disagreement SURFACES via the F1032 parallel-source rule + rc105 chiral flux.
- **context/<session>** — siona's --persist state as its own chromosome (managed working memory).
- **Ops = training:** graft `genome_append` / excise `genome_remove` / update `genome_replace`, each
  attested (`genome_register_attested` + op-log). The rebuild/select flow: kernel + op-log lets anyone
  re-derive from source, add sources, or re-order — order is DATA, not accident.

## Verdict / next
**The genome is the right managed home for the kernel and siona context — the layout works today at coarse chunking, the management surface is complete and fast, and exactly two storage items (#1245: bit-packing + linear append) stand between the design and shipping it.** Next: on #1245 landing — the genome-backed kernel build + siona `--persist` into a context chromosome; meanwhile the flat F1035 artifact remains the distributable.
