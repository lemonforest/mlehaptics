# ADR-0003: srmech is a C-host-standalone deliverable — never assume a Python environment

**Status:** Accepted — **standing policy** (governs every rc, every op, every review).
**Date:** 2026-07-16.
**Authors:** Steven Kirkland + Claude Opus 4.8.
**Supersedes:** none.
**Superseded-by:** none.
**Codifies the standing memory feedback:** `[[feedback_c_must_be_standalone_complete_no_python_fallback]]`
· `[[feedback_c_peer_delivered_same_rc_never_split]]` ·
`[[feedback_c_mirror_extends_to_every_composite_not_just_primitive_kernels]]` ·
`[[feedback_no_python_only_io_boundary_pal_mirrors_all_io]]` ·
`[[feedback_missing_math_is_added_to_srmech_as_cascade_never_imported]]`.

---

## 1. Context — the reflex this ADR exists to stop

srmech ships a **C library** (`c/src`, `c/include/srmech.h`) and a **Python package**
(`python/srmech`) that is a strict 1:1 mirror of it. The C library is the deliverable that
must run where **there is no Python interpreter at all** — an embedded host, a signed C-only
build, a downstream (e.g. siona) that links `libsrmech` and never imports CPython.

Despite this, we **keep re-deciding, at code-writing speed, that "Python will handle it"** —
even immediately after being told *"be prepared for no Python environment."* It happens the
same way the `Counter()` co-occurrence reflex happens (CLAUDE.md §2): the Python idiom is
right there, the C peer is more work, so the boundary silently drifts Python-ward. Examples of
the drift:

- "The C op handles the common case; the Python path covers the edge case." (Splits the input
  domain — now the op is **not** C-host-complete.)
- "Ship the Python now, add the C peer in a follow-on rc." (Splits delivery — the C host is
  broken between the two rcs.)
- "This orchestration is just glue; keep it in Python." (A composite with no C mirror — the C
  host cannot build the object at all.)
- "Read/write this one file from Python." (An I/O boundary the PAL does not mirror.)
- "Import `math`/`numpy` for this one function." (A dependency the C host cannot satisfy.)

Each is individually plausible and collectively fatal: any one of them means a C-only host
**cannot do the thing**. This ADR makes the C-host-standalone requirement a hard, checkable
policy instead of a reflex we re-lose every rc.

## 2. Decision

**srmech MUST build and run C-host-only. The C library is a first-class deliverable that
assumes no Python interpreter, no `libpython`, no CPython runtime, and no Python-side fallback.
Python is a *binding* and a *parity oracle* — never a runtime the C path leans on.**

Concretely, for **every** srmech capability (primitive class A–N op, carrier, composite,
orchestrator, I/O boundary, or DSL-declared class):

1. **Standalone-complete over the full input domain.** The C peer handles its *entire* input
   domain by itself — not "the common case," with Python owning the rest. If an input is valid
   for the Python API, the C peer produces the same result (or the same typed error). There is
   no domain the C host must bounce back to Python to service.
   (`[[feedback_c_must_be_standalone_complete_no_python_fallback]]`)

