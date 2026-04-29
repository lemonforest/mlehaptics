# chess-spectral v1.5 docs audit — overstrong claims & inadequately-hedged extrapolations

**Date:** 2026-04-29
**Branch:** `chess-spectral/v1.5-docs-audit-and-bridge-api` (forked from
`chess-spectral/v1.5-bridge-integration` at commit `74c6e84`).
**Audited surface:** every doc added or substantively modified between
v1.3.2 (commit `775a571`, last shipping release) and the v1.5 bridge
integration tip.

---

## How to read this report

Each finding is keyed `[F##]` with severity:

- **STRONG** — load-bearing overclaim. Either an unqualified novelty
  assertion without a prior-art survey, a prescribed threshold dressed
  as a logical gate, or a cross-domain extrapolation re-presented as a
  chess prediction.
- **MEDIUM** — rhetorical numbers framed as quantified analysis,
  aspirational scope claims, or wording that rounds an opinion into a
  fact.
- **WEAK** — wording polish that makes the hedge clearer; not load-
  bearing on its own but worth fixing while the audit is open.

Findings are organized by file. The "current text" quote is the
problematic span; "issue" names the overclaim category; "suggested
rewording" is a starting point — the user should refine before applying.

The user has already softened two flagged spans (research notebook
§16.5 "first 4D chess engine ever shipped" and §16.7 "must test at
L4/L8/L16"; see `git diff` in the worktree); those soft-landings are
not re-raised here. The audit covers the rest of the surface.

---

## Findings

### `docs/chess-maths/chess_spectral_research_notebook.md`

#### `[F01]` STRONG — §15.1, line 2434

> *"That combination doesn't exist on PyPI today. … chess-spectral is
> a working `H(4, 8)` implementation; the structure ports to any
> `H(d, q)` with modest changes …"*

**Issue.** "Doesn't exist on PyPI today" is a categorical absence claim
without an exhaustive PyPI survey. PyGSP / escnn / e3nn / Qiskit / lattice
QCD are named as nearby projects with comments on why each doesn't fill
the gap, but the implicit "we have looked at the rest of PyPI" is not
substantiated.

**Suggested rewording.** "We are not aware of a single PyPI package
combining these four properties; the named adjacencies (PyGSP, escnn,
e3nn, Qiskit, lattice QCD frameworks) each cover a strict subset. A
dedicated `Z_n^d` Hamming-scheme + `B_d` toolkit would be useful even
if a partial overlap exists; an exhaustive prior-art survey is
out of scope for this notebook."

---

#### `[F02]` STRONG — §15.2(2), line 2442

> *"The engineering 'choice' of basis is actually a representation-
> theoretic theorem; full diagnostics in [`spectral_identity_4d_findings.md`]
> … This is what makes the encoder canonical rather than ad-hoc — any
> `B_4`-equivariant function on Z_8^4 lattice configurations decomposes
> naturally in this basis."*

**Issue.** "Theorem" is doing real work here, but the supporting probe
(Pre-flight 3) is a *numerical verification at machine precision* on a
specific finite construction — that is strong evidence but not a
mathematical theorem. The standard statement (CSCO basis on a finite
group action on `L²(graph)`) is a theorem in the literature; what *we*
showed is that the encoder columns realize it. Compounded with "This
is what makes the encoder canonical" the language presents a numerical
verification as a self-supplied theorem.

**Suggested rewording.** "The encoder's columns are numerically
verified to be a simultaneous eigenbasis of (Δ, B_4 commutant) at
machine precision (Pre-flight 3). The mathematical statement that any
finite-group-equivariant function on the underlying lattice
decomposes in the simultaneous eigenbasis of the commutator algebra is
classical (Bouckaert–Smoluchowski–Wigner 1936; cf.
[spectral_identity_4d_findings.md] for citations); our contribution is
constructing the basis explicitly and verifying it is the one the
encoder uses."

The exact same softening should land in
[`spectral_identity_4d_findings.md` line 111](../python/research/spectral_identity_4d_findings.md)
("The encoder's tensor-DCT basis … is _canonical_") — same overclaim,
restated.

---

#### `[F03]` MEDIUM — §15.6, line 2487

> *"The mathematical content here is 0% novel — every individual
> ingredient is well-established. The toolkit packaging is ~70% novel:
> no single PyPI package combines what chess-spectral with qm_4d will
> provide. The chess-as-4D-spectral-physics framing is ~95% novel for
> chess specifically."*

**Issue.** The user explicitly flagged these "0% / 70% / 95%" as
rhetorical-numbers-presented-as-quantified-analysis in the prompt.
None of the three percentages is sourced or measurable. The range
0%–100% over three categories does double duty as both "honest scope"
language and as if-it-were-a-survey numerics.

**Suggested rewording.** "The mathematical content uses well-
established ingredients; the value is in the assembly. We are not
aware of a single PyPI package combining the four properties listed
in §15.1, and we have not seen the chess-as-4D-spectral-physics
framing in the literature for chess specifically — both observations
are 'as far as we have looked,' not survey conclusions."

---

#### `[F04]` STRONG — §15.6, line 2489

> *"The spectral identity in §15.2(2) is the cleanest of these: the
> encoder's basis IS the simultaneous eigenbasis of (Δ, B_4
> commutant), at machine precision. That's a clean math statement,
> and it's the theorem underlying every claim about 'B_4 equivariance
> for free.'"*

