# Spike #162 (b) — `srmech.spectral.permute` API surface via catalogue config — design doc

**Date**: 2026-05-19
**Branch**: `research/spike-162-form-function-rotation-extensions`
**Scope**: design only — DO NOT IMPLEMENT in this spike
**User direction (verbatim)**: *"use srmech catalogue configuration instead of creating new scripts"*

This document proposes the `srmech.spectral.permute` API surface as the
composition pattern verified bit-exact by Spike #159
(`[[user_stance_form_function_rotation_is_a_c_m_composition]]`),
registered via the existing `srmech.amsc.tool_schema.ToolEntry`
mechanism. No new primitive class is added; no new C symbol is added;
no new module is added. The catalogue-config approach reuses three
existing surfaces:

1. `srmech.amsc.hdc.permute` — Class C cyclic permute (already shipped,
   C-native).
2. `srmech.amsc.hdc.bundle` — Class M HDC majority bundle (already
   shipped, C-native).
3. `srmech.amsc.format.sha256_bytes` — Class A content-addressing (used
   to compute the form-function rotation amount from token / vector
   content).

## API signature (design only)

```python
def permute(
    handle_or_bytes: SpectralHandle | bytes,
    *,
    shift: int | None = None,
    shift_from_content: bool = False,
    encoder_tag: str = "default",
) -> SpectralHandle | bytes:
    """Form-function rotation = Class A ∘ Class C ∘ Class M composition.

    The composition pattern verified bit-exact by Spike #159 per
    ``[[user_stance_form_function_rotation_is_a_c_m_composition]]``:

        permute(a, k) XOR permute(b, k) = permute(a XOR b, k)
            (Class C ∘ Class M; bit-exact 30/30 cells)

        shift = int(SHA-256(content)[:8], 16) mod D_bits
            (Class A; content-determined rotation amount)

    Parameters
    ----------
    handle_or_bytes:
        Either a :class:`SpectralHandle` (uses ``.coefficients_bytes``)
        or raw ``bytes``.
    shift:
        Explicit rotation amount in bits. Mutually exclusive with
        ``shift_from_content``.
    shift_from_content:
        If True, compute shift from SHA-256 of the input content
        (``int(SHA-256(bytes)[:8], 16) mod D_bits``). This is the
        Class A content-addressing path verified by Spike #159 Q3.B
        (within-vs-between separation preserved at 31.6× vs 35.0×
        plain).
    encoder_tag:
        Forwarded to ``SpectralHandle.substrate_descriptor_hash`` if a
        new handle is produced; otherwise ignored.

    Returns
    -------
    Same type as input (handle in → handle out; bytes in → bytes out).
    Output handle's ``content_sha`` is recomputed; substrate descriptor
    is preserved (rotation does NOT change the substrate).

    Raises
    ------
    ValueError
        If both ``shift`` and ``shift_from_content`` provided, or
        neither.

    Notes
    -----
    * Class chain: ``Class A (SHA-256 → shift) ∘ Class C (cyclic permute
      via ``srmech.amsc.hdc.permute``) ∘ Class M (acts on bundle inputs
      pre-bind; Spike #159 Q3.A bit-exact 30/30 + Q3.C bit-exact 6/6 for
      uniform-rotation)``.
    * **No new primitive class**: this is composition pattern over the
      14-class A-N vocabulary per
      ``[[feedback_no_privileged_primitive_classes]]``.
    * **No new C symbol**: implementation delegates to existing native
      ``srmech_hdc_permute`` + ``sha256_hex`` C surfaces; Python-side
      wraps the composition.
    * Identity (Spike #159 Q3.A): ``permute(a, k) XOR permute(b, k) ==
      permute(a XOR b, k)`` bit-exact.
    * Symmetry (Spike #159 Q3.C uniform): ``bundle([permute(v_i, k) for
      v_i in V]) == permute(bundle(V), k)`` bit-exact when all v_i share
      uniform rotation k.

    Canonical SSoT
    --------------
    * Kanerva (2009) *Hyperdimensional Computing*, Cognitive Computation
      1, 139 (HDC permute + bundle algebra).
    * Plate (1995) *Holographic Reduced Representations*, IEEE TNN 6, 623
      (binding-rotation symmetries).
    * Spike #159 — bit-exact verification of the composition
      (commits ee7498f / 7b4483d).
    * ``[[user_stance_form_function_rotation_is_a_c_m_composition]]`` —
      canonical stance, promoted 2026-05-19.
    """
```