2. **Delivered in the same rc, byte-identical.** A new op ships its C peer **in the same rc**
   as its Python side, with **1:1 C↔Python byte parity** verified by a committed parity test.
   Never "Python now, C later." This includes *orchestrators* (e.g. `mint`), not only leaf
   kernels — orchestration that composes C-backed pieces still gets its own C entry point so a
   C-only caller can invoke the whole operation.
   (`[[feedback_c_peer_delivered_same_rc_never_split]]`, user direction 2026-07-16: "mint will
   also have C orchestration, 1:1 C:python parity.")

3. **Everything mirrors — every composite, not just primitive kernels.** There is no tier of
   "Python-only convenience composites." If Python can build it, C can build it.
   (`[[feedback_c_mirror_extends_to_every_composite_not_just_primitive_kernels]]`)

4. **All I/O mirrors through the PAL.** Every file/stream/socket boundary goes through
   `c/src/srmech_platform*` (the PAL) so the C host performs the same I/O. No "Python-only I/O
   boundary." (`[[feedback_no_python_only_io_boundary_pal_mirrors_all_io]]`)

5. **No host-math dependency.** No `numpy`, no stdlib `math`, no external math library — in
   *either* language. Missing math is added to srmech as a native cascade primitive, never
   imported. The full rule (all external math libraries, not just numpy/math) is **ADR-0005**.
   (`[[feedback_missing_math_is_added_to_srmech_as_cascade_never_imported]]`)

6. **Python is the oracle, not the fallback.** The pure-Python path exists to (a) be the
   numpy-free reference the C peer is checked against, and (b) run in a Python-only consumer.
   It is *never* the thing a C-host build silently falls through to — because in a C-only host
   it does not exist.

7. **Mirror the contract, not the bug.** Before mirroring a Python op to C, check for known
   bugs in the Python side — bit-exact mirroring of a buggy op enshrines the defect in two
   places. Fix first, then mirror. (`[[feedback_check_known_bugs_before_mirroring_python_to_c]]`)

8. **Every new ctypes binding declares `argtypes` + `restype`.** An undeclared binding is a
   silent ubuntu-only defer (the FFI layer mis-marshals on other platforms); declare both at
   registration. (`[[feedback_new_ctypes_binding_must_declare_argtypes_restype]]`)

9. **The parity verdict lives at the operator, floats only at the operand seam.** A C↔Python
   verdict that appears to need a float tolerance at the *operator* level is punting at the
   wrong seam — hold it exact at the operator; float enters only at the operand/display
   boundary. (`[[feedback_exact_verdict_at_operator_level_not_float_operand_seam]]`)

## 3. Consequences / enforcement (how we stop forgetting)

- **Same-rc C peer is a merge gate.** An rc that adds/changes a Python op without its
  byte-parity C peer is incomplete and does not ship. The parity test is the proof.
- **A C-host-only smoke is the ratchet.** The C test harness (`c/` standalone smokes, e.g.
  `test_srmech_genome`) builds and exercises the library **with no Python present**. New ops
  extend it. A capability that cannot be driven from the C-host smoke has not met this ADR.
  *(If a CI job that builds + runs the C library with no Python on PATH does not yet exist as a
  distinct gate, adding one is the enforcement work this ADR authorizes.)*
- **Review checklist item.** Every genome/carrier/op review asks explicitly: *"Does this run
  C-host-only, over its full domain, delivered this rc, byte-parity, PAL-mirrored, math-free?"*
  A "no" is a blocker, not a follow-up.
- **The parity + JPL discipline already in place is the substrate:** the per-op C↔Python
  byte-parity tests, `c/JPL_AUDIT.md` (Power-of-Ten), and the pedantic `-Werror` CI matrix.
  This ADR names the *purpose* those serve — a standalone C deliverable — so they are never
  treated as optional.

## 4. Non-goals

- This ADR does **not** forbid a Python-only *consumer* (a downstream that only ever uses the
  Python package is fine). It forbids a srmech capability that *requires* Python to function.
- It does not mandate that every op be C-*accelerated* for performance; it mandates that every
  op be C-*complete* for capability. (Performance dispatch is orthogonal — see the per-op
  native-dispatch pattern.)

## 5. Worked example — rc258 `mint` (§95a centromere, #1407)

`mint(kernels, the_one)` selects each chromosome's shape (stick vs centromere-minted) by the
attested `encode_shape` criterion and content-address orientation, then assembles the strand.
Under this ADR it is **not** enough for the Python `mint` to orchestrate C-backed
`chromosome`/`centromere` pieces: a `srmech_genome_mint` C entry point ships in the same rc,
byte-identical to the Python `mint`, so a C-only host can build a minted genome end-to-end.
The centromere cap, the shape selection (encode_shape C peer + `srmech_sha256_hex` orientation),
and the assembly all mirror in C. That is the shape every op takes.
