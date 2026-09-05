# ADR-0009: srmech is a multi-implementation codebase — the capability is the invariant, each implementation is a coherency projection

**Status:** ✅ Accepted — **standing policy** (governs every rc, every op, every review).
**Clauses:** unaudited.
**Date:** 2026-07-19.
**Authors:** Steven Kirkland + Claude Opus 4.8.
**Supersedes:** none.
**Superseded-by:** none.
**Amends:** **ADR-0003** (C-host-standalone — never assume a Python environment). ADR-0003 stays
in force in full; this ADR reframes the relationship its clause §2.6 describes and adds the
governance that made ADR-0003 unenforceable in practice. See §7 for the amend-not-supersede
rationale.
**Motivated by:** `docs/srmech/notes/c_host_parity_audit_rc273.md`.

---

## 1. Context — a correct principle that kept failing

ADR-0003 (2026-07-16) already says everything a reader would need: the C library is
first-class, every composite mirrors, orchestrators get their own entry point, delivery is
same-rc. It is right, it is Accepted, it is standing policy — and in the three days after it
was accepted, four capabilities shipped through review without a C implementation while
carrying language asserting they had one.

A principle that correct, failing that reliably, is not failing because people forgot it. It is
failing because the surrounding structure — vocabulary, taxonomy, tests — encodes the opposite
of what it says, and the structure wins. This ADR records the diagnosis, because an ADR that
only re-asserts ADR-0003 louder will produce the same result.

### 1.1 The default that generates the drift

The unstated default is: **Python is the implementation; C accelerates the hot parts.**

Under that default a missing C entry point is an **optimization gap, not a correctness gap** —
and an optimization gap is a legitimate thing to defer. That is why every individual deferral
below passed review while reading as reasonable. Each one is locally plausible; the sum is a
systemic hole in a shipped deliverable.

### 1.2 Observed instances (verified against the tree)

| rc | Capability | The claim made | What was actually true |
|----|-----------|----------------|------------------------|
| rc262 | `integrate` | docstring asserted "a C-only host integrates identically … region byte-offsets in the manifest" | the op ran on an in-memory strand with **no manifest at integrate-time**; the boundary-scan → locus → splice orchestration was Python-only. Refuted by the rc273 audit §G4; closed by rc276. |
| rc270 | `mint_strand` | "byte-identical whether the cap came from C or pure Python" | true of the **cap**, not of the **op** — the glue (data-turn scan → metacentric midpoint → single-block insert) was Python-only. Closed by rc277. |
| rc273 | `amplify` / `copy_number_of` | the C test proved reader-transparency and its comment concluded the additive field "needs no format bump … and no C change" | reader-transparency ≠ implementation parity. There is still **no C path to write or read the copy-number**. `grep srmech_genome_amplify c/include/srmech.h` → 0 hits, at rc280. **Still open.** |
| rc280 | `section_counts` | **claimed nothing false** — the CHANGELOG and header state the ceiling, the corpus figure, and the non-reentrancy plainly | the compiled implementation declines above ~11k sections against a 240,881-section corpus and the Python one runs. A *disclosed* missing capability is still a missing capability. Tracked as #899. **Still open.** Detailed below — this is mechanism 4, not mechanism 1. |
| rc466 | the five `exact=` Laplacian builders | rc466 shipped an exact-ℚ route on `normalized_laplacian`, `mass_normalized_laplacian`, `magnetic_laplacian`, `quaternion_laplacian` and `klein4_gain_laplacian`, and the drain gate measured every one of them exact | **a bare-C host runs 0 of the 5.** Every C symbol in the family is double-only in both directions — `srmech_graph_normalized_laplacian` (srmech.h:1891), `srmech_graph_mass_normalized_laplacian` (:1919), `srmech_graph_magnetic_laplacian` (:2002), `srmech_graph_klein4_gain_laplacian` (:2031): `const double *weights` in, `double *out_matrix` out. There is no exact arm and no `Q` / `Qi` limb form, so the capability exists only in the scripting implementation. Recorded rather than closed at rc467 (`#T1188`): an exact arm needs exact-ℚ bigint matrix output plus the perfect-rational-square root path — a slice on the scale of the `srmech_qmat_*` family, not a rider. Tracked as task `#T1188`, this ADR row being the landing surface — §6a's capability-rooted ledger is authorized follow-on and is not yet implemented, so a row here is what §5 means by "files a tracked gap". Closing it later is ABI-ADDITIVE (new symbols; srmech.h:2001 states the convention), so `SRMECH_ABI_VERSION` stays 25 either way. **Still open.** |
| rc467 | `resonant_spectrum(exact=True)` | rc467 drained the last undeclared silent demoter by composing four shipped exact ops, and the route is exact end to end in Python | **a bare-C host runs 0 of the exact route.** `srmech_resonant_spectrum` (srmech.h:2828) takes `const double *L_rowmajor`, so the exact route must SKIP the native call entirely rather than dispatch to it; the Python marshalling that would feed it is a `float()` per entry (coupling.py, `_resonant_spectrum_native`). Note the shape: this is an ORCHESTRATOR-level gap, not a kernel one — every kernel the exact cascade needs already ships in C (`srmech_sturm_isolate` srmech.h:13190, `srmech_eigvec_exact` :13271, `srmech_factor_integer_poly` :10524, `srmech_faddeev_leverrier` :13160, and the `srmech_qmat_*` family), so what is missing is the exact-route composition and its exact-ℚ return shape, not the arithmetic. Tracked as task `#T1188`, same landing surface; same close path and same ABI consequence as the row above. **Still open.** |