## Implementation sketch (informative, not normative)

```python
# In srmech/spectral/__init__.py — appended below recompose / similarity.

from ..amsc.hdc import permute as _hdc_permute
from ..amsc.format import sha256_bytes


def permute(
    handle_or_bytes,
    *,
    shift=None,
    shift_from_content=False,
    encoder_tag="default",
):
    if (shift is None) == (not shift_from_content):
        raise ValueError(
            "spectral.permute: exactly one of `shift` or "
            "`shift_from_content=True` must be provided"
        )
    bytes_in = (
        handle_or_bytes.coefficients_bytes
        if isinstance(handle_or_bytes, SpectralHandle)
        else handle_or_bytes
    )
    D_bits = len(bytes_in) * 8
    if shift_from_content:
        # Class A: content-addressed rotation amount.
        digest = sha256_bytes(bytes_in)  # hex str via existing surface
        # First 8 hex chars = 32 bits of entropy, modulo D_bits.
        shift = int(digest[:8], 16) % D_bits
    rotated = _hdc_permute(bytes_in, shift)
    if isinstance(handle_or_bytes, SpectralHandle):
        return SpectralHandle(
            substrate_descriptor_hash=handle_or_bytes.substrate_descriptor_hash,
            coefficients_bytes=rotated,
            content_sha=sha256_bytes(rotated),
            n_modes=handle_or_bytes.n_modes,
        )
    return rotated
```

## ToolEntry catalogue registration (the "catalogue config")

This is the **load-bearing artifact** of sub-task (b). The
catalogue-config approach means: the operation is discoverable via
`srmech.amsc.tool_schema.get_tool_schema()` like every other srmech
operation, without writing a new module or new script.

Add to `_register_spectral_tools()` (new private registrar in
`srmech/amsc/tool_schema.py`, parallel to `_register_hdc_tools()` /
`_register_qm_tools()`):

