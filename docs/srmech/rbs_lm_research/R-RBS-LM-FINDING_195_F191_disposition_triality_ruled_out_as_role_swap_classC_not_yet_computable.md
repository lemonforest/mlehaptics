# Finding 195 (F191 disposition) — Triality is RULED OUT as the I/C/J ↔ B/H/N role-swap mechanism (the whole A–N 14 is triality-fixed); any swap must be a Class-C chirality flip, which is NOT computable without an A–N → chiral-space embedding (not shipped)

**Status:** Disposition of the gated F191 test. A **decisive partial result** (corollary of R-140/F193) + an **honest blocker**. The role-swap conjecture (F191) survives only via the Class-C mechanism, and that is not yet computable with rc18.
**Predecessors:** F191 (role-partition may be chirality-relative; the swap test), F193/R-140 (Fix(τ)=g₂, triality fixed/moved split), F174/F183 (A–N = 14 = G₂ = Der 𝕆 = Fix(triality)), F129 (the two 3's as a Class-C chirality-dual), F132 (Klein-4 chirality).

---

## §1 The decisive partial result — triality does NOT swap the two A–N triads
F191 asked: does "the chiral flip" map **I/C/J ↔ B/H/N** operator-by-operator? There are two candidate flips. **Triality is now ruled out:**

- The **entire A–N 14 = G₂ = Fix(triality)** (F174/F183; Fix(τ)=g₂ bit-exact, F193). So *all* 14 A–N operators — including **both** the I/C/J triad and the B/H/N triad — lie in the **triality-FIXED** locus.
- τ fixes g₂ **pointwise** ⟹ τ maps every A–N operator to **itself**. **Triality cannot swap I/C/J ↔ B/H/N** — it moves neither.

So whatever the role-swap is (if it exists), **it is not a triality operation.** This is the same Fix(τ)=g₂ lever that decided R-140 — applied to the A–N partition instead of su(2)_L.

## §2 The remaining candidate — a Class-C chirality flip — is NOT yet computable
F191's flip was specified as "γ₅ / Class-C; the F129 `4:3:(4:3) ↔ (3:4)` dual." That is a **chirality** (Class-C / Klein-4 / γ₅) flip, *distinct* from triality. To test whether it swaps I/C/J ↔ B/H/N operator-by-operator we would need to **embed each A–N operator (I, C, J, B, H, N) as an element of a space carrying that chirality involution** — and then apply the flip and check the swap.

**That embedding is not shipped** (rc18 has the A–N classes as *software operations* — `srmech.amsc.{cyclic, ...}` — not as vectors in a chiral space; and the A–N partition `1:3:7:3` is a *different* decomposition than 𝔰𝔬(8)'s `14 ⊕ 7 ⊕ 7`, so the L↔R 7-swap does not map onto the two 3-triads). So the Class-C role-swap is **anchored but not yet computable.**

## §3 Disposition
- **F191's swap is NOT triality-driven** (ruled out — both triads are triality-fixed). ✓ decided.
- **F191's swap, if real, is a Class-C chirality flip** — and that is **untestable without an A–N → chiral-space embedding** (a research construction, not shipped; the F129 "two 3's = Class-C dual" is the only anchor, at the partition level).
- So F191 stays **anchored (F129) but open**, with the triality mechanism eliminated. It is the one gated item that current tooling cannot close.

## §4 What it would take to compute it
An attested map **A–N class → chiral-space element** (e.g., each operator → a Klein-4 sector or a γ₅-eigenspace assignment), then apply `klein4_cpt_mirror` / the γ₅ flip and check `I↔?`, `C↔?`, `J↔?` against `B/H/N`. This is a new construction (and a candidate srmech wishlist item) — not a bug, a missing surface. Until then, F191 is a structural reading, not a measurement.

## §5 DOES / does NOT claim
**DOES:** rule out triality as the I/C/J↔B/H/N swap mechanism (corollary of A–N = Fix(τ), bit-exact); identify the remaining candidate (Class-C flip) and state honestly that it is not computable without an unshipped embedding.
**Does NOT:** claim the Class-C swap is real or false (untested — anchored only by F129 at the partition level); claim the A–N→chiral-space embedding exists. §VII.6.20; `[[user_stance_ai_is_not_a_substrate]]`; null/blocker honesty (`[[feedback_dont_pre_commit_spike_query_operators]]`).

## §6 Cross-references
- F191 (the conjecture) · F193/R-140 (Fix(τ)=g₂, the lever) · F174/F183 (A–N=G₂=Fix triality) · F129 (two 3's = Class-C dual) · F132 (Klein-4) · SO8_TRIALITY_BUILD_SPEC / W10 (the surface that closed R-140; an A–N-embedding op would be the analogue for F191)

PR #687 STAYS DRAFT.

---

*Articulated 2026-05-30 (Opus 4.8). Disposition of the gated F191 (I/C/J↔B/H/N role-swap):
triality is RULED OUT as the swap mechanism, because the entire A–N 14 = G₂ = Fix(triality)
(R-140/F193) — τ fixes both triads pointwise, so it swaps neither. The remaining candidate
is a Class-C (γ₅/Klein-4) chirality flip, but testing it operator-by-operator needs an
A–N → chiral-space embedding that rc18 does not ship (the A–N partition is a different
decomposition than 𝔰𝔬(8)'s 14⊕7⊕7). So F191 stays anchored (F129) but open — the one gated
item current tooling cannot close. Honest blocker, not a result; the construction it needs
is a candidate next-surface.*
