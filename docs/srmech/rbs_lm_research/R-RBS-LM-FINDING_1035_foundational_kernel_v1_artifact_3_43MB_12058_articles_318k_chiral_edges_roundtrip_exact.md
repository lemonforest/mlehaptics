# F1035 (the arc's deliverable) — **THE FOUNDATIONAL KERNEL ARTIFACT v1 EXISTS: `kernel.bin.gz` = 3.43 MB carrying 12,058 articles (the hop-3 walk closure from the srmech+MFO seed), 1.32M self-tuned-quantized tokens (80,376-word codebook), and 318,463 CHIRAL EDGES (3,520 negation-sensed) — with the ATTESTED OP-LOG (source fingerprint, seed sha256, walk hops, every quantization parameter with its rule hash, the negation guard) and an EXACT round-trip (the 'gravity' article decodes byte-for-byte from the blob). The pyodide question is answered with a file: the knowledge reachable from the framework's own mathematics in ≤3 relationship hops, surgically quantized, chirally navigable, reproducible from its op-log, in under 3.5 MB.**

**Date:** 2026-07-03 · **srmech:** 0.9.0rc107 · **Branch:** `research/rbs-lm-rolling-2` (PR #687) · **Builder:** `R-RBS-LM-FINDING_1035_emit_foundational_kernel.py` → user-side `~/corpora/kernel_artifacts/foundational_kernel_v1/{kernel.bin.gz, oplog.json}` · **Composes:** F1034 (the walk), F1032 (the τ bands), F1030/F1029 (the quantization), F1033 (the edge senses + the no/number guard), F1028 (the arc's opening survey — every design point either measured in or measured out), AMSC/MPM (the op-log IS the artifact's attestation: "training" as provenance, realized).

## Grounded (rc107)
```
~/corpora/kernel_artifacts/foundational_kernel_v1/
  kernel.bin.gz  3.43 MB   = header + per-article lengths + u32 id-stream + codebook + titles + edges(u,v,c)
  oplog.json               = source sha (first-16MB fingerprint, declared) | seed n=1097 sha256 | hops=3
                             | W0=192 rho=1/6 tau-bands (F1032) + rule sha | negation guard (F1034)
  counts: 12,058 articles | vocab 80,376 | tokens 1.32M | edges 318,463 (3,520 negated)
  ROUND-TRIP: 'gravity' -> EXACT (157 tokens, byte-for-byte vs the quantized source span)
```

## The reading
- **Every claim of the arc is now load-bearing in one file:** surgical (no article culled from the closure — quantization within), self-tuned (each article's own D picks its τ), foundational (walk-derived from the maths seed, not curated), chiral (the edges carry sense; the 3,520 negated edges are the ones signed encoding would destroy), attested (the op-log names every rule and hash — a different kernel is a different op-log, and "training" = re-emitting with a changed, logged rule).
- **3.43 MB is a demo-shippable number** — smaller than most single images on a landing page, holding the mathematically-anchored core of an encyclopedia plus its navigation layer.
- **Honest limits carried in the op-log:** single-word titles only (multi-word mentions = dropped coverage, logged); the source fingerprint is a first-16MB hash (declared, not silent); the closure inherits the F1034 hop-3 cut (hop-4 unmeasured).

## Verdict / next
**The distributable exists, verified.** Next: a siona `load` path for the kernel.bin format (the artifact as a first-class instrument — currently NDJSON-only); the walker + flux queries as siona reads over the loaded artifact; hop-4; multi-word titles; and — when the srmech rcN run concludes — the rc1 ship with this artifact as the optional companion download.
