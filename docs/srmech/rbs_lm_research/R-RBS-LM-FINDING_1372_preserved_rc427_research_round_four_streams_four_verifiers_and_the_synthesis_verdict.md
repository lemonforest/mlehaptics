# F1372 — **preserved: the rc427 `#T1130` research round. Four generative streams, four adversarial verifiers and the synthesis verdict. Their files were already on `main`, but the 15 commit messages that carry the verdicts were on no remote.**

Consolidation record (2026-09-14). Source: local branch `srmech-rc427-research`, tip `7018ec8cc`, 15 commits on no remote, all dated 2026-08-12:

- four rc426 follow-ups;
- the four streams G4/ARROW, G2/REVERSAL, G3/NOTATION and G1/OPGAPS;
- the verifiers V-G4, V2, V3 and V1;
- two collect merges;
- the synthesis.

## Why this needed an archive although no file was missing

Measured on 2026-09-14.

**The files are safe.** All 23 paths the 15 commits touch carry the tip's exact blob on `origin/main` (`b398b8c46`) and on this branch (`2658bee5b`). `git ls-tree` was run at the three refs and the outputs compared with `diff`, which exited 0 both times. On both refs, `git log --diff-filter=A` for `rc427_research_round_synthesis.md` and `reversal_is_not_rewind_rc426.py` names `0ad5b8521` and `93daca2bf` (2026-08-12, *"assemble the build branch, and the collect that had already happened"*; *"carry the rc426 reversal note, the provenance 14 rc427 citations point at"*).

**The messages were not.**

- None of the 15 exact subjects occurs among the 6,500 commit subjects reachable from any remote ref (`grep -Fx`, 0 matches).
- Five distinctive body phrases also occur 0 times in the remote commit messages: `SHIPPED-OP DEFECT: oct_torsor_act is an ANTI-action`, `FV1 REFUTED`, `the forcing law forced nothing`, `six-to-eight op arithmetic rc` and `THE rc424 MUSIC REJECTION STANDS`.
- In `main`'s files, only two of those phrases (plus a rc426 verdict row) appear: `six-to-eight op arithmetic rc` at `rc427_research_round_synthesis.md:505`, and `REVERSAL IS NOT REWIND, CONDITIONALLY` in the rc426 note pair.

So the per-stream verifier verdicts, the retraction, and each commit's list of its own instrument failures existed only in these messages.

## What the commits found (their own words)

- **rc426 reversal note** (`70c3a0c5b`). *"CHIRAL reversal is co-extensive with the FORWARD law on EVERY carrier — set equality, not merely equal counts — including the non-associative octonion unit loop. BARE reversal is not, except where the carrier is abelian."* The same message says *"SHIPPED-OP DEFECT: oct_torsor_act is an ANTI-action, not an action."*
- **§9b** (`3318fe34a`). *"So the arrow is a property of the INPUT z, not of the operator's own equation."*
- **Set, not count** (`976f73340`). The verdicts now carry set-overlap fields, and *"the O16 row reads REVERSAL IS NOT REWIND, CONDITIONALLY."*
- **Retraction** (`f210148bb`). *"RETRACTION. An earlier record in this note called the oct_torsor_act composition order a shipped DEFECT. That was an OVERCLAIM and is withdrawn."* The existing test `test_oct_torsor_rc388.py` already asserts the reversed order.
- **G4/ARROW** (`a9ded6c83`).
  - *"(a) YES, buildable exactly and closed-form: T_c(x) = mod_mul(x, c, n) with gcd(c,n) > 1."*
  - *"(b) The loss is exactly legible — ker T is a subgroup of order gcd(c,n), fibres uniform on 37/37 — AND THAT IS THE PROBLEM."*
  - *"\"Monoid torsor\" is VACUOUS."*
- **G2/REVERSAL** (`408d86207`).
  - *"Class C on ORDER SURVIVES."*
  - *"Class K on INVERSION is REFUTED, twice."*
  - *"\"K THEN C\" is EMPTY as a sequencing claim"*
  - At the loop the "commuting probability" rate is *"THREE different rationals — bare 43/64, Pr(G) 11/32, k/|G| 9/16"*.
- **G3/NOTATION** (`1af5b41c6`).
  - *"A spelling-fibre op is therefore REJECTED: it would re-ship `srmech.math.covering.lift_fibre`."*
  - On the rc426 leak test: *"This is a BOUND on the committed F12b instrument, not a refutation — every verdict it returned stands."*
  - *"FORM, not identity."*