```python
def _register_spectral_tools() -> None:
    """Register tool entries for the runtime spectral surface
    (``srmech.spectral.*``) per Spike #115 / Spike #159 design.

    Each operation cites the composition over the 14-class A-N
    vocabulary in its summary per
    ``[[feedback_no_privileged_primitive_classes]]``.
    """
    P = ToolParameter
    R = ToolReturn

    entries: List[ToolEntry] = [
        # Existing surfaces — to be registered in same registrar:
        ToolEntry(
            name="srmech.spectral.decompose",
            owner="srmech",
            category="spectral",
            summary=(
                "Spectral decompose: Class L (Hermitian Laplacian "
                "eigendecomposition) ∘ Class A (SHA-256 content "
                "addressing). Returns SpectralHandle with cached "
                "eigenbasis keyed by substrate descriptor hash. "
                "Canonical SSoT: Chung (1997) Spectral Graph Theory; "
                "Golub & Van Loan (2013) Matrix Computations §8.5."
            ),
            parameters=(
                P("state", "np.ndarray", True, "(n,) node-domain state"),
                P("laplacian", "np.ndarray", True, "(n, n) Hermitian"),
                P("encoder_tag", "str", False, "encoder identity tag"),
            ),
            returns=R("SpectralHandle", "handle with coefficients + descriptor hash"),
        ),
        ToolEntry(
            name="srmech.spectral.delta",
            owner="srmech",
            category="spectral",
            summary=(
                "Spectral delta: Class M (HDC bind / XOR self-inverse) on "
                "encoded coefficient bytes per Spike #114 Option B "
                "(1.22× faster than the Option-A encoder-handling "
                "wrapper). bind(ref, delta) = current; bind(delta, "
                "current) = ref; bind(a, bind(a, b)) = b. Canonical "
                "SSoT: Plate (1995) IEEE TNN 6, 623; Kanerva (2009) "
                "Cognitive Computation 1, 139."
            ),
            parameters=(
                P("ref", "SpectralHandle | bytes", True),
                P("current", "SpectralHandle | bytes", True),
            ),
            returns=R("bytes", "XOR delta; same length as inputs"),
        ),
        ToolEntry(
            name="srmech.spectral.recompose",
            owner="srmech",
            category="spectral",
            summary=(
                "Spectral recompose: Class L (inverse eigendecomposition "
                "state = V @ coeffs) ∘ Class M (SHA-256 content "
                "integrity check on handle). Reconstructs node-domain "
                "state from a handle on the same Laplacian + "
                "encoder_tag. Canonical SSoT: Chung (1997) Spectral "
                "Graph Theory."
            ),
            parameters=(
                P("handle", "SpectralHandle", True),
                P("laplacian", "np.ndarray", True, "same as decompose"),
                P("encoder_tag", "str", False),
            ),
            returns=R("np.ndarray", "(n_modes,) complex128"),
        ),
        ToolEntry(
            name="srmech.spectral.similarity",
            owner="srmech",
            category="spectral",
            summary=(
                "Spectral similarity: Class M (HDC similarity = "
                "1 − 2·hamming(a,b)/D ∈ [−1, 1]) on coefficient bytes "
                "per Spike #115 design / Spike #114 Option B. +1 "
                "identical; 0 orthogonal; −1 anti-correlated. "
                "Canonical SSoT: Kanerva (2009) §3.2."
            ),
            parameters=(
                P("a", "SpectralHandle | bytes", True),
                P("b", "SpectralHandle | bytes", True),
            ),
            returns=R("float", "in [-1, +1]"),
        ),

        # NEW (Spike #162 (b) — this design proposal):
        ToolEntry(
            name="srmech.spectral.permute",
            owner="srmech",
            category="spectral",
            summary=(
                "Form-function rotation: Class A (SHA-256 content "
                "addressing → shift amount) ∘ Class C (cyclic permute "
                "via srmech.amsc.hdc.permute) ∘ Class M (bundle / bind "
                "symmetry pre-rotation). Spike #159 verified bit-exact: "
                "permute(a, k) XOR permute(b, k) = permute(a XOR b, k) "
                "(30/30 cells); bundle commutes with uniform permute "
                "(6/6 cells). Content-determined shift gives "
                "form-function-determined cross-binning; preserves "
                "within-vs-between separation (31.6× rotated vs 35.0× "
                "plain). Canonical SSoT: Kanerva (2009) §3.2; Plate "
                "(1995) IEEE TNN 6, 623; Spike #159 records (commit "
                "ee7498f); "
                "[[user_stance_form_function_rotation_is_a_c_m_composition]]."
            ),
            parameters=(
                P("handle_or_bytes", "SpectralHandle | bytes", True,
                  "input to rotate"),
                P("shift", "int | None", False,
                  "explicit bit-rotation; mutually exclusive with shift_from_content"),
                P("shift_from_content", "bool", False,
                  "True ⇒ shift = SHA-256(bytes)[:8] mod D_bits"),
                P("encoder_tag", "str", False,
                  "forwarded to new SpectralHandle when input is a handle"),
            ),
            returns=R(
                "SpectralHandle | bytes",
                "same type as input; rotation preserves popcount + substrate descriptor",
            ),
        ),
    ]
    for e in entries:
        register_tool(e)
```

The new `_register_spectral_tools()` function would be added to the
sequence of registrars called at module-init (alongside
`_register_amsc_tools()`, `_register_qm_tools()`, etc.).

## Minimal-coverage test plan (DO NOT IMPLEMENT in this spike)

Per srmech CLAUDE.md JPL ratchet + Spike #115 test patterns, the
minimum-coverage test suite for `srmech.spectral.permute` follows the
existing `tests/test_*.py` family:

**`tests/test_spectral_permute.py`** (proposed):

1. `test_explicit_shift_round_trip` — `permute(v, k); permute(_, -k)`
   recovers original bytes exactly (involution; existing
   `srmech.amsc.hdc.permute` invariant).
2. `test_shift_from_content_deterministic` — same bytes → same shift →
   same rotated output (Class A determinism).
3. `test_shift_from_content_different_inputs_different_shifts` — two
   distinct content vectors produce two distinct shifts (collision
   resistance via SHA-256).
4. `test_rotation_bind_commutativity_bit_exact` — Spike #159 Q3.A
   replay: `bind(permute(a,k), permute(b,k)) == permute(bind(a,b), k)`
   bit-exact for k ∈ {1, 7, 64, 1023, 4097, 8191}. **JPL Rule 5: 2+
   asserts per test.**
