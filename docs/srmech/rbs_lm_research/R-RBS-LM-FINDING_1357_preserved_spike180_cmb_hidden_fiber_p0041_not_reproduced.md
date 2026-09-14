# F1357 — **preserved: Spike #180 — PR #585's CMB hidden-fiber p = 0.041 is H0-NOT-REPRODUCED under replication, five independent datasets, Bonferroni and a researcher-degrees-of-freedom audit**

Consolidation record (2026-09-14). Source: local branch `research/spike-180-cmb-hidden-fiber-confirmatory-independent-data`, one commit on no remote: `6bb07db03` (2026-05-19).

**User (2026-05-19), as recorded in the commit:** *"Dispatch confirmatory spike before closure"* — the chosen answer for PR #585's "NEW POSITIVE CMB R4-1 chain p=0.04 hidden-fiber correlation claim".

## What the commit found (its own words and figures)

**Verdict: H0-NOT-REPRODUCED.** *"The marginal positive does not reproduce under any of the standard rigor tests."*

| test | figures as printed |
|---|---|
| multi-seed replication of PR #585's exact null (10 seeds, 50 uniform eigenvalues in [0,250], 10,000 trials each) | p 0.0518–0.0584, mean 0.0552; *"PR #585's reported p=0.041 is BELOW ALL 10 replications"*; *"Likely an undocumented outlier seed"* |
| independent datasets | Planck PR3 p=0.19 · WMAP 9yr p=1.00 · ACT DR4 p=0.14 · SPT-3G p=0.87 · Planck PR4 p=0.19 — *"No independent dataset reaches p<0.05"* |
| Bonferroni (5–6 tests in the Spike #47 R4-1 + PR #585 cluster) | corrected alpha 0.010–0.0083; *"Independent best p=0.14 fails Bonferroni by an order of magnitude"* |
| researcher degrees of freedom | 23,760 valid integer chains match Planck peaks within 1.6%; PR #585's chain ranks 745/23,760 (top 3.1 percentile); its Λ=28 entry is 1.63% against the stated 1.6% maximum; the best Planck-faithful chain {2,12,27,52,83,127,174,228} gives p=0.171 |
| structural diagnosis | the squashed-S⁷ spectrum is denser than round-S⁷ (208 vs 25 eigenvalues in the tested range); *"NOT a hidden-fiber correlation; a density artifact"* |

- **F-180-1, process integrity:** *"The actual null-test code that produced p=0.041 does NOT exist in PR #585's committed script. The p-value appears only in the NDJSON output. Load-bearing significance claim has no auditable provenance."*
- **What it keeps:** *"PR #585 PRIMARY verdict (spectrally-distinct; M-theory KK spectrum NOT bit-exactly instantiable on round-S^7) is INDEPENDENT and stands. Only the CMB hidden-fiber sub-claim is retracted."* It lists a five-point recommended amendment to PR #585.
- **Citations it lists as verified (arXiv):** Aghanim+ 2020 arXiv:1807.06209; Hinshaw+ 2013 arXiv:1212.5226; Aiola+ 2020 arXiv:2007.07288; Dutcher+ 2021 arXiv:2101.01684; Akrami+ 2020 arXiv:2007.04997; Ekhammar–Nilsson 2021 arXiv:2105.05229; Nilsson 2024 arXiv:2412.04208. None was re-verified in this consolidation.

## Where it lives on PR #687

All three paths were absent here, and the prototype script does not use numpy, so the commit was cherry-picked with `-x`:

- `docs/srmech/notes/spike180_cmb_hidden_fiber_confirmatory_findings_2026-05-19.md`
- `docs/srmech/notes/spike180_cmb_hidden_fiber_confirmatory_prototype.py`
- `docs/srmech/notes/spike180_records_2026-05-19.ndjson`

Archive: `preserved_branches/research__spike-180-cmb-hidden-fiber-confirmatory-independent-data/`.

## DIFFERS

None.

Branch safe to delete once this commit is on origin: yes
