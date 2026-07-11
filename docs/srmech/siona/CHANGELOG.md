# Changelog — siona

All notable changes to the `siona` package. Versioning: `X.Y.ZrcN` tags publish to **TestPyPI**;
clean `X.Y.Z` tags to **PyPI** (the human production gate). Each rcN ships via its **own PR**.

## 0.1.0rc1 — the UN-MIRROR cut (in progress; unreleased)

**Breaking / identity:** `siona` stops being a co-name alias for `srmech` (releases ≤ 0.0.4 were a
metadata-only mirror; srmech rc173 removed the in-wheel `import siona` alias) and becomes its **own
package**: the grounded inference layer, a **srmech profile plugin** (`srmech.profiles` entry-point)
on a lean `srmech>=0.8.1` dependency. The **wheel** stays lean — no corpora bundled inside it;
instruments and knowledge load by path. Knowledge **kernels are distributed as attested companion
artifacts** (CC-BY-SA-compliant by the MPR attestation each acquired fact carries — see
`PKG1_DECISION.md`).

### Added
- **`[profile.native]` C tier — Siona's own `libsiona_native.so`** (`c/siona_native.{c,h}` + `c/Makefile`,
  JPL Power-of-Ten clean). srmech's profile loader loads it as `srmech.profile("siona").native` after an ABI
  handshake; `siona._native` dispatches to it with a **bit-for-bit pure-Python fallback** (the has_native
  pattern, so the surface is identical with or without the `.so`). rc1 ops: `fnv1a64` (content hash),
  `tokenize` (byte-scan word boundaries; ~3–8× the Python scan), the windowed **co-occurrence accumulator**
  (`cooccurrence_edges_parallel`, tokens→edges via a caller-arena open-addressing hash; ~3.8× in the dense
  parallel form after the P0 `array`-buffer readback), and the **fused tokens→subset-Laplacian**
  (`cooccurrence_laplacian`, P1) — accumulates the ≤256-node subgraph's `L = D − A` directly from the token
  stream into an `array('d')` that IS srmech's `Mat` wire form (wrapped zero-copy → `symmetric_eigendecompose`),
  so the Θ(input) edge list NEVER crosses the boundary: **20.3× over the round-trip, bit-for-bit == a
  `dense_laplacian` compose, identical spectrum**. FFI note: a standalone co-occurrence that hands edges back
  to Python can't win big (the edge list is Θ(input)); the real win is fusion. Local/dev build: `make -C c`;
  a release ships true per-OS wheels via cibuildwheel. Optimization path recorded in `c/OPTIMIZATION.md`.
- **Fix:** the `board` bridge surface (a `Board` data constant, not a callable) is removed from
  `[profile.bridge]` — it failed the loader's callability smoke test and blocked the whole profile from
  activating. The default board stays reachable as `siona.boards.ENGLISH`.
- `siona.bridge` — the de Bruijn fiber walk + full-body recall (walk/recall/route/two_mode_recall);
  symbol-agnostic (integer ids); pure-Python, exact.
- `siona.infer` — the grounded inference loop (research findings F1008–F1012):
  - `Session.route` (F1010): intent routing {define | tool-call | self-command | continue} by
    **declared operator frames + operand shape** — no similarity thresholds (that signal was
    measured and rejected as non-separable).
  - `Grounding` (F1008): utterance→tool grounding over srmech's **live** `tool_schema` registry
    (name-weighted, order-carrying unigram+adjacency-bigram encoding; 347-tool surface).
  - `Session._drive_tool` (F1009): signature-fit on typed parameters → resolve → **run the real
    srmech op** → read the result into working memory; (F1012) cross-turn operand resolution —
    a turn may reference a value **remembered in an earlier turn**.
  - the self surface (F1011): siona's own 8 tools registered into srmech's registry via
    `register_profile_tools` — one registry, two surfaces; `help` answers from the **live** schema
    (Class-H self-introspection).
  - ingested knowledge **kernels** (F1012): declared linear-map form; composition is
    **exact-rational** (integer num/den, srmech `cyclic.gcd` reduction, collapse only at display).
- `siona.boards` — the language-BOARD layer (PKG-1): per-language **declared operator profiles**
  (`Board`, `ENGLISH`, `load_board` TOML descriptors) on the byte/glyph substrate (script-agnostic;
  anagram-distinct). **English is board #1, not the architecture.** Rosetta-layer lineage (F649,
  ni-Vanuatu as living exemplar) documented dignity-first — exemplar + pointer, never data.

### Discipline
- Bag-of-words audit **clean** (PKG1_DECISION §audit): every content encoding carries order; an
  order-free bundle may only be a weighting statistic. Regression set: F1004/F1008/F1010.
- Publish gate: see `PUBLISH_GATE.md` (publisher-repo move, notebook stays with mlehaptics RTD,
  hardening backlog before the rc1 tag).

## 0.0.4 and earlier (historical)
- Metadata-only co-name alias for `srmech` (retired; see the un-mirror note above).
