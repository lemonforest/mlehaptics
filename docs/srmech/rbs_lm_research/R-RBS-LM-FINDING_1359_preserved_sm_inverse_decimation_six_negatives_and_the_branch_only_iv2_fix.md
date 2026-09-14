# F1359 — **preserved: the six-spike SM inverse-decimation series — six negatives, and the §IV.2 decimation-polynomial fix that `main` records as living only on this branch**

Consolidation record (2026-09-14). Source: local branch `research/sm-inverse-decimation-spike`, six commits on no remote (all 2026-05-12).

## What the commits found (their own verdict lines)

| # | commit | verdict and figures as printed |
|---|---|---|
| 1 | `1742bdea2` | *"SG-family R(λ) REFUTED as SM mass hierarchy generator"*. Best-fit decimation depths k_μ = [7, 5, 5] and k_τ = [11, 7, 11] across leptons / up / down: *"No common level structure."* Mean log₅ integer-deviation 0.267 against a random baseline of 0.25 |
| 2 | `f25908163` | *"base-sweep diagnostic is Diophantine-degenerate; eigenvalue-matching alone cannot find THE fractal"*. Per-family fits (leptons b* 1.8725, dev 0.0007; up 2.667, dev 0.0079; down 1.7212, dev 0.0168) against a 10,000-family null: 3% / 48% / 89% percentiles, joint 1.22% |
| 3 | `9eabb62c8` | *"confirms §XIII.1 is at best fractal-decorated Kaluza-Klein"*. SU(2) covers {1,2,3,6} trivially and SU(3)×SU(2)×U(1) tautologically; CP² misses multiplicity 2 |
| 4 | `7993124a2` | *"MFO-natural reframing bounds the problem but doesn't reveal THE candidate"*. SM charged fermions span [0, 25.5] in log-m²; 25.3% of random 9-value scatters reproduce the tested signature; best fit SG3_first9 R² = 0.9503, max residual 3.79 |
| 5 | `df7fb90a8` | *"corrected null reveals no structural signal; SM seesaw pairing ranks 6/15"*. The first draft compared 3-pair RMS with a 6-pair null (bug acknowledged); SM pairing RMS 3.51–4.01 against best 2.69–3.23 |
| 6 | `256ba6b78` | MFO §IV.2: *"Before: R(λ) = λ(5 − λ), R⁻¹(w) = (5 ± √(25 − 4w))/2 · After: R(λ) = λ(5 − 4λ), R⁻¹(w) = (5 ± √(25 − 16w))/8"*, plus a §XIII.1 status block cataloguing the six attempts and the untried test classes (topological invariants, RG flow on the fractal, Connes spectral action, anomaly cancellation) |

Commit 5's cumulative line: *"Six independent honest negatives. None of the eigenvalue-based methods we've tried identifies a fractal candidate reproducing SM structure beyond chance."* Commit 6 attributes the corrected form to *"Strichartz; Bajorin-Chen-Dagan-Emmons-Hussein-Khalil-Mody-Steinhurst-Teplyaev 2008; Kigami's analysis on PCF fractals"*, with no DOI or arXiv identifier.

## What `main` records about commit 6 (read 2026-09-14, not re-run)

`main`'s MFO notebook (Part-I notice, the rc459 retraction dated 2026-08-28) and `main`'s `CHANGELOG.md` cite this commit by SHA:

- *"MEASURED BY ANCESTRY: `git merge-base --is-ancestor 256ba6b78 HEAD` → NOT-ANCESTOR; `git branch --contains 256ba6b78` → only `research/sm-inverse-decimation-spike` … The fix lives on an unmerged branch and `main` never carried it."*
- *"'which polynomial is correct' is a statement about which convention a given construction satisfies — and that is an unrun measurement"*; §IV.2 *"is left standing and flagged rather than 'fixed'"*.
- On the citation: `au:Bajorin` returned 0 arXiv entries, so *"the author-year is removed rather than shipped unattested, and the attribution is left where it actually lives: in that commit message, on an unmerged branch."*

This branch's notebook agrees on the first point. At `4db51be25` it still prints `R^{-1}(w) = (5 ± √(25 − 4w))/2` (line 393) and carries no six-spike status block.

## Where it lives on PR #687

- **Archive only**, all six commits: `preserved_branches/research__sm-inverse-decimation-spike/`, including the five PNG figures as binary patches.
- Commits 1–5 touch only absent paths, but each adds a script that does `import numpy as np` (and matplotlib). The consolidation's hard rule is that no numpy is added to this branch, so none of them was cherry-picked; `git am` re-applies them.
- Commit 6 was not cherry-picked either: its one path, the MFO notebook, DIFFERS.

## DIFFERS

- `docs/antikythera-maths/mfo_spectral_research_notebook.md` — the notebook has moved on by thousands of lines, and this commit's §IV.2 and §XIII.1 edits are on no other ref.

Branch safe to delete once this commit is on origin: no — every byte is preserved in the archive, but `main`'s MFO notebook and CHANGELOG cite commit `256ba6b78` by SHA and use `git branch --contains 256ba6b78` as their evidence. Deleting this branch leaves that SHA unreachable, so those citations should first point at the archived patch, whose `From 256ba6b78…` header carries the SHA. That repointing is a maintainer decision and is not part of this commit.