5. `test_uniform_rotation_bundle_commutativity` — Spike #159 Q3.C
   replay: `bundle([permute(v_i, k) for v_i in V]) == permute(bundle(V),
   k)` for odd N, uniform k.
6. `test_handle_preserves_substrate_descriptor` — handle in → handle
   out with same `substrate_descriptor_hash`; `content_sha` updated;
   `n_modes` preserved.
7. `test_handle_content_sha_integrity` — new handle's `content_sha` ==
   `sha256_bytes(new_coefficients_bytes)`.
8. `test_mutual_exclusion_raises` — providing both / neither of
   `shift` / `shift_from_content` raises `ValueError`.
9. `test_within_between_separation_preserved` — magnitude-level
   replay of Spike #159 Q3.B: 4 paraphrase cohorts × 3 paraphrases;
   verify within-mean / between-mean ratio ≥ 10× (Spike #159 measured
   31.6× rotated vs 35.0× plain — guard at conservative 10× floor for
   test stability).
10. `test_tool_schema_registration` — `get_tool_schema().lookup(
    "srmech.spectral.permute")` returns the registered entry; `category
    == "spectral"`; owner == "srmech".

**Estimated test runtime**: < 2 s (no eigendecomposition; bind / bundle
/ permute are C-native and O(D)).

**JPL Power-of-Ten compliance**: all tests follow the
`[[feedback_jpl_rule_5_two_assert_habit]]` pattern — entry-pointer
assert + range/post-condition assert per test function.

## Composition with existing canon — citations + stance bridges

* `[[user_stance_form_function_rotation_is_a_c_m_composition]]` —
  canonical stance, promoted 2026-05-19 per user direction post-Spike
  #159 verdict. This API IS the runtime surface for that composition.
* `[[feedback_no_privileged_primitive_classes]]` — no class promotion;
  composition over existing 14-class A-N vocabulary.
* `[[feedback_no_binding_layer_carveout]]` — implementation reuses
  existing C-native `srmech_hdc_permute` + `sha256_hex` symbols; no
  binding-layer carve-out.
* `[[feedback_science_is_ssot_not_project]]` — canonical SSoT (Kanerva
  2009, Plate 1995, Chung 1997) cited in tool_schema summary; Spike
  #159 record cited as empirical anchor.
* `[[feedback_no_mvp_framing]]` — full-coverage shipping: design
  covers the whole `srmech.spectral.permute` surface, not a
  minimum-viable subset. Implementation is rcN+2 work per the
  spectral-module roadmap.
* `[[feedback_jpl_rule_5_two_assert_habit]]` — 2+ asserts per test
  function in the proposed test plan.

## Outstanding work after this design lands

* Implementation patch: append the function body + integrate
  `_register_spectral_tools()` into `tool_schema.py` module init.
  Single PR after Spike #162 closes.
* TestPyPI rc verification before clean v0.5.0 (or whichever release
  carries it) per `[[feedback_always_rc_first_for_downstream_publishes]]`.
* Position-aware variant (Spike #159 Round 1 fermata): does
  `permute(v(t), shift(t) + position_offset)` resolve the negation
  falsifier (Spike #147 / #159 Q2.B; pos-vs-neg sim 0.594)? Out of
  scope for the basic `permute` surface; potential future
  `srmech.spectral.permute_position_aware` if Spike #147-resolver
  spike validates the variant.

## Why this is "catalogue config" not "new script"

Per user direction *"use srmech catalogue configuration instead of
creating new scripts"*: the entire deliverable is

* **3 lines of catalog wiring** (the ToolEntry block) within an
  existing registrar pattern,
* **~25 lines of Python composition** over existing primitives,
* **0 lines of new C**,
* **0 new modules**.

Discoverable via `srmech.amsc.tool_schema.get_tool_schema()`, smoke-
testable via the auto-derivation path (ADR-0001 §5.5), and citable in
research notebooks via the registered canonical-SSoT string. This is
the AMSC framework discipline at full strength — adding capability is a
CONFIG change in tool_schema + tiny composition wrapper, not a new
script.

## Stance status

Design only; not yet implemented. Implementation deferred to a follow-
up PR that ships the body + test suite + tool_schema integration per
the discipline above. This document is the **catalogue-config
specification** sub-task (b) called for in Spike #162.
