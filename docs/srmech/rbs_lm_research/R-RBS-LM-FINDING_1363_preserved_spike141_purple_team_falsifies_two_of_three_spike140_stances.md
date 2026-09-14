# F1363 — **preserved: Spike #141 — purple-team falsification of Spike #140's three stance candidates: A FALSIFIED, B SURVIVES-WITH-REFINEMENT, C FALSIFIED under strict spec**

Consolidation record (2026-09-14). Source: local branch `research/spike-141-purple-team-falsification-spike-140-stances`, one commit on no remote: `ee39d6432` (2026-05-18).

**User (2026-05-18), as recorded in the commit:** *"let's see which statement survives falsification"*

## What the commit found (its own words)

- **STANCE A** (the bridge IS tool-use composed with attention via {C,M}): **FALSIFIED.** Three silicon-NN counter-examples bridge information → operation without both attention and tool-use: a feedforward CNN classifier (L+K+M+K), an LSTM (M+K+I+C) and a Rule 110 cellular automaton (L+E+I+C). *"Intersection of class chains across counter-examples is EMPTY."* DDPM was considered and removed, because Ho 2020 uses attention at 16×16 resolution.
- **STANCE B** (silicon-NN is partition-coexistent with BBB): **SURVIVES-WITH-REFINEMENT.** The class-by-class role audit gives 2 STRONG (E, L under substitution), 1 STRONG-on-partial (I on the tool-use loop), 3 WEAK (D, K, partial I), 1 DIVERGENT under strict HDC spec (M) and 1 AMBIGUOUS (C). Scope must tighten to *"silicon-NN WITH TOOL-USE ENABLED"*.
- **STANCE C** ({C, M} IS the universal substrate-coupling-bridge invariant): **FALSIFIED under strict-spec definitions**, by four counter-examples: Hamiltonian unitary evolution (Hadamard self-inverse verified at 0.00e+00), Bennett 1973 reversible computing / Toffoli, a pure photodetector, and Rule 110. Under a permissive spec it *"survives but unfalsifiable-by-construction"*. Refinement offered: *"'{C, M} IS invariant of MEMORY-WITH-DIRECTION bridges' (narrower; defensible) — but this is NOT what Stance C as written claims."*
- Authoring decision tree returned: autonomously authorable, *"NONE of the three as written"*; needing user direction, Stance B refined and Stance C refined; *"Should be dropped: Stance A literal form, Stance C universal form."* Also *"14 A-N vocabulary intact"* and *"PR strategy: DO NOT MERGE."*

## Where it lives on PR #687

- **Archive only:** `preserved_branches/research__spike-141-purple-team-falsification-spike-140-stances/`.
- All four paths were absent here, but `spike141_stance_a_attack.py` and `spike141_stance_c_attack.py` do `import numpy as np`. Under the consolidation's no-numpy hard rule the commit was not cherry-picked; `git am` re-applies it.

## DIFFERS

None.

**Composes:** F1362.

Branch safe to delete once this commit is on origin: yes