- **V-G4 verifier** (`e5d56b76f`).
  - CONFIRMED: the closed form *"agrees with an independently written enumeration oracle on ALL 1,829 cells with 2 <= n <= 60, 0 <= c < n"*.
  - REFUTED: *"the Poly escape hatch's \"negative control\" is a literal tautology"*.
- **V2 verifier** (`1a6d68383`).
  - *"FV1 REFUTED — the stream lead measurement is ENTAILED, not observed."*
  - *"FV3 REFUTED — chiral_reversal is one shipped chiral_flip call over a mapped word, zero decision branches"*.
  - *"FV2 BOUNDED — NC3 is VACUOUS on the abelian rows (4 of 8 measured)."*
  - *"FV4 EMPTY"*.
- **V3 verifier** (`8cbd96e8e`).
  - *"REFUTED (V1): \"the alphabet size is a THEOREM of the generator, a = g^-1 mod n, 0 failures across 188 cells\" is an instrument that cannot return otherwise."*
  - *"DEFECT (V9): action_lattice_read's homomorphism verdict tracks whether the tuning is anchored at 0, not the lattice."*
  - It also records TAUTOLOGY (V8) and CLASS (V10).
- **G1/OPGAPS** (`251f81d20`).
  - *"FB2: an unguarded class-equation op reports 144 where the truth is 88 (M16) and 544 where the truth is 184 (M32), silently. The associativity guard IS the op."*
  - *"THE rc424 MUSIC REJECTION STANDS, re-examined and not overturned"*.
  - *"TWO PRE-REGISTERED FALSIFIERS FIRED AGAINST ME. FC1a (ladder) and FC1b (off-ladder) are both UNSUPPORTED"*.
- **V1 verifier** (`d359cfd42`).
  - REFUTED: the FA3 decision, because the downstream 13824 vs 5184 is identical under both conventions.
  - *"The two conventions are ISOMORPHIC"*.
  - *"FC3's \"three Moufang identities fail on pairwise-disjoint halves\" is SPELLING-DEPENDENT."*
- **Synthesis** (`7018ec8cc`).
  - *"G1's `conjugacy_census` and G2's `commuting_probability` are the SAME op with two calling conventions."*
  - G2's required callables cannot cross JSON-RPC, so both census ops take a Cayley table.
  - *"Verdict: a six-to-eight op arithmetic rc. All four G3 notation ops rejected."*
  - *"Registry 649 -> 656 projected; 17 ripple surfaces named, and the one gate that catches a lying `returns=` is CI-only."*
  - *"READ-ONLY: no version bump, no package source touched, no PR, not pushed."*

The two merges (`9370558d3`, `3acf4bc34`) only collect the verifier commits. Their messages are subject lines.

This record relays what the messages say; it did not re-run any of their measurements. Whether a later rc built the synthesis' six to eight ops was not checked here.

## Where it lives on PR #687

- **Archive:** `preserved_branches/srmech-rc427-research/`.
  - 13 patches from `git format-patch srmech-rc427-research --not --remotes`: the 13 non-merge commits, oldest first. format-patch omits the two merges.
  - A `TIP.txt` with the commit list and the per-path status against `origin/main` and this branch.
- **Nothing cherry-picked.** Every touched path is already here with the tip's blob.
- **Merges.** Both parents of each merge are commits of the same unpushed series (`9370558d3` = `251f81d20` + `d359cfd42`; `3acf4bc34` = `9370558d3` + `8cbd96e8e`). `git show --cc` prints no hunks for either.
- **README.** `preserved_branches/README.md` ends by saying this source *"is recorded in the PR #687 body only and has no folder here"*. That was true when it was pushed and is superseded by this folder. The README stays unedited under the additive-only rule.

## Re-apply proof (2026-09-14, scratch clone made with `git clone --no-checkout --shared`)

```
git checkout --detach a532b2fa92dc0394ee443ad56db69eb507ced297   # parent of 70c3a0c5b; contained in origin/main
git am --keep-cr preserved_branches/srmech-rc427-research/0*.patch   # 13 of 13 apply
git rev-parse HEAD^{tree}                  -> 42edd00b8a3d4e61aa14f42317cc984af231d775
git rev-parse 7018ec8cc^{tree}             -> 42edd00b8a3d4e61aa14f42317cc984af231d775   (EQUAL)
```

The linear series reproduces the merged tip tree exactly, so the two merges carry nothing the patches lack.

Branch safe to delete once this commit is on origin: yes

Integrated 2026-09-14: see F1373.