A fourth pattern — *"it declines cleanly, the pure path works"* — is a **safety** argument
offered where a **capability** argument is required. A clean decline means the compiled
implementation cannot serve an input the scripting implementation can; that the decline is
well-behaved is a separate (and good) property. This pattern is already named as an
anti-pattern for carriers in **ADR-0006 §2.5** ("do not add a fast path that declines at its
ceiling"); this ADR generalizes it from carriers to implementations.

**rc280 `section_counts` is the instance — and it is a different, sharper case than the three
above.** JPL Rule 3 bans malloc and the exported signature carries no `ws` arena, so
`srmech_genome_section_counts` works out of three file-scope statics (`g_sc_arena`,
`g_sc_slots`, `g_sc_win` — `c/src/srmech_genome.c`). The bounds, verified in the header block
at `c/include/srmech.h`:

- the 32 MiB catalog arena's ~2.7 KiB/chromosome term gives a **~11,000-section ceiling**,
  against the F1253 store's **240,881 sections**;
- the 2^18-slot count table gives a **196,608 distinct-id ceiling**, against the store's
  **1,100,189 ids** — a second bound, exceeded by more than 5×.

Over any bound the peer returns `SRMECH_ERR_OVERFLOW`, the binding reads that as a decline, and
the Python implementation runs. The same statics make the call **not reentrant**. Tracked as
task **#899** (per the conductor; the id does not appear in the tree, so it is recorded here on
that authority, not tree-verified).

**Why it is the sharper case:** rc262/rc270/rc273 each *asserted* a parity that did not exist.
rc280 does the opposite — the CHANGELOG entry and the header block state the ceiling, the
corpus figure, the non-reentrancy, and the fact that removing the ceiling would require a `ws`
parameter (a wire-signature change) *deliberately not taken in that rc*. That disclosure is
exemplary and this ADR does not fault it. **The mechanism survives full disclosure anyway** —
because the honest decline is offered as the resolution rather than as a filed gap, and a
capability the compiled implementation cannot serve at the only scale that matters remains a
missing capability no matter how well it is documented. This is precisely why §5 requires a
decline to file a tracked gap: candour about a hole is not the same as tracking it, and
mechanism 4 is the one mechanism that a well-written changelog does not defeat.

### 1.3 The four reinforcing mechanisms

Each verified against the tree at v0.9.0rc280:

1. **The vocabulary encodes hierarchy.** "C **peer**" (1668 occurrences), "**pure fallback**"
   (175), "**native dispatch**" (276), "accelerat\*" (499), `HAS_NATIVE` (1451). *Peer* is
   relative to something; *fallback* presupposes a primary; *accelerate* presupposes a
   reference implementation being sped up. The words do the thinking.