**Issue.** Restated form of `[F02]`. "The theorem" is again an
unqualified self-attribution; the supporting structure is numerical.
Should be softened the same way.

**Suggested rewording.** "The spectral identity in §15.2(2) is the
cleanest of these: the encoder's basis is numerically verified
(Pre-flight 3) to be the simultaneous eigenbasis of (Δ, B_4 commutant)
at machine precision. The classical theorem (CSCO on finite-group
representations) provides the structural reason; the verification
shows our specific construction realizes it."

---

#### `[F05]` STRONG — §15.4, item 1, line 2471

> *"Pedagogy and teaching. … no shipping educational toolkit covers
> Z_n^d analysis end-to-end with both engineering and physics APIs."*

**Issue.** "No shipping educational toolkit covers" is a categorical
claim. The pedagogy field has Sage, GAP, Mathematica notebooks,
educational Python projects under various universities — even if none
is *quite* this, the unqualified "no shipping toolkit" reads stronger
than what we can defend. Compounds with `[F01]`.

**Suggested rewording.** "We are not aware of a Python educational
toolkit that covers Z_n^d analysis end-to-end with both engineering
and physics APIs; SageMath / GAP / Mathematica notebooks exist in
research papers but no PyPI-installable package fills the same niche
in our experience. Treat this as 'a real gap as far as we can see,'
not as a survey finding."

---

#### `[F06]` STRONG — §15.4, item 3, line 2473

> *"Quantum-walk research on Hamming graphs. The arXiv:2509.26243
> audience (symmetric coined quantum walks on Hamming graphs) needs
> reference implementations to validate theorems against. chess-spectral
> with qm_4d gives them a parity-tested substrate."*

**Issue.** Two compounding overclaims: (1) "needs reference
implementations" as a stated requirement of an external audience whose
needs we have not surveyed; (2) "gives them a parity-tested substrate"
asserts our toolkit is fit-for-purpose for a community we have not
engaged. The cited paper is a single 2025 arXiv preprint.

**Suggested rewording.** "Quantum-walk research on Hamming graphs.
The arXiv:2509.26243 line of work (symmetric coined quantum walks on
Hamming graphs) is a candidate user of reference implementations;
chess-spectral with qm_4d may be a useful substrate. Whether the
substrate matches their needs is a question for that community, not
a claim we should make for them."

---

#### `[F07]` MEDIUM — §16.7, "Implications for Phase 6 design", item 4, line 2593

> *"The QM-expectation evaluator is the more interesting test. Spectral
> channel-energy weighting is structurally close to what Othello tested
> and likely faces the same shallow-strong / deep-vanishing decay."*

**Issue.** "Likely faces the same … decay" extrapolates the Othello
finding to chess. The Othello → chess depth translation was the
user-flagged example of methodological inheritance, not a logical
mapping. Even softened in the §16.5 text and in the §16.7 item 1
text, item 4 still asserts the prediction.

**Suggested rewording.** "The QM-expectation evaluator is the more
interesting test. Spectral channel-energy weighting is structurally
close to what Othello tested; whether chess inherits the shallow-
strong / deep-vanishing pattern is genuinely open — chess's larger
branching factor and the much weaker material baseline (vs Othello's
Edax) make a clean analog non-obvious. Plotting per-depth ELO deltas
is what tells us whether the pattern transfers."

---

#### `[F08]` MEDIUM — §16.7, "Updates to §16.5", final bullet, line 2604

> *"(new) Per-depth signal decay curve. Plot ELO delta vs search depth
> for each evaluator. This is the most informative single chart Phase
> 6 can produce — directly comparable to the Othello L6/L10 contrast."*

**Issue.** "Directly comparable to the Othello L6/L10 contrast" is the
same Othello → chess depth-mapping issue in compact form. The user-
softened §16.5 text now says "shallow / mid / deep, illustrative not
prescribed"; this bullet still claims direct comparability with the
Othello L6/L10 axis.

**Suggested rewording.** "(new) Per-depth signal decay curve. Plot
ELO delta vs search depth for each evaluator. This is the most
informative single chart Phase 6 can produce — analogous in shape
(though not necessarily in depth values) to the Othello L6/L10
contrast."

---

#### `[F09]` STRONG — §16.7, "Phase 7 (learned weights) reframing", line 2608

> *"If Phase 6 confirms the depth-decay pattern for spectral evaluation
> in chess …"*

**Issue.** "Confirms" presupposes the depth-decay pattern is the
expected outcome. Given the cross-domain mapping is methodological
inheritance, the framing should be neutral — confirm vs refute vs
something-else are all live possibilities.

**Suggested rewording.** "If Phase 6 finds the depth-decay pattern
holds for spectral evaluation in chess, Phase 7's learned-weights
work has two paths: …"

---

#### `[F10]` STRONG — §16.8, item 1, line 2622

> *"Faithful sheaf bracket-classifier: +40% gain (`research/faithful_sheaf.py`;
> §2e.5–§2e.6 of the othello notebook). Replacing endpoint-only
> restriction maps with per-cell R1/R2/R3/R4 bracket-state classifier
> and projecting pending-flank counts through D_4 lifted D_4-A_1(s²)
> partial ρ from −0.319 → −0.447 at N=2587."*

