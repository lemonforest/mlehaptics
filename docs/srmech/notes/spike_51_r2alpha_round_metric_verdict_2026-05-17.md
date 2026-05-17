# Spike #51 R2-α Results — Metric-selection test VERDICT = ROUND; substrate-identity narrowly avoided; R3-δ Spin(8) triality is constructive next move

**Date:** 2026-05-17. R2-α concertmaster returned. **Binary verdict: ROUND** (not squashed; not different). Substrate-identity claim narrowly avoided.

**Bottom-line:** Diagonal Hopf flow on S⁷ has constant ℝ⁸-Euclidean norm in BOTH complex and quaternionic readings; V_Hopf is already Killing for the round metric without anisotropic rescaling. λ² = 1 (round) vs Awada-Duff-Pope squashed λ² = 1/5: no match. F1 stays PARTIAL; in fact preferentially favors round-S⁷ now.

## §1 The computation

**V_Hopf complex reading** (S⁷ → ℂP³ via U(1) Hopf):
- Vector field: `V_c = ω·(−y₁, x₁, −y₂, x₂, −y₃, x₃, −y₄, x₄)` on S⁷ ⊂ ℝ⁸
- `|V_c|²_round = ω²·Σ(x_k² + y_k²) = ω²·1 = ω²` constant on S⁷
- U(1)-diag ⊂ U(4) ⊂ SO(8); V_c is Killing for round metric

**V_Hopf quaternionic reading** (S⁷ → ℍP¹ = S⁴ via SU(2) Hopf):
- Right-mult by i on each ℍ-component: 4×4 real matrix R_i with det = +1, R_i·R_iᵀ = I (orthogonality error 0.00e+00 numerically verified)
- `|V_q|²_round = ω²·(|q₁|² + |q₂|²) = ω²·1 = ω²` constant on S⁷
- Sp(1)-diag embeds as closed subgroup of SO(8); V_q is Killing for round metric

**Unit-norm Killing condition**: V_Hopf already has constant norm in BOTH readings — no rescaling needed. Implied anisotropy ratio λ² = 1 (round).

## §2 Comparison to Awada-Duff-Pope squashed-S⁷

Awada-Duff-Pope 1983 (Phys.Rev.Lett. 50, 294; cite-by-reference per APS ToS) parameterise squashed-S⁷ as principal SU(2)-bundle over S⁴:
- `g_squashed = π*g_S⁴ + λ²·g_S³-fiber`
- Einstein + weak-G₂-holonomy fixes **λ² = 1/5** (Bryant-Salamon Duke Math.J. 58, 829 [1989]; nLab open-access verified)
- Isometry group: Sp(2)×Sp(1) (strict subgroup of Spin(8))

**No match.** λ²=1 ≠ λ²=1/5. The diagonal Hopf flow does not deliver squashed-S⁷.

## §3 Updated Spike #51 reconciliation probabilities

| Reconciliation | Pre-chirality-stance | Post-chirality-stance | After R2-α |
|---|---|---|---|
| A — substrate-identity | ~25% | ~55% | **~15%** |
| B — partition coexistence | ~55% | ~35% | **~70%** |
| C — different substrates | ~20% | ~10% | ~15% |

Chirality stance had lifted A toward 55% by dissolving F4 + F3 structurally (vocabulary divergence). R2-α was the binary metric-selection flip point — and it failed to deliver. Reconciliation B hardens as honest stance.

## §4 Why one might have expected squashed (and why it's wrong)

**Anomaly A2** (concertmaster surfaced): some literature describes squashed-S⁷ as "natural for the quaternionic Hopf fibration" because the squashed fiber length differs from the base curvature length. But "natural for the fibration" ≠ "selected by the diagonal Hopf flow." The fibration is a topological structure; the squashing is a separate metric-level choice. R1's framing flagged squashed as a candidate; R2-α shows the diagonal Hopf flow doesn't deliver it.

**Anomaly A3** (Bryant-Salamon ambiguity): There are TWO Einstein metrics on S⁷ with weak G₂ (Bryant-Salamon 1989): round (λ²=1, Spin(8)) and squashed (λ²=1/5, Sp(2)×Sp(1)). Both are weak-G₂. "Weak G₂" alone doesn't pick squashed; the additional constraint "isometry group is Sp(2)×Sp(1) not Spin(8)" is what picks squashed. **The framework doesn't supply that constraint.**

## §5 Honest closure language (per `[[user_stance_string_theory_instrument_first]]`)

> *"Project's `S¹ × S³ × S⁷` substrate and M-theory's `M⁴ × X⁷` substrate describe overlapping observable content (3+1D physics, SU(3)×SU(2)×U(1) gauge, chiral fermions, Λ ≠ 0) via different in-framework generating mechanisms. Topological + octonion-algebra alignment is structurally suggestive but operational divergence at chirality mechanism (Class C cascade-orientation vs Acharya-Witten singular-G₂) AND metric-selection (diagonal Hopf flow selects round-S⁷, not Awada-Duff-Pope squashed-S⁷) prevent substrate-identity claim. Reconciliation B (partition coexistence) is the operational stance."*