2. **The taxonomy is Python-rooted, so it cannot express the goal.** All **680** rows of
   `python/tests/rosetta_classification.ndjson` are keyed by a Python dotted path
   (`exposed_as` / `defined_at`); **zero** rows are keyed by a C symbol. The enumeration step
   in `test_rosetta_completeness.py` is explicitly "enumerate the live public-op surface
   (every public callable defined in `srmech.amsc` / `srmech.qm` /
   `srmech.signal_processing`)." Every bucket therefore describes *a Python op's relationship
   to C*: `c_dispatched` = "routes to a `srmech_*` C symbol", `composition_of_c` = "pure
   composition of `c_dispatched` ops". **There is no bucket meaning "this capability exists
   independently in both trees."** The classification literally cannot say the thing this
   project wants said.

   The live exhibit: `srmech.biology.genome.amplify` is classified `composition_of_c`, a bucket
   whose own docstring annotates it *"(standalone-ready)"*, while no `srmech_genome_amplify`
   symbol exists. The label is not a lie about the row's own definition — it is a true
   statement in a vocabulary that cannot distinguish "composes C parts" from "a C host can
   run this."

   **The defect is not confined to `composition_of_c`.** `srmech.biology.plasmid.section_counts`
   is classified **`c_dispatched`** — the *strongest* label the taxonomy has, "routes to a
   `srmech_*` C symbol (standalone-ready)" — and it does route to one. That C implementation
   also declines above ~11,000 sections against a 240,881-section corpus (§1.2). Both facts are
   true simultaneously, because `c_dispatched` records that a C symbol is **reached**, never
   that it **suffices**. No bucket in the taxonomy has a place to put "has a compiled
   implementation that cannot serve the real input domain."

3. **The tests run in one direction only.** `test_rosetta_transitive_standalone.py` walks the
   callee graph of every `composition_of_c` op, but `_reached_ledger_ops` treats a
   `c_dispatched` / `composition_of_c` / `non_compute` row as a **leaf and stops** (`continue
   # C-backed / validated-elsewhere leaf: stop`). So it proves a composite *reaches* C-backed
   leaves; it never proves a bare-C host can run the composite's own glue. Nothing anywhere
   enumerates the C header and asks "is the C host complete?" — the only test that reads
   `c/include/srmech.h` at all (`test_native_sha256.py`) reads it for the version string.

4. **"It declines cleanly" defers indefinitely.** A safety property is accepted in place of a
   capability property, and because the decline is genuinely well-behaved there is never a
   forcing moment. The rc280 `section_counts` instance (§1.2) shows this is the one mechanism
   that **full disclosure does not defeat**: everything about that ceiling is documented
   accurately and the gap is still open, because being candid about a hole and tracking it are
   different acts.

**Why the mechanisms are load-bearing together:** (1) makes the gap unspeakable, (2) makes it
unclassifiable, (3) makes it undetectable, (4) makes it indefinitely deferrable. Fixing any one
alone leaves the other three generating the same outcome.

## 2. Decision — the framing

**srmech is a multi-implementation codebase. The CAPABILITY is the invariant. Each
implementation is a COHERENCY PROJECTION of that capability into one execution regime. No
implementation is primary.**

```
                      CAPABILITY  (the invariant)
                   e.g. "amplify a gene's copy number"
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   scripting-            compiled-            (future: a third
   coherency             coherency             implementation —
   implementation        implementation        Go / Rust / …)
   (python/srmech)       (c/src, c/include)
        │                     │                     │
        └─────────────────────┴─────────────────────┘
              same capability · byte-identical results
              differing only in execution regime
```

This is the project's own frame-relativity discipline applied to its own architecture.
Privileging the Python frame and calling C "the accelerator" is the same error as privileging
one quantity and calling its twin "only mathematically real." The implementations are related
by projection, not by rank.

Concretely:

1. **Capability-first.** A capability is defined once, independent of language. An
   implementation either realizes it over the full input domain or does not have it. "Realizes
   it by calling the other implementation" is not realizing it.

2. **No implementation is the reference.** The **differential-oracle role is a test-time role
   that rotates**, not a rank. When checking a new C implementation, the Python one is the
   oracle; when checking a Python refactor, the C one is. This is the clause of ADR-0003 §2.6
   ("Python is the oracle, not the fallback") that this ADR amends: the sentence is correct
   about what Python is *not* (a fallback) and, read as a standing description rather than a
   test-time role, incorrectly fixes Python as the thing the other implementation is measured
   *against*. The oracle relation is symmetric; the parity claim is what matters.

3. **Parity is byte-identical results, not similar behavior.** Unchanged from ADR-0003 §2.2.

4. **Implementations may differ in execution regime only** — scheduling, memory strategy,
   routing, packaging. They may not differ in which inputs they serve or what results they
   produce.

## 3. Decision — vocabulary

The hierarchy words are retired from **capability description**. Some remain valid as
**routing** or **packaging** description; those distinctions are stated, not glossed.