**Issue.** This is fine *as a quotation of the Othello result*. But
the surrounding paragraph and the §16.8.5 conclusion ("the structural
ceiling depends on what observables you have access to") generalize
it across the chess/Othello boundary in a way that re-uses the +40%
number as if it predicted a chess outcome. The number is reported as
Othello data and then loaded into the chess-side reasoning.

**Suggested rewording.** Keep the Othello number as-is in §16.8.1
(it's a faithful quotation). Where §16.8.5 concludes "the structural
ceiling depends on what observables you have access to," add an
explicit hedge: "in Othello. Whether the same shape (richer features
+ learned coupling lift the ceiling) replays in chess is a Phase 7
empirical question, not a prediction."

---

#### `[F11]` STRONG — §16.8, item 2, line 2624

> *"Phase-operator reweighting chain: +114% cumulative gain … This is
> the most directly applicable result to chess-spectral's Phase 6
> design — the QM-expectation evaluator with learned `α_O` weights on
> the §15.2(4) Hermitian observables is structurally close to this
> construction. Treat it as the prior to beat."*

**Issue.** "Treat it as the prior to beat" elevates an Othello-side
fitted construction into a chess-side benchmark. The structural
similarity is real (Nelder-Mead-fit weights on entropy-difference
features ≈ learned α_O weights on Hermitian observables), but
"the prior to beat" frames the +114% Othello gain as if it were the
chess target. The cross-domain hop is exactly the user-flagged class
of overstrong claim.

**Suggested rewording.** "Phase-operator reweighting chain: +114%
cumulative gain (Othello). The structural analog for chess-spectral
Phase 7 is the QM-expectation evaluator with learned α_O weights on
the §15.2(4) Hermitian observables. The Othello gain doesn't predict
the chess gain (different game, different baseline, different feature
basis); use it as a methodology pointer (Nelder-Mead-fit on entropy-
diff features works well in this class of problem) rather than a
target number."

---

#### `[F12]` MEDIUM — §16.8.4, item 4, line 2677

> *"Three-regime channel decomposition. Phase 6's per-channel ablation
> should classify chess channels into the (monotone / trajectory-driven
> / turn-order-coupled) regimes."*

**Issue.** "Should classify chess channels" prescribes a
classification scheme inherited from Othello. The three regimes were
identified in Othello data; whether chess channels separate into the
same three regimes is empirically open.

**Suggested rewording.** "Three-regime channel decomposition. Phase 6's
per-channel ablation can test whether chess channels exhibit the same
(monotone / trajectory-driven / turn-order-coupled) regime structure
the Othello data showed. Treating the Othello categorization as a
hypothesis to test, not a prescriptive decomposition."

---

#### `[F13]` MEDIUM — §16.8.5, "Combined working hypothesis", item 1, line 2686

> *"Phase 6 ships naive linear spectral weights (analogous to zen-pike's
> Architecture A) and likely confirms the depth-decay pattern."*

**Issue.** Same prediction-from-Othello shape as `[F07]` and `[F09]`.
"Likely confirms" again presupposes the chess outcome will replay
the Othello pattern.

**Suggested rewording.** "Phase 6 ships naive linear spectral weights
(analogous to zen-pike's Architecture A); whether they replay the
Othello depth-decay or break the pattern (e.g., because chess's
material baseline is far weaker than Edax) is the load-bearing
empirical question."

---

#### `[F14]` STRONG — §16.8.5, "Combined working hypothesis", item 3, line 2688

> *"Validation target should be game outcomes, not Stockfish eval at
> fixed depth — Edax d=20 didn't bridge the perfect-play gap on
> Othello, and there's no reason Stockfish at any heuristic depth
> would do better on chess."*

**Issue.** "There's no reason Stockfish at any heuristic depth would
do better on chess" extrapolates the Othello/Edax finding to chess
without engaging the differences (Stockfish is a much-deeper search
engine than typical Edax leaves; chess-side game-theoretic structure
differs). The Othello finding (Edax d=20 ≠ perfect-play correlation
target) is a real result; the chess prediction it implies is much
weaker than the framing suggests.

**Suggested rewording.** "Validation target should preferentially be
game outcomes, not engine evals at fixed depth — Edax d=20 didn't
bridge the perfect-play gap on Othello, which suggests engine-eval-
as-truth has limitations even with deep heuristic search. Whether
Stockfish at any depth bridges the gap on chess is empirically
open; using game outcomes as primary truth and engine evals as a
regularizer is conservative."

---

#### `[F15]` STRONG — §17.6, "The line is bright", line 2818

> *"chess-spectral exposes capabilities; chess4D-OC chooses how to
> use them."*

**Issue.** Stylistically clean but rhetorically overstrong. There
isn't actually a bright line — `getDrawStatus()` taking
`has_legal_moves: bool` from the consumer (per §17.5 narrative) is
exactly the kind of capability/policy intermixing the slogan claims
isn't happening. The line is reasonably bright most places; saying
"bright" unconditionally papers over the gray edges.

**Suggested rewording.** "The intended split: chess-spectral exposes
capabilities; chess4D-OC chooses how to use them. Edge cases like
`getDrawStatus`'s `has_legal_moves` parameter (a capability that
takes a policy bit from the consumer) sit on the boundary — those
are documented per-method rather than hidden under the slogan."

