# F1360 — **preserved: the Killing–Yano Kerr hidden-symmetry literature review (verdict PARTIAL), with the three attribution corrections that PDF extraction caught**

Consolidation record (2026-09-14). Source: local branch `research/killing-yano-literature-review`, three commits on no remote (2026-05-12). The one touched path was absent here, so all three commits were cherry-picked with `-x`, in order.

## What the commits found (their own words)

- `4b49b16ec` — *"Verdict: PARTIAL — the structural ingredients are in place across three distinct literatures (CMS low-frequency SL(2,R)^2, photon-ring emergent SL(2,R) in the eikonal limit, and the principal-CKY commuting-operator tower …), but no published paper assembles them into a closed-form C_KY = lambda_{s,lm}(a omega) + ... identity analogous to the C_L + C_R = 2 lambda_S^2(l) result of Spike #9 / PR #356."* It lists 15 paper anchors and 5 MFO-attack gaps.
- `11409fc8b` — arXiv:2401.03553 is by **Gray and Kubizňák (2024)**, not Houri–Tanahashi–Yasui; four locations are corrected (caught by Spike #11, PR #359). It records its own limit: *"Spike #11's PDF extraction verified the AUTHORS and arXiv ID, but did NOT independently verify the title or journal ref"*, and both are flagged for re-verification.
- `c85259c47` — two more corrections, caught by Spike #12A (PR #361). The HKLS 2022 *"Holography of the Photon Ring"* paper is **arXiv:2205.05064**; the listed arXiv:2207.06435 resolves to an unrelated paper. arXiv:2309.02262's authors are **Xue, Jiang and Zhang**.

`4b49b16ec`'s own message still names "Houri-Tanahashi-Yasui 2024"; the file as landed is the state after `c85259c47` and carries the corrected attributions. No reference was re-fetched in this consolidation.

## Where it lives on PR #687

- Cherry-picked with `-x` (three commits): `docs/srmech/notes/killing_yano_kerr_literature_review_2026-05-12.md`.
- Archive: `preserved_branches/research__killing-yano-literature-review/`.
- `docs/srmech/notes/spike_12b_lie_algebroid_ky_bracket_scope_2026-05-13.md:270`, on this branch and on `main`, points at this review as *"on branch `research/killing-yano-literature-review` at `c85259c`"*. The same file now sits at that path on this branch.

## DIFFERS

None.

Branch safe to delete once this commit is on origin: yes — the spike-12b pointer names the branch and `c85259c`; after deletion the content resolves at the same path here and byte-exact in the archive.

Integrated 2026-09-14: see F1373.
