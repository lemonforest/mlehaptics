# Claude Code: Small fix — remove "C17 encoder" misnomer from supplement

## Context

Three occurrences of "C17 encoder" in `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md` on main. All three originated from prompts written by a previous Claude Chat session that mistakenly coined "C17" as a name for the 640-dim chess spectral encoder. This collides with the C language standard (ISO/IEC 9899:2018, "C17"), which is Steven's actual use of the term. The supplement's merged text was auto-adopted from the prompt.

Fix: replace "C17 encoder" references with neutral language. The encoder's actual names in the codebase are `encode_640`, the `chess_spectral` package, or "the 640-dim encoder." Use those.

## Patches

### PATCH 1 — §11.5.6 "What this motivates" paragraph

File: `docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md`

OLD:
```
It is not a modification of the C17 encoder; it is a separate instrument built from the same mathematical discipline, tested against the same CSV produced by §11.5.
```

NEW:
```
It is not a modification of the existing 640-dim encoder; it is a separate instrument built from the same mathematical discipline, tested against the same CSV produced by §11.5.
```

### PATCH 2 — §12 stub opening paragraph

OLD:
```
> **Status.** Working experiment. Triggered by §11.5.6's validated null for path-2 check filtering in the C17 encoder. Asks whether a separate HDC instrument, derived from the same mathematical discipline that produced C17 but targeting king-attack structure specifically, can expose the signal that C17 does not.
```

NEW:
```
> **Status.** Working experiment. Triggered by §11.5.6's validated null for path-2 check filtering in the 640-dim encoder (`encode_640` in the `chess_spectral` package). Asks whether a separate HDC instrument, derived from the same mathematical discipline that produced `encode_640` but targeting king-attack structure specifically, can expose the signal that `encode_640` does not.
```

### PATCH 3 — §12 stub scoping paragraph

OLD:
```
> **Important scoping.** §12 does not modify C17. C17 remains the validated 640-dim encoder for §9 and §11's experiments. §12 is a parallel instrument built to answer a specific question C17 did not answer. If §12 succeeds, the HDC encoder family has a king-attack member; if §12 fails, C17's construction pattern does not support king-attack content naturally and the null result from §11.5 reflects a structural property of that construction pattern, not a gap.
```

NEW:
```
> **Important scoping.** §12 does not modify `encode_640`. The existing 640-dim encoder remains the validated instrument for §9 and §11's experiments. §12 is a parallel instrument built to answer a specific question `encode_640` did not answer. If §12 succeeds, the HDC encoder family has a king-attack member; if §12 fails, the existing encoder's construction pattern does not support king-attack content naturally and the null result from §11.5 reflects a structural property of that construction pattern, not a gap.
```

### Grep verification

After applying:
```bash
grep -c "C17" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md     # expect 0
grep -c "encode_640" docs/chess-maths/PHASE_OPERATOR_SUPPLEMENT.md   # expect 4 or more (existing + new refs)
```

Zero occurrences of "C17" in the supplement after these patches. The term "C17" is reserved for the C language standard in Steven's research vocabulary and should not refer to an encoder.

## Commit

Single commit on a new branch `chess-spectral-phase-operator-c17-cleanup`:

```
docs: remove erroneous 'C17 encoder' references in PHASE_OPERATOR_SUPPLEMENT

'C17' was coined in Claude Chat prompts as a shorthand for the 640-dim
spectral encoder, but it collides with the ISO/IEC 9899:2018 C language
standard (also called C17) which is the term's actual use in the research
vocabulary. Replaced with 'encode_640' / 'the 640-dim encoder' / 'the
chess_spectral package' — the names the code and research notebook
actually use.
```

Open a tiny PR separately from §11.6. This is a standalone cleanup; no other changes, no code impact.

## Scope

- This fix is documentation-only. No code changes, no test changes, no experiment re-runs.
- No other uses of "C17" exist in the merged codebase (verified by grep across notebook, supplement, code).
- Do not merge without researcher approval, but the PR should be small enough that review is quick.