---

#### `[F16]` STRONG — §18.2, line 2840

> *"The Phase 1 spectral-identity result + the Phase 3.5 phase-
> distinguishability result together establish that chess-spectral's
> QM extension is more than notation — the channels are an irreducibly
> quantum decomposition (irrep-typed eigenbasis of (Δ, B_4 commutant)
> per Pre-flight 3) AND moves act as channel-distinguishable unitaries
> (Probe 1)."*

**Issue.** "Establish that chess-spectral's QM extension is more than
notation" is doing a lot of work — Probe 1 showed 73.6% strong-
distinguishability on a specific 9,500-pair sample with the channel-
phase formulas in ADR-001. That's evidence the Aaronson-trap escape
valve is *open*, which is exactly how §18.1 phrases it. The §18.2
reframing pushes from "escape valve open" to "irreducibly quantum
decomposition," which is a much stronger claim (and "irreducibly
quantum" is a term of art with a specific meaning in QM literature
that doesn't quite line up).

**Suggested rewording.** "The Phase 1 spectral-identity result + the
Phase 3.5 phase-distinguishability result together show that chess-
spectral's QM extension is not a tautological re-notation — the
channels carry an irrep-typed decomposition (per Pre-flight 3) AND
moves act as channel-distinguishable unitaries with the ADR-001 phase
convention (Probe 1's 73.6% strong-distinguishability rate). Whether
this rises to 'irreducibly quantum content' in the technical sense is
a stronger claim we don't make; what we have shown is the Aaronson-
trap escape valve is open."

---

#### `[F17]` STRONG — §18.2, second paragraph, line 2842

> *"… it does close the door on the strongest version of the Aaronson
> critique: at minimum, our channel-as-PVM measurements distinguish
> moves, which is more than a basis-aligned PVM on basis-aligned
> states could ever do."*

**Issue.** "Closes the door on the strongest version of the Aaronson
critique" overstates what Probe 1 showed. Probe 1 showed channel-
distinct phases produce non-trivial inner-product overlaps between
post-move states; that's the Aaronson escape valve being *open* on
this specific construction, not "the strongest version of the
critique closed." Aaronson's critique survives all sorts of
post-hoc constructions; what we have is empirical evidence that
this particular construction doesn't reduce to it.

**Suggested rewording.** "… it shows the strongest version of the
Aaronson critique — that this is just classical permutations in QM
notation — does not apply to the ADR-001 channel-phase construction
on the Probe 1 sample. Whether weaker variants of the critique
survive (e.g., 'the channel-distinct phases don't carry chess-
relevant information') is the §16 / Phase 6 empirical question."

---

### `docs/chess-maths/chess_spectral_4d_notebook.md`

#### `[F18]` STRONG — qm_4d Pre-flight Findings → "Pre-flight 3" interpretation, line 775

> *"The 'engineering choice' of basis is a representation-theoretic
> theorem. Any B_4-equivariant function on Z_8^4 configurations
> decomposes naturally in the encoder's basis."*

**Issue.** Same as `[F02]` / `[F04]`. The encoder's basis being the
simultaneous eigenbasis of (Δ, B_4 commutant) was *verified at machine
precision*; the underlying decomposition theorem (for any finite-group
action on `L²` of a graph respecting the operator) is classical, not
a result of this work. Calling our verification "a representation-
theoretic theorem" elevates it.

**Suggested rewording.** "The encoder's choice of basis is verified
to realize the simultaneous eigenbasis of (Δ, B_4 commutant) at
machine precision, putting it in correspondence with the classical
representation-theoretic decomposition. Any B_4-equivariant function
on Z_8^4 configurations therefore decomposes naturally in this
basis."

---

#### `[F19]` MEDIUM — Phase 6 plan section, line 781 (lightly already softened)

The user already softened the "first 4D chess engine ever shipped"
language. The current text reads:

> *"… we don't have an exhaustive survey of prior 4D chess search
> implementations, so we make no 'first ever' claim."*

**Status.** Already softened — no further action. Recorded for
completeness.

---

### `docs/chess-maths/chess-spectral/docs/adr/qm_4d/ADR-001-phase-convention-for-unitary-moves.md`

#### `[F20]` STRONG — §3.2 "Aaronson escape", line 115

> *"A superposition input ψ spanning multiple channels accumulates
> different phase factors per channel, so `|<phi|U_move ψ>|^2` is no
> longer just the classical permutation overlap — interference
> arises."*

**Issue.** "Interference arises" is presented as a structural
consequence; Probe 1 retroactively showed this *empirically* (73.6%
strong distinguishability, 100% below-threshold), but at the time
ADR-001 was written this was a structural argument. Post-Probe-1, the
ADR claim survives empirically — but the wording still presents the
prediction as a guarantee. Probe 1's amendment record (PHASE_3_5_PROBE_RESULTS)
calls the result "PASS — ship as-is," which is correct for the
specific phase formulas in §3.1, but doesn't generalize to "any
ADR-001-shaped construction produces interference."

**Suggested rewording.** "A superposition input ψ spanning multiple
channels accumulates different phase factors per channel, so for
states with non-trivial channel support `|<phi|U_move ψ>|^2` will
generically differ from the classical permutation overlap (i.e.,
interference is structurally available). Whether the interference is
quantitatively meaningful for chess-relevant ψ states was tested in
Phase 3.5 Probe-1 (PASS at 73.6% strong distinguishability)."

---

#### `[F21]` MEDIUM — §3.3 "Why these specific phase values" (`pi/4`, `2pi/3`, etc.), lines 137–157

> *"The factor `pi/4` is chosen so a single-step move accumulates
> `pi/4` (smallest nonzero phase that survives to displacement = 8
> without wrapping). … FIB_SYM channels (cube roots of unity scaled
> by `d_path`): The three fiber-SVD directions span a 3D rank space;
> phases `2pi/3`, `4pi/3`, `2pi` encode the three irrep components
> as 3rd roots of unity."*

**Issue.** The §3.3 derivations are post-hoc rationalizations — the
phases are *design choices* that produce empirically distinguishable
moves, but the framing reads as if there's a unique principled
derivation. Section 5.4 (Option D variants) and the user's own
"Krawtchouk values rejected because opaque" reasoning shows the
choice is closer to "readable rationals that work" than "uniquely
principled."

**Suggested rewording.** Keep the table; reframe the prose as "These
specific values are design choices that satisfy the constraints in
§3.2 while staying readable; they are not uniquely determined by
representation theory. Krawtchouk-based variants (rejected in §5.4)
or other rational choices would also satisfy the constraints. The
load-bearing property is that channels accumulate *distinct* phases,
not that the specific values are canonical."

---

#### `[F22]` STRONG — §4.2 "What this forecloses", line 188

> *"No path-history dependence on the phase. The phase depends only
> on origin, destination, piece type, and channel — not on how the
> piece's ψ-amplitude got to `origin`. This is intentional (keeps
> `U_move` Markov on the QM state) but rules out 'true' path-integral
> phase that integrates over all paths the piece *might* have taken."*

**Issue.** "True path-integral phase" presents Berry-phase-from-
path-integration as the canonical version, when in fact path
integrals in QM live on continuous configuration spaces; on a
discrete graph there is no "true" path integral, only various
discrete approximations (Berry-phase analogs, sum-over-paths on the
graph, etc.). The framing imports continuum-QM language unhelpfully.

**Suggested rewording.** "No path-history dependence on the phase.
The phase depends only on origin, destination, piece type, and
channel — not on how the piece's ψ-amplitude reached `origin`. On a
discrete graph this is the simplest phase convention; richer
alternatives (graph-Berry-phase along the path, sum-over-paths on
the graph) are documented in Option B (§5.2) and deferred to v1.7+."

---

### `docs/chess-maths/chess-spectral/docs/adr/qm_4d/ADR-002-time-evolution-semantics.md`

#### `[F23]` MEDIUM — §4.1 "Captures collapse to a single rescale", line 217

> *"A reviewer asking 'how does QM chess handle captures?' gets a
> one-line answer: 'we project and renormalize — the textbook Born-
> rule operation.'"*

**Issue.** Captures aren't textbook Born-rule projections in any
standard sense — Born-rule projection is "measure observable, collapse
to eigenspace of measured eigenvalue, renormalize." Capture-as-rescale
is a *partial-isometry composed with renormalization*, which is
related but not the textbook Born picture. Calling it "the textbook
Born-rule operation" misnames it for rhetorical convenience.

**Suggested rewording.** "Captures collapse to a single rescale of ψ.
The non-unitary structure is contained in N — a partial-isometry
followed by norm restoration. This is structurally similar to a
Born-rule measurement projection (project + renormalize) but is
specifically the projection-then-renormalize step of a measurement
without the eigenvalue-sampling step."

---

### `docs/chess-maths/chess-spectral/docs/adr/qm_4d/ADR-003-per-channel-move-transformation.md`

#### `[F24]` STRONG — §3.1 channel 0 "Verification", line 132

> *"`Pi_0 @ encode_4d_A1(pos_pre) = encode_4d_A1(pos_post)` exactly,
> provided sig values for non-`o`, non-`d` squares are unchanged."*

**Status.** This claim was *empirically falsified* by PR #76 and
explicitly amended by `ADR-003-AMENDMENT-orbit-restriction.md`. The
amendment file exists and PHASE_3_5_PROBE_RESULTS.md flags the
amendment. **However, the original §3.1 prose still reads as written
— a downstream reader landing on §3.1 first will read a verification
claim that is no longer supported.** The amendment file fixes this
in narrative but doesn't update the §3.1 text itself.

**Suggested action.** Add a 2-line "Amended" callout box at the top
of §3.1 pointing at the amendment file ("This claim is restricted to
same-orbit non-capture moves per ADR-003 amendment; cross-orbit moves
fall back to measurement-only re-encode"). The amendment file
already contains the precise wording.

---

#### `[F25]` MEDIUM — §4.2 "What this forecloses", line 363

> *"Full-strict-QM Track B in v1.5. Channels 5-7 and 10 are not
> strictly evolved unitarily."*

**Issue.** The post-Phase-3.5 picture is more restrictive than the
ADR's original framing: A_1, STD4_X/Y/Z/W are now *only same-orbit*
strict-unitary (per the AMENDMENT); FIB_SYM are measurement-only;
FD_DIAG is rank-1 + renorm. So "Channels 5-7 and 10 are not strictly
evolved" understates the actual scope-narrowing. The "Aggregate v1.5
unitarity" table in §3 is also pre-amendment.

**Suggested rewording.** Add a "Post-Phase-3.5 / post-PR-#76 status"
row that names the actual v1.5 strict-unitary tier (A_1 same-orbit;
STD4 same-orbit; FA_PAWN axis-flip non-capture); FIB_SYM and FD_DIAG
were already best-effort; cross-orbit / capture cases route through
measurement-only. The ADR's original analysis remains valid as the
design rationale; the table should explicitly note "amended — see
PHASE_3_5_PROBE_RESULTS and ADR-003-AMENDMENT for current status."

---

### `docs/chess-maths/chess-spectral/docs/adr/qm_4d/ADR-004-z2-superselection-structure.md`

#### `[F26]` STRONG — §3.4, line 162

> *"This means `U_move @ J_op = −J_op @ U_move` (`U_move` *anti-
> commutes* with `J_op`, not commutes). Equivalently: `U_move` is a
> Z_2-graded operator of *odd parity* (it changes sector). … This is
> a strong constraint on `U_move`. Verification: for each of the
> strict-unitary channel constructions in ADR-003, the per-channel
> `Pi_c` must satisfy `Pi_c @ J_c = −J_c @ Pi_c` …"*

**Status.** This claim was *empirically falsified* by Phase 3.5
Probe-4 (anti-commutator residual = 128, target 1e-10 — fails by 30
orders of magnitude). PHASE_3_5_PROBE_RESULTS.md amends this section
to "the parity sector change is mediated by `state_to_psi`'s sign
multiplier; per-channel anti-commutation is not required." The probe
results file says §3.4 should be replaced.

**However, the §3.4 text still reads as written.** A reader landing
on ADR-004 directly will read a constraint that is empirically
known to fail. As with `[F24]`, the amendment lives in a separate
file but doesn't update the original ADR text.

**Suggested action.** Add the same "Amended — see
PHASE_3_5_PROBE_RESULTS.md" callout at the top of §3.4 with the
specific replacement wording from the probe-results file.

---

#### `[F27]` WEAK — §4.1 "Pre-flight 2 commutation cross-check is trivial", line 257

> *"Pre-flight 2 commutation cross-check is trivial. The 5
> `H_piece_4` observables commute with `J_op` by construction (graph-
> adjacency matrices of B_4-symmetric reach graphs commute with B_4-
> central elements). The cross-check is a closed-form test, not a
> deep theorem."*

**Issue.** Minor — "by construction" is correct *if* the lift uses
B_4-symmetric reach predicates, which it does, but the test is still
worth running (and the section says ~80 LOC of test). "Trivial" is
true given the construction; calling out *why* it's trivial in a
sentence rather than asserting it would be cleaner.

**Suggested rewording.** "Pre-flight 2's commutation cross-check is
trivial *given the construction* (graph-adjacency matrices of
B_4-symmetric reach graphs automatically commute with B_4-central
elements), but the test is still asserted at construction time as
an invariant."

---

### `docs/chess-maths/chess-spectral/docs/adr/qm_4d/ADR-005-pawn-pseudo-hermitian-eta-metric.md`

#### `[F28]` STRONG — §3.3.1 "M_pawn_w_white^T = M_pawn_w_black", lines 199–200

> *"`M_pawn_w_white^T = M_pawn_w_black` (push directions reverse)"*

**Status.** Phase 3.5 Probe-3 found this holds *only in the
no-double-push variant* (residual 0.0); the full operator including
double-push has residual 32.0. PHASE_3_5_PROBE_RESULTS.md amends to
the M_single + M_double decomposition. Same shape as `[F24]` and
`[F26]`: the original ADR text still asserts the un-amended identity.

**Suggested action.** Add an "Amended" callout at the top of §3.3.1
with the M_single / M_double decomposition wording from the probe-
results file.

---

#### `[F29]` MEDIUM — §5.5 "which η operator to use" / §3.3 "the unique η", lines 216, 451

> *"The η operator that makes `M_pawn_w_white` pseudo-Hermitian is:
> `η_pawn_w := P_w` … Within Option δ, the choice of η is constrained
> by the directed-push structure. The §3.3 derivation `η = P_w` (axis
> parity flip) is the unique η-operator candidate that …"*

**Issue.** "The unique η-operator candidate" overclaims — uniqueness
is up to scale, *and* up to the no-double-push idealization. Probe-3
showed `J_op` also satisfies the no-double-push pseudo-Hermiticity at
zero residual (per the findings table). So η is not unique even
among the candidates the probe checked.

**Suggested rewording.** "Within Option δ, P_w is the natural η-
operator candidate constrained by the directed-push structure (axis
parity ↔ flip the pawn's push direction). Probe-3 showed both `P_w`
and `J_op` satisfy the no-double-push pseudo-Hermiticity at zero
residual; we pick `P_w` for its physical interpretability. Other
non-trivial candidates (e.g., scaled variants) exist by the up-to-
positive-scalar non-uniqueness in the pseudo-Hermitian framework."

---

### `docs/chess-maths/chess-spectral/python/research/spectral_identity_4d_findings.md`

#### `[F30]` STRONG — "The encoder's tensor-DCT basis is canonical", line 111

> *"The encoder's tensor-DCT basis `e_i (x) e_j (x) e_k (x) e_l` is
> _canonical_: it diagonalizes `Delta` (Kronecker-sum eigenvalues) AND
> every P_lambda commutes with every `pi(g)` (B_4-action). The choice
> of basis _within_ each multidimensional eigenspace is therefore not
> arbitrary engineering — it is determined by the simultaneous spectral
> decomposition of the operator algebra `< Delta, pi(B_4) >`."*

**Issue.** Same shape as `[F02]` / `[F04]` / `[F18]`. The basis is
canonical *up to a CSCO completion* — within each multidim eigenspace
the simultaneous-eigenbasis-of-Δ-and-B_4-commutant constraint leaves
freedom (there's a finite group acting; pick the irrep-decomposition
basis vs other bases). The paragraph correctly says "sub-decomposition
*within* a B_4-stable subspace, not a re-choice of basis," but the
"canonical" framing rounds over the within-eigenspace freedom.

**Suggested rewording.** "The encoder's tensor-DCT basis
`e_i ⊗ e_j ⊗ e_k ⊗ e_l` simultaneously diagonalizes Δ and commutes
with all pi(g) — the necessary structure for any B_4-equivariant
analysis. Within each multidimensional eigenspace, further refinement
into B_4-irrep components is a choice; the simultaneous-eigenbasis
constraint fixes the eigenspace decomposition but not the basis
within. The 'canonical' label refers to the eigenspace-level
property, not to a unique within-eigenspace choice."

---

### `docs/chess-maths/chess-spectral/python/research/track_b_pawn_pt_symmetry_findings.md`

#### `[F31]` MEDIUM — Recommendation §, line 69

> *"The spectrum is fully real because M is nilpotent (all eigenvalues
> = 0); pawn pushes are non-iterable on a finite board. ADR-005's
> PT-realness gate is trivially satisfied."*

**Issue.** "Trivially satisfied" — true in the literal sense (zero
spectrum is real), but the framing reads as if the gate was passed
*meaningfully*. A nilpotent operator with all-zero eigenvalues
satisfies *any* spectrum-realness gate trivially; the gate doesn't
distinguish meaningful PT-symmetry from triviality. The PT-symmetry
question for pawns is essentially undetermined by the eigenvalue test.

**Suggested rewording.** "The spectrum is fully real because M is
nilpotent (all eigenvalues = 0; pawn pushes don't iterate on a finite
board). ADR-005's PT-realness gate is satisfied trivially — but
because the eigenvalues are all zero, the gate doesn't actually
distinguish a meaningfully PT-symmetric operator from a generically
nilpotent one. The pseudo-Hermiticity check (which probes the
operator's structure beyond its spectrum) is the more discriminating
test, and it's what the M_single / M_double decomposition resolves."

---

### `docs/chess-maths/chess-spectral/docs/adr/qm_4d/ADR-003-AMENDMENT-orbit-restriction.md`

#### `[F32]` MEDIUM — §3.3, "Predicted to fail cross-orbit by the same mechanism", line 96

> *"STD4_X/Y/Z/W (B3a): `Pi_a = D_a @ swap @ D_a^{-1}` (rescaled swap;
> ADR-003 §3.1 channels 1-4). The rescaling is diagonal and commutes
> with the orbit projector iff the swap does — i.e., the same orbit
> dichotomy applies. Predicted to fail cross-orbit by the same
> mechanism; B3a's tests will quantify."*

**Issue.** "Predicted to fail cross-orbit by the same mechanism" is
a structural prediction that *was subsequently verified* in B3a (per
the dynamics module status post-B5). The wording is honest at the
time of writing — "to verify in B3a" — but a downstream reader after
B5 should be told the prediction was confirmed. As with `[F24]`/`[F26]`/`[F28]`
the issue is that the doc isn't updated post-empirical-result, so
the "prediction" wording survives past when it became "confirmed."

**Suggested action.** Add a post-B3a status update: "Post-B3a: this
prediction was confirmed empirically; STD4_X/Y/Z/W exhibit the same
same-orbit / cross-orbit dichotomy as A_1."

---

## Internal-consistency check (cross-doc contradictions)

Walking the docs in parallel surfaced these:

#### `[F33]` STRONG — Channel count consistency

The 4D notebook line 7 (architecture summary), 2D notebook §15.2(3),
ADR-003 §3, ADR-001 §3.1 (table), and `qm_4d_bridge.py` _SHIPPED_CHANNELS
all consistently report **11 channels**. ✅ No drift.

The 2D notebook §16.1 item 2 says "11 channels (4D) or 10 channels
(2D)" — that's the *2D vs 4D* difference (2D ships the 10-channel
encoder, 4D ships 11). Cross-checked against the python README's
2D vs 4D split: ✅ consistent. No drift.

