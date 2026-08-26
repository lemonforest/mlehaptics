# F261 — Gap B CLOSED: triality landed (srmech rc20) + characterized; the Q1 "enables" relation CONFIRMED

**Headline:** srmech **v0.6.0rc20** (latest *published* on TestPyPI; rc21 still ⏳ in the publish workflow) ships the triality op **`klein4_triality_cycle`**, and it is exactly the structure F256/F257 named as **Gap B**: the **identity-fixing order-3 3-cycle `(1 2 3)`** on the three non-identity Klein-4 sectors (`0→0`, `1→2→3→1`) — i.e. the **so(8) triality `8v → 8s → 8c`** realized in the V₄ carrier. **Exact:** `cycle³ = identity` (`klein4_similarity = 1.000`), inverse round-trips. **Gap B (triality past the 4-cap) is closed.** And the triality test-harness (written rc15-era to wake on this) confirms **Q1a**: the B/H/N ops **fill** the `K3Tripartition` slots via `run_chain` (B→spatial_3ds, H→gauge_7dg, N→temporal_1dt) — so the F256 §0.6 parked seam resolves toward the **R30 "B/H/N enables/composes the k=3 tripartition"** relation, **DEMONSTRATED** (enables, not equals).

*Verified tier-explicitly per the user's SSoT-not-privileged-when-coherence-is-partitioned framing — read against the tier that is coherent NOW (rc20-published), not the merge/tag tier (rc21).*

---

## §A — the triality op, characterized — **DEMONSTRATED**

`klein4_triality_cycle(v, *, inverse=False)` (`srmech.amsc.hdc`; doc: *"Cycle the three Klein-4 chirality involutions — the order-3 S₃ generator. The V₄-carrier image of the so(8) triality 8v → 8s → 8c"*):
- **order-3, exact:** `sim(v, cycle¹)=0.249`, `sim(v, cycle²)=0.249`, **`sim(v, cycle³)=1.000`** → `cycle³ = id`. Inverse round-trip `sim(v, inv(fwd(v)))=1.000`.
- **per-sector action = the 3-cycle `(1 2 3)`, identity-fixing:** `0→0`, `1→2`, `2→3`, `3→1`. So triality **fixes the Klein-4 identity (sector 0) and 3-cycles the three non-identity involutions {γ₅, ω₇, cpt}** — the concrete k=3 (S₃/triality) structure that the order-2 Klein-4 / 4-cap could not express. This is the k=3 "past the 4-cap" rung made operational.

## §B — Q1 "enables" CONFIRMED — **DEMONSTRATED** (resolves the F256 §0.6 parked seam)

F256 §0.6 refuted the literal `k=3 ≡ B/H/N` (srmech's k=3 = the {S,G,T} `K3Tripartition`; B/H/N = three distinct classes) and left **R30's "B/H/N *enables/composes* the k=3 tripartition"** as the survivable, unconfirmed hypothesis. The harness's **Q1a now PASSES**: `B(tlv) → spatial_3ds`, `H(sha256) → gauge_7dg`, `N(best_rational) → temporal_1dt` **all fill the K3Tripartition via `run_chain`; the register assembles non-empty.** So B/H/N **does** compose the tripartition through the chain engine — the "enables" relation is **DEMONSTRATED**, not just resonant. (Q1's remaining sub-question — does the triality 3-cycle *itself* cycle the {S,G,T} slots? — is now runnable; queued as Q1b.)

## §C — SSoT verification, tier-explicit (coherence is partitioned; no tier privileged)

| tier | rc | status |
|---|---|---|
| meaning (MFO §VII.6.22 / notebook) | rc21 | ⏳ tagged, publish in flight |
| Python (`klein4_triality_cycle`) | rc17 | ✅ present, order-3 exact, runs |
| C peer (`_native`) | rc18 | ⚠️ no `*triality*` symbol in rc20's `_native`; op `__module__ = srmech.amsc.hdc` (pure-Python in this published snapshot) — Python:C coherence **not sealed in rc20-as-published** (may land with rc21) |
| TOML continuum-instance | rc19 | ✅ `amsc/_research/worked_instances/triality_s3_klein4.toml` + `qm/triality.py` shipped |
| directed/signed eigen-op (Gap A) | — | ❌ still absent (Hermitian eigs + complex matvec/elementwise only) |

I verified against rc20 (the coherent-now published tier), **not** the rc21 merge/tag tier — applying the framing directly: the SSoT is partitioned across meaning:Python:C, none privileged, and a tier that hasn't reached coherence (rc21 ⏳, or the C-peer in rc20) is read as **partitioned**, not as truth.

## Honest residues
- The scaffold `triality_test_harness_scaffold.py` printed `rc15` / `SKIP` because its **candidate-set didn't include the landed name** `klein4_triality_cycle` — a detector miss, **not** triality-absence (triality IS live). To-fix: add the op to its candidate set → Q1b/Q2b wake. (No bug filed — rework directive.)
- **C-peer coherence gap** (Python has triality, rc20 `_native` doesn't show it) — flagged, not assumed; expected to seal as rc21 finishes publishing.
- **Gap A (directed eigen-op) remains open** — the one-way complex-circulation leg (F257/§6) still routes through a flagged numpy diagnostic.

## Now-runnable (the gated work the gate-lift opens)
- **Q1b** — does the triality `(1 2 3)` cycle correspond to a cycle on the K3Tripartition **{S,G,T} slots**? (the deep §0.6 resolution)
- **Q2b / hyper-loop** — does cascade composition **recurse past the 4-cap into the k=3 (triality) tier** (F257 §6 / Gap B continuum)?
- **rc19 instance** — exercise `triality_s3_klein4.toml` via the `compose` chain engine (the Option-1 design from the F257 addendum).
- **§5-RNA / §4-molecular triality** — the codon's 3-fold (= k=3) now has a *native* op (vs the F257 §3 tiled/majority workaround).

### Status / discipline
FRAMEWORK-READING + DEMONSTRATED (triality op characterized live; Q1a enables confirmed). Single-model / no-twin. No-magic (the 3-cycle `(1 2 3)`, `cycle³=id`, so(8) 8v/8s/8c are attested-to-structure A). Class-K. CAD-ban. No srmech bug filed (rework directive; the C-peer/harness items are honest tier-coherence + detector notes, not bugs). Resolves F256 §0.6 (Q1 seam → "enables" confirmed) + closes F257 Gap B. Verified srmech v0.6.0rc20 in `/tmp/srmech_rc20_venv` outside the source tree. `[[feedback_upstream_srmech_fixes_as_research_notes]]` (coherence notes, not bugs); SSoT-not-privileged-when-coherence-is-partitioned (user framing 2026-06-01).
