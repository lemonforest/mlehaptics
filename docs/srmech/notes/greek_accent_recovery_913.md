# #913 — the Greek accent "loss" is a memoryless-projection artifact, not inherent unrecoverability

**Verdict: the original "unrecoverable" reading was WRONG.** It conflated *"a
memoryless per-character casefold cannot restore the accent"* (true) with *"the
accent cannot be recovered"* (false). The tonos is absent from the uppercase
**codepoint stream** but is a fixed property of the **word** — a recoverable
fiber living in lexical structure that a local, context-free map provably cannot
see. Recovery is a *structure-aware inverse* (lexicon + morphology + optional
context), not a memoryless map.

Machine-checked by `python/tests/test_greek_accent_recovery_913.py`.

## The facts

| | codepoints | note |
|---|---|---|
| `ΓΛΩΣΣΑ` | Γ Λ Ω(03A9) Σ Σ Α | uppercase carries **no** tonos (monotonic Greek drops accents in caps) |
| `casefold(ΓΛΩΣΣΑ)` | γ λ **ω(03C9)** σ σ α | the accentless skeleton — memoryless map, no word-model |
| true `γλώσσα` | γ λ **ώ(03CE)** σ σ α | stressed omega — needs the lexeme |

**The sharp proof that structure-aware recovery is real and already shipping:**
`str.lower` *already performs one* — final sigma, `ΟΔΟΣ → οδο`**`ς`**`(03C2)`,
chosen from word-boundary **position** — while dropping the tonos in the same
call. The dividing line is exactly **locally-computable-from-position** (final
sigma: yes) vs **requires-the-lexicon** (accent: no).

## What is recoverable, and the honest tail

- **Deterministic core** — for a lexicon word the skeleton keys a unique
  accented form (`γλωσσα → γλώσσα`), including paradigm stress-**shift**
  (`ανθρωπων → ανθρώπων`, gen. pl.). This is a Class-E catalog ∘ Class-D
  morphology ∘ Class-C which-accent ∘ Class-K present/absent cascade.
- **Irreducible tail** (why it is "deterministic core + probabilistic tail,"
  not total) — heterophonic homographs a word **in isolation** cannot decide
  (`ματια → {μάτια, ματιά}`, `η/ή`, `που/πού`, `πως/πώς`, `αλλα → {άλλα, αλλά}`),
  OOV proper nouns, and syntactic/enclitic accents (the second tonos in
  `ο άνθρωπός μου` depends on the *following* word). These need sentence context.

## Framing (kept honest)

The "abelian projection discards a fiber recoverable via non-abelian structure"
intuition is **directionally sound and made a falsifiable prediction that paid
off** (recoverability) — but it is an **analogy, not a theorem**: `casefold` is
not literally an abelian group homomorphism and re-accentuation is not a lift
through a non-abelian cover. The load-bearing, literal statement is: *a
memoryless projection is lossy exactly where a structure-aware inverse is not;
the discarded information lives in non-local (lexical) structure the local map
cannot see.*

## Scope

srmech does **not** ship a Greek re-accentuator here — a half-built lexicon
would be the "partial/unproven surface" the project bans. The deliverable is the
**corrected understanding + a documenting test** that machine-checks the
mechanism (deterministic recovery is possible; the tail is genuinely ambiguous;
the local-vs-lexical boundary). A full restorer stays a future arc gated on a
properly attested Greek stress lexicon under AMSC, only if a real downstream need
appears.

**Prior art** (attested): diacritic restoration is an established NLP task —
Náplava & Straka *"Diacritics Restoration using BERT"*; *"Dilated CNNs for
Lightweight Diacritics Restoration,"* LREC 2022 (arXiv:2201.06757); Greek is an
actively-surveyed NLP language (arXiv:2408.10962). No Greek accuracy figure is
asserted (that would be unattested).