(Recorded as `[F33]` because the user explicitly asked about this
class of contradiction; nothing to fix, but the audit checked.)

---

#### `[F34]` STRONG — ADR text vs amendment file divergence

Three ADRs (`ADR-003 §3.1`, `ADR-004 §3.4`, `ADR-005 §3.3.1`) carry
text that was empirically falsified by Phase 3.5 probes (see `[F24]`,
`[F26]`, `[F28]`). The amendments live in separate documents
(`PHASE_3_5_PROBE_RESULTS.md`, `ADR-003-AMENDMENT-orbit-restriction.md`)
that explicitly note the original text "is preserved as the design
record at the time of the decision." This is a deliberate convention
per the README ("ADRs themselves are preserved … this doc captures
the empirical reality").

**However**, that convention only works if every ADR has a forward-
pointing callout to its amendment. Currently:
- `ADR-003-AMENDMENT-orbit-restriction.md` is forward-linked from
  `README.md` and `ADR-003-per-channel-move-transformation.md` is
  *not* updated to point to its amendment.
- `ADR-004 §3.4` has no callout pointing at the Probe 4 amendment.
- `ADR-005 §3.3.1` has no callout pointing at the Probe 3 amendment.

**Suggested action (cross-cutting).** Add a 2-line "Amended — see
[PHASE_3_5_PROBE_RESULTS.md](PHASE_3_5_PROBE_RESULTS.md)" callout at
the top of each amended section. This preserves the "ADR is the
historical record" convention while giving downstream readers a
forward link to current status. The README.md already has the table;
each ADR just needs the section-level pointer.

#### `[F35]` MEDIUM — The "qm_4d.py" module's H_piece spectrum claims

Pre-flight 2 quoted spectrum bounds for rook ([-4, 28] integer) but
also notes "non-rook pieces have larger non-integer spectra." 4D
notebook lines 749–754 give the empirical full sweep. ADR-004 §3.3
asserts "real-symmetric matrices have real spectrum (Pre-flight 2
already confirmed)" which is true, but elsewhere (`[F27]`'s context)
the claim "trivial" is overstated.

