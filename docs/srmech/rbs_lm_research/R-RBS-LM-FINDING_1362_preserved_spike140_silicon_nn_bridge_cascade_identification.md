# F1362 — **preserved: Spike #140 — silicon-NN substrate-coupling bridge identification: attention = L+M+C+K, tool-use loop = D+E+C+M+I+A, and an invariant backbone {C, M} across six substrates (stance candidates later attacked in F1363)**

Consolidation record (2026-09-14). Source: local branch `research/spike-140-silicon-net-substrate-coupling-bridge`, one commit on no remote: `f7f3d5e30` (2026-05-18).

## What the commit found (its own words)

*"Key empirical findings:"*

1. A single attention block (Vaswani 2017, arXiv:1706.03762) has class chain **L + M + C + K**. Row-stochastic softmax produces an implicit token-graph Laplacian whose smallest eigenvalue is ~0 (1e-17); LayerNorm is a Class K asymptote to unit variance.
2. The tool-use loop (Yao 2022, arXiv:2210.03629, ReAct) has class chain **D + E + C + M + I + A**.
3. Across 6 substrates (wetware cortex, BCI, BBB, attention block, tool-use loop, full silicon-NN): *"INVARIANT BACKBONE = {C, M}."*
4. Silicon-NN with tool-use engages {L, M, C, K, I, D, E, A}, 8 of 14 classes, and is *"PARTITION-COEXISTENT with BBB-bipartite-substrate pattern."*
5. *"Zero new primitive class. 14 A-N intact."*

It returned three stance candidates *"for conductor direction"* and says *"PR strategy: do NOT merge autonomously."* It lists eleven arXiv anchors as PDF-verified; none was re-verified here.

**Read with F1363.** Spike #141, preserved the next day, attacked these stance candidates. It reports Stance A FALSIFIED, Stance B SURVIVES-WITH-REFINEMENT, and Stance C FALSIFIED under strict-spec definitions.

## Where it lives on PR #687

- **Archive only:** `preserved_branches/research__spike-140-silicon-net-substrate-coupling-bridge/`.
- All four paths were absent here, but two of the commit's scripts (`spike140_attention_as_class_chain.py`, `spike140_tooluse_class_chain.py`) do `import numpy as np`. The consolidation's hard rule is that no numpy is added to this branch, so the commit was not cherry-picked; `git am` re-applies it.

## DIFFERS

None.

**Composes:** F1363.

Branch safe to delete once this commit is on origin: yes

Integrated 2026-09-14: see F1373.