| Retired / restricted | Why | Use instead |
|---|---|---|
| "C **peer**" | a peer is defined relative to a primary | "the C implementation" / "the compiled-coherency implementation" |
| "**pure fallback**", "pure-Python fallback" | a fallback is what you get when the real thing is absent | "the Python implementation" / "the scripting-coherency implementation" |
| "C **accelerates** …", "the accelerator", "native **acceleration**" | frames C as a speed treatment applied to a Python original | "the compiled-coherency implementation" (capability); "faster on this path" (a measured performance claim, stated as such) |
| "**native dispatch**" — *restricted, not retired* | valid for **routing**: which implementation services a call inside a co-installed process. Invalid as a description of whether a capability **exists**. | keep for routing; never as evidence of parity |
| "Python is the **oracle**" | correct as a test-time role, wrong as a standing rank | "the differential oracle for this check" (naming which direction, this time) |
| "just glue", "only orchestration" | orchestration is a capability; ADR-0003 §2.2 already says so | name the capability |

**Kept deliberately:** "**C twin**" (already in use in the Rosetta ratchet) — *twin* is
symmetric and already carries the intended framing. Renaming symmetric vocabulary would be
churn.

**Not retired here:** the `HAS_NATIVE` **code symbol**. It names a real runtime fact (is the
shared library loaded in this process) and renaming it is code work, out of scope for a
documentation ADR. It is flagged for the follow-on work in §5 to consider; this ADR does not
authorize the rename.

## 4. Decision — the exemption rule

**Exempt from multi-implementation parity: host-integration and protocol-adapter layers.**
Specifically the MCP server adapter and the Anthropic-SDK / `claude_sdk` adapter (in the tree:
the `srmech.mcp` / `srmech.llm` surfaces, and the `host_glue` rows — 21 of them — under the
`non_compute` bucket). These bind srmech to a specific host runtime; there is no
language-independent capability underneath them to project.

**Nothing else is exempt.**

Any new exemption **requires an amendment to this ADR** — a PR that argues the case against
this rule, reviewed as an architecture decision. An exemption asserted in a docstring, a
changelog entry, a test comment, or a code review reply is **not an exemption**. This is the
specific procedural gap the rc262 / rc270 / rc273 instances went through: each recorded its
carve-out in prose attached to the code, where nothing was positioned to challenge it.

## 5. Decision — a clean decline is a correct FAILURE MODE, not parity

An implementation that declines an input the other implementation serves **does not have the
capability for that domain**. The decline being clean, typed, non-crashing, and well-tested is
required (ADR-0003 §2.1, ADR-0006 §2.6) and is **never sufficient**.

**Every such decline files a tracked gap** — a ledger row (§6a) recording the capability, the
declining implementation, and the boundary. "It declines cleanly, the other path works" is a
statement about the quality of the decline, and is not a parity argument.

This applies **even when the decline is fully and accurately documented**. rc280's
`section_counts` (§1.2) documents its ceiling, its corpus shortfall, its non-reentrancy, and the
signature change that would remove it — and the gap is still open, because a changelog entry is
not a tracked gap. **Disclosure is necessary and is not sufficient.** A build-time lever
(`SRMECH_GENOME_SC_ARENA_BYTES`) that a caller *could* raise is likewise not parity: parity is a
property of what the implementation serves as shipped, not of what a recompile could reach.

## 6. Consequences — follow-on work this ADR authorizes but does NOT implement

This ADR is the framing that the following derive from. Each is named here so the downstream
change is derivable rather than a third ad-hoc scheme. **None of it is implemented by this
ADR**, and each maps to a mechanism in §1.3:

| Mechanism (§1.3) | Follow-on this ADR authorizes |
|---|---|
| 1 — vocabulary encodes hierarchy | A vocabulary sweep of docstrings / `ToolEntry` summaries / ADR + CLAUDE.md prose per the §3 table; a decision on the `HAS_NATIVE` symbol |
| 2 — taxonomy is Python-rooted | **(a) A capability-rooted ledger** |
| 3 — tests run one direction | **(b) A C-host capability manifest** |
| 4 — clean decline defers indefinitely | The §5 rule made mechanical: a decline boundary is a ledger row, not a comment |

**(a) A capability-rooted ledger.** Re-key the Rosetta ledger from a Python symbol to a
**capability**, with a set of implementations present and a set missing:
`capability → {implementations present} / {missing}`. Under this shape a Python-only capability
renders as **"missing: compiled"** — a hole with a name — rather than as `composition_of_c`, a
bucket whose annotation reads *"standalone-ready."* This is the change that makes the gap
speakable and classifiable; the two current buckets survive inside it as *how* an
implementation realizes a capability, which is a genuinely useful distinction that should not
be lost.