No contradiction — but the per-piece bounds are documented in *three*
places (4D notebook qm_4d Pre-flight section; phase_operators_4d
audit; 2D notebook §15.2(4)) and any future per-piece spectrum
adjustment must update all three. Not an error today; flagged for
future hygiene.

---

## Summary

**Total findings:** 35 (33 substantive + 2 internal-consistency
checks).

| Severity | Count |
|----------|-------|
| STRONG   | 18    |
| MEDIUM   | 12    |
| WEAK     | 1     |
| Already softened (recorded for completeness) | 1 (F19) |
| Internal consistency / no-drift confirmation | 1 (F33) |
| Cross-cutting hygiene (ADR ↔ amendment) | 1 (F34) |
| Future-hygiene only | 1 (F35) |

**Top 5 highest-priority items** (most egregious overclaims):

1. **`[F02]` / `[F04]` / `[F18]` / `[F30]` — "encoder basis is the
   theorem" overclaim.** Four restatements across the 2D notebook
   (§15.2, §15.6), 4D notebook (Pre-flight 3 interpretation), and
   spectral_identity_4d_findings.md. Numerical verification is
   represented as a self-supplied theorem in each restatement.
   Single fix recommended: pick one canonical phrasing
   ("numerically verified to realize the classical CSCO basis") and
   use it consistently in all four locations.

