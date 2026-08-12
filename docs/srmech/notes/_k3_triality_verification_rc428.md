# The k=3 triality over rc428 — what a third verifier bought, measured

`#T1126` / `#T1131` · adjudication of three co-equal verifiers over `srmech-rc428`
(0.9.0rc428, registry 655, ABI 14) · 2026-08-12

This is a **research result about verification method**, not a build report. The
question the maintainer asked is narrow and answerable: *does a three-way
verification buy anything over one?* Everything below is measured on this one
build, and the bound at the end says so.

---

## 0. The instrument, and what it can and cannot return

Three verifiers — **8v** (opus, instrument lens), **8s** (sonnet, citation-truth
lens), **8c** (haiku, will-CI-go-red lens) — answered an **identically-worded**
pinned question set P1–P5 and then reported through their own lens. The
adjudicator (a fourth reader) re-ran every disputed item with its own commands.

The measurement can return **"nothing"**: if all three reps had agreed on all
five questions and no rep had found a finding the others missed, the honest
result would have been *the second and third verifier bought nothing*. It did
not return that. It also could have returned *the majority was right* — the
adjudicator pre-registered the disputed item as a falsifier and would have
reported 8v wrong had `run_controls` raised. It did not raise.

Environment verified before anything was derived: `srmech.__file__ =
…/docs/srmech/python/srmech/__init__.py`, `__version__ = 0.9.0rc428`,
`len(get_tool_schema().tools) == 655` **after** `warmup_all()`,
`SRMECH_ABI_VERSION 14`, numpy absent, WSL2.

---

## 1. Agreement rate on P1–P5

| | 8v (opus) | 8s (sonnet) | 8c (haiku) | verdict |
|---|---|---|---|---|
| **P1** gate fires on fabricated attribution | YES | YES | YES | **UNANIMOUS** |
| **P2** gate spares correct citations non-vacuously | YES | YES | YES | **UNANIMOUS** |
| **P3** can extraction report a present term absent? | **SILENTLY-BLESSES** | ABORTS | ABORTS | **MAJORITY 2-1 — the MINORITY is right** |
| **P4** `Cayley-Dickson` count in `arXiv:math/0105155` | 22 | 22 | 22 | **UNANIMOUS** |
| **P5** does anything reach the network at test time? | NO | NO | NO | **UNANIMOUS** |

**Agreement rate: 4 / 5 unanimous (80%). 1 / 5 split. Zero abstentions.**

All four unanimous answers were re-measured by the adjudicator rather than
accepted: P1/P2 by driving the shipped `_evaluate` over four fabricated and
three correct locator claims (4 FIRE, 3 spared by non-zero counts of 36/2/16);
P4 by an independent fetch and an independently-written dash-tolerant matcher
(22 = 18 en-dash + 4 ASCII, and the shipped `search()` agrees); P5 by re-running
`tests/test_citation_manifest_rc428.py` with `socket.socket.connect` /
`connect_ex` / `create_connection` / `getaddrinfo` all raising — **21 passed in
17.94s**.

The one split is the one that mattered. Majority-voting it would have shipped
the wrong answer to the only question on this list whose wrong answer is
dangerous.

---

## 2. The dissent, adjudicated

**P3 as asked:** *can the extraction return "term absent" when the term is
present, without aborting?*

8s and 8c both answered ABORTS. Both reached that answer by exercising the
instrument's **own built-in fixture set** — `abort_path_bite_test()`, three
cases (empty / whitespace-only / plausible-but-wrong). 8s ran it for real, which
is honest work; but the case set was the instrument's, not the verifier's.