**(b) A C-host capability manifest.** Enumerated and asserted **from the C side** — the C tree
declaring what it provides, checked against the capability ledger. The motivating fact:
**nothing in the tree today would notice if the C implementation lost a capability entirely.**
The Rosetta ratchets enumerate Python and ask whether it reaches C; no test enumerates C. A
manifest closes the reverse direction, and is the thing that would have caught rc262 / rc270 /
rc273 at review time.

> **Status note (rc300, `#938`) — a bounded first step on (b), not its delivery.**
> `srmech/amsc/_c_claims.py` records, per `c_dispatched` op, the `srmech_*` symbols that op's
> dispatch path names, filtered against the symbols *declared in `c/include/srmech.h`*; it is
> checked against the loaded library by `srmech.amsc._native.c_claim_report()`, surfaced as
> `describe()["c_claims"]`, and asserted by `tests/test_c_claim_resolution_rc300.py`.
>
> What this changes in §1.3 mechanism 3: the claim that *"the only test that reads
> `c/include/srmech.h` at all reads it for the version string"* is no longer true, and the claim
> that *"nothing in the tree today would notice if the C implementation lost a capability
> entirely"* is now **partially** false — a lost symbol that a `c_dispatched` op claims is
> detected, named, and fails the suite. That state was previously silent, because ABI matching
> does not cover it: `srmech.h` adds symbols ABI-additively, so a stale build keeps ABI 8, keeps
> `HAS_NATIVE` true, and falls to correct pure paths under a false classification.
>
> What it does **not** do, and why (b) stays open: the direction is still Python-rooted. It asks
> *"is the symbol this Python op claims present?"*, not *"is the C host complete?"*. It cannot
> see a capability C never had a Python claimant for, it says nothing about whether a reached
> symbol **suffices** over the real input domain (the §1.2 / mechanism-2 defect is untouched),
> and its extraction is static, leaving **23 of 263** `c_dispatched` ops with no attributable
> symbol — enumerated in `UNVERIFIABLE_CLAIMS` under a down-only ceiling rather than left
> invisible.

**(c) How a third implementation is additive, not a port.** Under this framing a Go or Rust
implementation is **a third projection of the same capability set**, not a translation of the
Python or C source. It is checked against the capability ledger and the manifest, differentially
against whichever existing implementation serves as oracle for that check, and it inherits the
§4 exemption rule unchanged. Concretely: it does not need to be a line-for-line port of either
tree, and neither existing tree acquires seniority over it. What it must do is realize each
capability over the full input domain with byte-identical results. This is also the test of
whether the framing is real — if a third implementation would have to be "a port of the C one,"
the capability is not actually defined independently of an implementation, and that is a defect
in the capability definition.

## 7. Why this amends ADR-0003 rather than superseding it or landing standalone

**Not a supersede.** All nine of ADR-0003's decisions remain correct and in force; none is
retracted. Superseding would retire nine correct rules and force their re-litigation, and would
lose the memory-feedback trail ADR-0003 consolidates. The rc273 audit's finding was never "0003
is wrong" — it was that 0003's standard was applied strictly to some ops and loosely to others,
with nothing to arbitrate.

**Not standalone-alongside.** The tension is real and must be resolved in writing rather than
left for a reader to notice: ADR-0003 §2.6 fixes Python as the oracle and C as the standalone
deliverable, which is an asymmetric frame. A new ADR that ignored that clause would leave two
documents in force disagreeing about whether an implementation can be primary — the same
unenforced disagreement between two standards that the audit identified as the systemic root
cause (audit §0). §2.2 above states the amendment explicitly.

**Therefore: a new ADR that amends one clause of 0003 and adds governance around it.** ADR-0003
answers *what must be true* (C runs standalone, everything mirrors). ADR-0009 answers *why it
keeps not being true, what the relationship between implementations actually is, what is
exempt, and what a decline means.* ADR-0003 keeps its number, its status, and its content;
its index row and this ADR cross-reference each other.

## 8. Scope honesty — what this ADR does NOT claim

- **It does not assert that srmech currently has multi-implementation parity. It does not.**
  This ADR defines the standard the audit's open gaps are measured against.