2. **`[F24]` / `[F26]` / `[F28]` — three ADRs carry empirically-
   falsified text without in-section amendment callouts.** ADR-003 §3.1's
   verification claim, ADR-004 §3.4's anti-commutation requirement,
   and ADR-005 §3.3.1's transpose identity are all amended in
   external files but the original ADR sections remain untouched.
   Risk: a reader landing on ADR-004 §3.4 reads a constraint that
   is known to fail. The cross-cutting fix is `[F34]`.

3. **`[F03]` — §15.6's "0% / 70% / 95% novel" rhetorical
   percentages.** User explicitly flagged this in the audit prompt;
   the percentages are not sourced.

4. **`[F11]` / `[F14]` / `[F09]` / `[F13]` — Othello → chess
   extrapolation overclaims.** Even after the user's softening of
   §16.5 / §16.7 item 1, downstream items in §16.7, §16.8.4, and
   §16.8.5 still translate Othello numbers into chess predictions
   ("the prior to beat", "no reason Stockfish would do better",
   "likely confirms the depth-decay pattern").

5. **`[F01]` / `[F05]` / `[F06]` — categorical "no PyPI package /
   no shipping toolkit / community needs this" claims** without
   exhaustive surveys. Three near-restatements; consistent fix is
   to soften "doesn't exist" → "we are not aware of."

**Aspirational-vs-accomplishment items (less urgent but worth
addressing):** `[F15]` (the bright-line rhetoric), `[F17]`
(closing the door on Aaronson), `[F23]` (textbook Born-rule misnaming).

**Out-of-section text adjustments:** `[F25]`, `[F32]` — the two
predict-then-verify spans where the doc never circled back to mark
the prediction as verified after it landed empirically.

---

## Internal inconsistencies spotted

- **F33 (no drift):** Channel count is consistent across docs and
  code at 11 (4D) / 10 (2D).
- **F34 (real divergence):** ADR text vs amendment file. Three ADR
  sections carry text that was empirically falsified, but the
  amendments live in separate files without in-section forward
  links. This is the only structural inconsistency in the audited
  surface, and the fix is mechanical (add 2-line callouts).
- **F35 (non-issue today):** Per-piece spectrum bounds duplicated in
  three places; no drift now, but future updates need to keep all
  three in sync.

No "all 11 channels ship vs all 10 channels ship" type contradiction
was found — the bridge code, ADR-001 / ADR-003 channel tables, and
both notebooks agree on 11 channels for 4D throughout.