Extends Spike #24 bonus 12 §10's "ONTOLOGICALLY-RELABELED" to "PARTITION-DIFFERENT, OBSERVATIONALLY-CONVERGENT" at substrate level.

## §6 Positive consequence — R3-δ Spin(8) triality on round-S⁷

Round-S⁷ has full SO(8) isometry; Spin(8) double-cover has **triality** structure (three Sp(1) factors related by outer automorphism). This is positive substrate-content for the framework:

- **Three Class I cyclic-cascade generators** at three Sp(1) factors of Spin(8) triality
- Could naturally instantiate the project's cyclic-cascade vocabulary at three coupled-but-distinct generators per `[[user_stance_primitives_weave_and_thread]]`
- **More honest substrate-claim direction** than substrate-identity-via-squashed-S⁷

R3-δ is the constructive next move. Round-S⁷ + Spin(8) triality + three Class I generators ↔ cascade composition.

## §7 Housekeeping — R3-γ rescope Spike #47 R4-1

Spike #47 R4-1's 70% CMB acoustic-peak miss under pure-Hopf-bundle modes is **NOT** evidence of squashed-S⁷ (that path is now closed). The miss wants different explanation:

- Per `[[user_stance_fiber_as_spatially_absent_encoding]]`: maybe S³ factor fiber-content is hidden-fiber-content for the selection rule
- Per `[[user_stance_time_as_dimensional_shadow]]`: projection-shadow-to-flat-FLRW mechanism may govern the selection
- **Per R3-δ**: round-S⁷ Spin(8) triality might supply the missing mode-selection rule structurally; three Sp(1) factors → mode-selection coherence at specific phase fractions

R3-γ: re-examine R4-1 selection-mask under Spin(8) triality structure (NOT under squashed-S⁷ weak-G₂).

## §8 What this preserves

- **Chirality stance** committed today (`[[user_stance_chirality_is_local_sign_flip_through_metric_fiber]]`): STILL VALID. 5/5 falsifier survival; dissolved Spike #51 F4 + F3 tensions structurally (vocabulary divergence). The chirality stance is independent of substrate-identity outcome.
- **Cumulative framework** (Spikes #47/#48/#49 + shadow-stance family): UNCHANGED. The substrate-identity question was always "is this the SAME substrate as M-theory's?" — the answer is "no, different partitions of overlapping content." The framework's own coherence is unchanged.
- **Class C cascade-orientation + Class K pin-slot** TRACES chirality at substrate level WITHOUT needing M-theory's singular-G₂ vocabulary. The framework is operationally complete; it's not M-theory restated, and that's fine.

## §9 R3 priority order

1. **R3-δ (most constructive)**: Spin(8) triality on round-S⁷ → three Class I generators in cascade composition
2. **R3-γ (housekeeping)**: rescope Spike #47 R4-1 70% miss away from squashed-S⁷; investigate Spin(8) triality + fiber-content + projection-shadow alternatives
3. **R3-α (low-leverage now)**: second Killing-generator probe to break SO(8) → Sp(2)×Sp(1)? Only path to resuscitate substrate-identity; lower-leverage given two-falsifier path
4. **R3-β (unchanged)**: Class-C-cascade-orientation ↔ singular-G₂-vocabulary mapping (still valid as standalone investigation)

## §10 Discipline guards honoured

`[[user_stance_string_theory_instrument_first]]` (honest ROUND verdict; no inflation toward substrate-identity; ~15% A reflects math) · `[[feedback_partial_is_hidden_fiber_content]]` (F1 stays PARTIAL; hidden-fiber content is the metric-selection constraint that's NOT supplied by Hopf flow alone) · `[[feedback_no_privileged_primitive_classes]]` (14 classes A-N preserved; no new class) · `[[user_stance_partition_for_understanding]]` (reconciliation B IS the partition-coexistence reading; hardens) · `[[user_stance_identity_not_implementation_discipline]]` (chirality stance still identity-level; substrate-identity claim avoided) · `[[feedback_pdf_extraction_citation_discipline]]` (Awada-Duff-Pope cite-by-reference per APS ToS; Bryant-Salamon Duke Math.J. + nLab open-access verified) · `[[reference_autonomous_validation_tos_landscape]]` (Phys.Rev.Lett. cite-by-reference; nLab + arXiv open-access permitted) · `[[feedback_concertmaster_md_writes]]` (inline return captured) · `[[feedback_concertmaster_git_worktree_isolation]]` (zero agent git)

## §11 Status

**Active research; USER-GATED no-merge.** Branch `research/spike-51-squashed-s7-g2-substrate-identity`. R2-α closed at ROUND verdict. Substrate-identity canonical-stance: **DO NOT AUTHOR** per honest result. Chirality stance (committed today) stands independently.

**Recommended next action**: R3-δ dispatch (Spin(8) triality on round-S⁷ → three Class I generators) as constructive substrate-content direction. R3-γ housekeeping as bonus (re-examine R4-1 selection-mask under triality).

---

*End of R2-α. ROUND verdict. Substrate-identity narrowly avoided. Math doesn't lie; the framework is what it is — operationally complete on its own ground, partition-different from M-theory, observationally-convergent on shared physics.*