8v constructed **six** breakages instead of three and reported that two of them
do not abort. The adjudicator rebuilt both from an independent fetch of the real
source (`arXiv:math/0105155` e-print, sha256
`90b0bceb7c536a20400ac417fcc5d3b7d3d07e09f47ef7e4f0e1a624eedeb557`, matching the
shipped manifest's `source_eprint_sha256` exactly):

| breakage | positive control | `run_controls` | would have reported |
|---|---|---|---|
| baseline (true text) | `octonion` = 172 | PASS | `Cayley-Dickson` = 22 ✓ |
| **latin-1 misdecode** | `octonion` = **172** (ASCII survives) | **NO ABORT** | `Cayley-Dickson` = **4** (true 22) |
| **truncation to 2%** | `octonion` = **1** (head retains it) | **NO ABORT** | `Cayley-Dickson` = **0**, `Hopf` = **0** (true 22 / 20) |

**8v is right; the majority is wrong.** The extraction can report a present term
absent and does not abort. The `multi_spelling` control *does* detect both cases
(`count=4 expected=22 verdict=FAIL`, `count=0 expected=22 verdict=FAIL`) — and
`build_rows` never reads it.

**8v was not error-free inside its correct dissent.** It reported the latin-1
case as `Hopf=21 CD=7`; the adjudicator's construction gives `Hopf=20 CD=4`. The
direction and the verdict reproduce; the two integers do not. A correct minority
is still a minority that must be re-measured, not adopted.

---

## 3. What each rep found that no other rep found

This is the direct measure of what each additional perspective bought.

### 8v — 6 unique findings (all adjudicator-confirmed)

1. **The controls that catch the encoding trap are computed and discarded.**
   `tools/build_citation_manifest.py:1000-1006`. Adjudicator-verified: `grep` for
   `multi_spelling` / `negative_verdict` / `always_true_terms` / `u_fffd_present`
   over `tests/` and `srmech/` returns **zero matches**; the emitted source row
   (`:1032`) carries `positive_control` only; `run_controls(gs_text, …)` at
   `:1006` discards its return value; `main()`'s only return is `return 0` at
   `:1506`, so `--validate` exits 0 while printing `DEAD SEAM`.
2. **Variant asymmetry** in the shipped gate's `_evaluate`
   (`tests/test_citation_manifest_rc428.py:174-179`) — matches the canonical term
   only, while the manifest counts canonical **+ variants**. Confirmed; census
   reproduces 8v's **12 of 32** watchlist rows never named, exactly.
3. **`tex_sections` does not strip LaTeX `%` comments.** Confirmed by injection:
   Baez labels shift `[§1,§1.1,§2,§2.1,§2.2,§2.3,§2.4,§3…]` →
   `[§1,§2,§2.1,§3,§3.1…]`. Latent: 0 commented-out sectioning commands in both
   sources (4 and 19 comment lines respectively).
4. **No extraction-completeness check** — the truncation row in §2 is the
   demonstration.
5. **Docstring claims a safeguard the code does not implement**
   (`:682-689`): "fall back ONLY with the encoding recorded, never silently" —
   `except UnicodeDecodeError: text = raw.decode("latin-1")` records nothing.
6. **Commit-count discrepancy** — report says 5, `git rev-list --count
   origin/main..HEAD` = **6**.

### 8s — 2 unique findings

1. **`malcev_defect`'s docstring names a test that never calls it.**
   `srmech/cascade/cayley_dickson.py:2412` + the S3 fixture at
   `tests/test_citation_manifest_rc428.py:383`. Adjudicated **PARTIALLY
   CORRECT**: `tests/test_loop_bind_moufang.py` contains zero occurrences of
   `malcev_defect` (8s's grep is right), **but** its
   `test_jacobi_fails_malcev_holds` does execute the Mal'cev identity on 𝕆
   (`assert _normsq(mal) < 1e-18`) via the HDC loop-bind path. So the docstring's
   *substantive* claim is true; what is false is the implication that the named
   test exercises **this op**. `tests/test_moufang_loop_rc398.py` does.
   The **fully-confirmed half is stronger than the half 8s led with**: the S3
   gate asserts only `(PY_ROOT / named_test).exists()` plus a verdict-marker
   substring. It never checks the named test exercises anything, so any
   existing-but-unrelated filename passes.
2. **Independent source-truth reads** — Schafer ch. II eqn (11), ch. III (1)-(2),
   (6′), (7)-(9) line-for-line against the Gutenberg TeX; Baez §3.1's Hopf-bundle
   table and §4.2's 𝕆P² statement verbatim. **Not re-verified by the
   adjudicator** — recorded as such rather than blessed. Partially corroborated
   numerically: `Hopf` reads 16 at §3.1 and 0 at §4.2.

### 8c — 0 unique findings

8c produced **no defect finding of its own**. Its unique contribution was
*breadth of gate execution* (a full `ripple_check.py` sweep, `--collect-only`,
version-SSOT and gate-registration checks) — verification of the kind that
confirms rather than discovers. The adjudicator re-verified two of its claims
(`tests/test_citation_manifest_rc428.py` present in **both**
`tools/ripple_gates.txt:266` and `FROZEN_KNOWN_GATES` at
`tests/test_ripple_manifest_covers_known_gates.py:160`; version SSOT at rc428) —
both true.

**This is a real result and it is worth stating plainly: the third rep found
nothing the other two had not.** It was also wrong on P3.

### Adjudicator — 1 finding no rep produced

`backend_pypdf`'s docstring (`tools/build_citation_manifest.py:606-611`) says
pypdf is *"REJECTED for counting — proven to under-report 22 -> 16"* and adds
*"If this ever starts agreeing with ghostscript, that is itself a finding worth
chasing."* **Measured on the real PDF** (sha256 `f8087fb9…`, matching the
manifest's `source_pdf_sha256`): under the **shipped dense matcher** pypdf
returns `Cayley-Dickson` = **22** and `octonion` = **172** — identical to
ghostscript. The 16 is a property of **naive whitespace-sensitive** matching
(`naive_vs_dense_check` on pypdf: naive 16, dense 22, 6 missed literals such as
`Cayley–Dick son`), not of the backend on the path the manifest uses. The
docstring's own trigger condition is therefore **satisfied right now and
unchased**, and its REJECTED framing is a false statement about a control in the
rc whose subject is false statements about controls.

8s came closest — it measured pypdf at 16–21 naive — and concluded the opposite
way, treating the discrepancy as its own methodology error rather than as the
docstring's.

---

## 4. Was any rep wrong on a pinned question?

**Yes. 8s and 8c were both wrong on P3.** Named, with the check that decided it
in §2. The adjudicator did not assume the strongest model was right and did not
vote; it re-ran the disputed item and let `run_controls` answer.

Model tier is not evidence here and must not be read as such: **n=1**. The
correct rep also carried a quantitative error inside its correct dissent (§2).

---

## 5. Correlated failure — the bound this puts on triality

**Two of three reps made the same mistake, in the same direction, for the same
reason.** 8s and 8c both answered P3 by exercising the instrument's own
`abort_path_bite_test` fixture set and reporting what it returns.

That is a textbook **common-mode failure**, and its shared cause is not a
coincidence of two models: it is the shared prior *"the built-in self-test
defines the failure space."* All three reps are same-family models with shared
training lineage, which is precisely the condition under which N-version
redundancy delivers less than independence would predict.

The bound this puts on triality is specific: **triality protects against
independent error and does NOT protect against a shared prior.** On this build
the protection held only because one rep happened to construct its own breakages
rather than run the shipped ones. Had 8v done what 8s and 8c did — which is the
*reasonable* thing to do — the triality would have returned 3/3 ABORTS and been
unanimously wrong, with higher confidence than a single verifier would have had.

The mitigation this measurement supports is not "more reps". It is **assigning
at least one rep a lens that forbids using the instrument's own fixtures** —
which is, in retrospect, exactly what "instrument lens" was supposed to mean and
what the other two lenses did not require.

---

## 6. Cost, and where the marginal return stood

| rep | unique confirmed findings | wrong on a pinned Q | contribution kind |
|---|---|---|---|
| 8v (opus) | **6** (+ the P3 dissent) | no | discovery |
| 8s (sonnet) | **2** (1 partial, 1 unverified) | **yes (P3)** | source-truth + one gate-semantics gap |
| 8c (haiku) | **0** | **yes (P3)** | breadth confirmation |
| adjudicator | **1** | — | dispute resolution + one new finding |

A fourth reader found a fourth thing. On this build the marginal return of an
additional perspective had **not visibly saturated at N=3** — but that is one
observation, not a curve, and it is not offered as one.

---

## 7. Verdict and honest bound

**BOUNDED.**

- **What is established:** the triality changed the answer to 1 of 5 pinned
  questions, and changed it *away* from the majority. It surfaced 8 unique
  confirmed findings that a single verifier would have had to find alone. On this
  build, three-way verification bought something real and specific.
- **What is NOT established:** that N=3 is the right N; that model tier predicts
  correctness (n=1); that the marginal return of a 4th reader generalises; that
  the agreement rate 4/5 estimates anything about future builds.
- **What is REFUTED:** the implicit claim that agreement among same-family reps
  raises confidence proportionally. Two of three agreed, in the same wrong
  direction, from the same shared prior. **Agreement among reps that share a
  prior is not independent evidence, and the 2-1 majority here would have been
  the wrong answer with two votes behind it.**
- **Scope:** n = 1 build, 1 task, 1 model family, 5 pinned questions, one
  adjudicator who is also same-family. Nothing here is a claim about N-version
  programming in general.

The single most valuable row in this table is the P3 line, and it exists only
because the protocol required the adjudicator to **check the disputed item
rather than count votes**. That rule is doing the work, not the number three.