- **Current state as verified at v0.9.0rc280** (the audit was taken at rc273 and the tree has
  moved): audit gaps **G4 `integrate`** and **G5 `mint_strand`** are **closed** (rc276, rc277 —
  both now `c_dispatched` with whole-op C entry points). **G6 `amplify` /
  `copy_number_of`** closed at rc281; **G1 `recursive_cut`** closed at **rc284**. **G2
  `genome_from_graph`**, **G3 graph `genome_partition`**, and the **G7** minors
  (`condense`, `decondense`, `active_telomere`, `genes`, `mint_plan`, multi-gene
  `chromosome`) remain **open**.
  > **G1 caveat as written at rc280, and how it resolved.** At rc280, `grep
  > srmech_laplacian_recursive_cut c/include/srmech.h` returned a hit — but the hit was
  > inside a **prose comment** on `srmech_genome_integrate_plasmids` recording that stage 2
  > *"NEVER calls"* it. The symbol name existed only as a reference to its absence. **rc284
  > closed G1**: `srmech_laplacian_recursive_cut` (+ `_arena_bytes`) is now declared in the
  > header, defined in `c/src/srmech_laplacian.c`, bound in `_native.py`, and genuinely
  > dispatched by the op — all four checked mechanically by the rc281 wire-glue ratchet.
  >
  > **What G1 turned out to be is worth recording, because the obvious reading was wrong.**
  > G1 was widely described as needing a Fiedler-vector computation built in C under
  > ADR-0005. It did not: `srmech_laplacian_fiedler_sparse_file` has been native since
  > **rc168**, with the §101 tick already threaded at phase `PARTITIONING`, and
  > `srmech_rational_sqrt` has supplied its only square root since rc45. The missing piece
  > was the **`while pending` recursion around the engine** — the disk-backed queue, the
  > induced-subgraph relabel, the tome lifecycle — plus three absent **PAL** primitives
  > (`mkdir` / `remove` / replacing-`rename`). The gap was I/O and control flow, not
  > mathematics. This is a §1.3-shaped mechanism: the capability looked blocked on the
  > hardest-sounding component, and was actually blocked on the most mundane one.
  >
  > **G1 was the shared dead-end of G2 and G3, so rc284 UNBLOCKS both — but unblocking is
  > not closing.** G3 additionally needs exact-integer participation, the antimode
  > histogram and per-node classify; G2 needs all of G3 plus its in-RAM `_induced_subgraph`
  > relabel, the per-group `graph_to_kernel` → `mint_strand` loop and strand assembly.
- **rc279 and rc280 shipped a new capability surface** (`plasmid_extract`, `section_counts`,
  `conserved_core`, `genome_integrate_plasmids`), taking the ledger from 677 to **680** rows.
  Two are `c_dispatched`, two `composition_of_c`. `section_counts` is the §1.2 instance.
- **It does not claim the diagnosis in §1.3 is complete** — four mechanisms were identified and
  verified; there may be others.
- **It does not implement any of §6.** No ledger is re-keyed, no manifest exists, no vocabulary
  sweep has been performed, and no test has changed as a result of this ADR.
- **It does not commit the project to a Go or Rust implementation.** §6(c) states how one would
  be additive *if* undertaken.
- **It does not resolve the rc273 audit's three open fermatas** (audit §5: the reclassification
  of native-dispatched genome ops; the scope of the systemic ratchet fix; whether G7-minor reads
  owe a C mirror). Those are conductor decisions and are inputs to §6(a), not outputs of this
  ADR.

## 9. Sources

`docs/srmech/notes/c_host_parity_audit_rc273.md` (the motivating audit) ·
ADR-0003 (amended by this ADR) · ADR-0005 (no external math library) ·
ADR-0006 §2.5–2.6 (decline-at-a-ceiling as an anti-pattern; bounded arena + honest decline) ·
ADR-0007 (release engineering) ·
`[[feedback_genome_must_exist_fully_in_c]]` ·
`[[feedback_c_must_be_standalone_complete_no_python_fallback]]` ·
`[[feedback_c_peer_delivered_same_rc_never_split]]` ·
`[[feedback_c_mirror_extends_to_every_composite_not_just_primitive_kernels]]` ·
`[[feedback_name_the_gap_plainly_dont_hedge_or_document_away]]` ·
`[[feedback_dont_ship_partial_unproven_difficulty_is_not_an_excuse]]` ·
`[[reference_two_language_problem_inverted_python_c_different_scales]]`

User direction (2026-07-19): *"it's simply supposed to be a multi source code base. the only
things so far exempt from this parity has been the mcp/claude_sdk layer … there should be a C
native and Python native codebase for srmech that do the exact same thing at different coherency
perspectives, scripting vs native compiled."*
