# ADR-0011: One encoding per datum — the genome has no cache

**Status:** ✅ Accepted — user direction 2026-07-26. Applies immediately to all genome work.
**Clauses:** unaudited.
**Date:** 2026-07-26.

---

## Context

The genome store has repeatedly grown a *second* representation of data the strand already
determines: a `manifest.json` sidecar, a re-parsed head, a catalog index. Each time it was
introduced for a defensible local reason — speed, convenience, "the read needs the digest" — and
each time it later had to be removed or bound because the two encodings could disagree.

The principle that would have prevented every one of those was never written down. It exists as a
user stance and as tracked work (the sidecar-dissolution arc), but **an implementer reading the ADRs
finds nothing**. ADR-0003 says the C host must stand alone and that the catalog is derived by
scanning the body — the principle *applied*, but never *named*. So it was rediscovered instead of
followed, and a build brief in rc345 restated "the manifest is a cache" as though it were settled
design.

**This was already decided once, on exactly these grounds, and then undone by relabeling.**
rc142 (§44 / F733) removed the manifest gene-index sidecar and said why:

> **§44 corrects the direction: biology has NO offset table** — chromosome + gene boundaries are
> FIXED-WIDTH INLINE markers scanned for in the strand itself (TTAGGG telomere repeats / stop
> codons), and fixed-width records are exactly what make the sidecar unnecessary.

It shipped a regression test pinning *"the body carrying the caps + the manifest carrying NO
sidecar."* The **offset table** was genuinely dissolved. But the **file** was kept and renamed to
*"an optional, rebuildable `.fai`-style cache"*, and rc144 stated its actual purpose:

> When `manifest.json` exists, the loaders read it (**the cheap, unchanged fast path — `turns.bin`
> never opened for a catalog read**).

That is a cache, by its own description. Calling it *optional* and *rebuildable* made the principle
feel honoured while the second encoding stayed on disk — and every later coupling to it (rc337's
second parse, the digest mirror) grew from the surviving file, not from a new decision. **The
failure mode this ADR exists to prevent is not "someone adds a sidecar"; it is "a dissolved sidecar
survives as a cache under a gentler name."**

**The rediscovery is measurable.** Within a single day:

| | what happened |
|---|---|
| rc337 | added `genome_catalog_committed_head` — a *second* open+parse of `manifest.json` to recover the committed digest |
| rc337 | that helper's `void` return conflated "nothing committed" with "arena too small to look" — **a bound that failed open** |
| rc342 | deleted it, threading the digest out of a parse the derive **already performs**; **no read gained an open, a parse, or a hash** |
| rc342 | the first attempt reused rc337's approach and tripped the rc282 open-count ratchet at 5 → 7 opens — the guard rejected the cache |

The cache was never the answer, and a guard said so before a human did.

## Decision

**A datum has exactly ONE encoding in the genome. Not an encoding plus a fast cache.**

Concretely, within the genome:

1. **Anything derivable from the strand is DERIVED, never stored.** If the strand determines it, the
   strand is where it lives. `content = n_turns − n_chromosomes` is derived; the catalog is derived
   by scanning the body; the committed digest is read from the head, not mirrored.
2. **No sidecar.** `manifest.json` is a violation of this ADR, not an exception to it. Its
   dissolution into a genome-native seed + attestation chromosome is the standing direction.
3. **No cache, and no escape hatch inside the genome.** If a cache is ever genuinely required, **it
   lives outside the genome boundary** — a separate, separately-named layer with its own lifecycle —
   never a genome field, never a head entry, never a format-version bump.
4. **A `GENOME_FORMAT_VERSION` bump is never the right answer to a derivable value.** Needing one is
   the signal that the value should have been derived.

### Why: biology-faithful cascade

The genome's contract is that it runs **biology's actual cascade, not a modified one**
(`[[feedback_simulate_with_biologys_actual_cascade_not_modified]]`). Biology does not maintain a
sidecar index of its own chromosomes. It re-derives — every read walks the strand. A cell has no
table of contents, no committed digest mirror, no second copy kept in sync.

So "add a cache" is not a neutral engineering choice here; it is a **departure from the cascade the
genome exists to be faithful to**. Every time the design reached for one, the reach itself was the
defect signal.

### "But an LLM needs to read it" is backwards

The remaining justification offered for `manifest.json` is that a reader — typically an LLM — needs
a legible view of the store. That argument inverts the architecture, because **the LLM-readable
surface already exists and is built the admissible way**: `describe()`, the tool schema, the MCP
registry and the C registries are *build-time projections of a single source*, regenerated in a
fixed order and gated so a desync is a red build (ADR-0007's ripple, ADR-0010's lockstep rename).

A reader should call the apparatus, not read a second copy of the data. Shipping a runtime sidecar
for legibility means the reader is trusting an encoding that nothing verifies against the strand —
which is exactly how rc337's digest mirror came to need bounding in the first place. If a legible
view is wanted, derive it on demand through the tool surface; do not persist it.

### CACHE versus WITNESS — the distinction that makes this checkable

Not every stored derivable value is a cache. The store already contains a legitimate counter-example
three fields away from a violating one:

| head field | stored | compared on read | disagreement is |
|---|---|---|---|
| `body_sha256` | yes | **yes** — `genome.py:9407-9412` raises | **caught** |
| `carrier` | yes | derivable, "a pure function of the body" | n/a |
| `n_turns` / `n_chromosomes` | yes | **never** | **silent** |

> **A stored derivable value is admissible IFF something compares it against the strand and
> disagreement is loud. Otherwise it is a cache and this ADR forbids it.**

- A **cache** exists to avoid recomputation. It is *expected to always agree*. If it can disagree
  silently it is a defect, because it reports a fact nothing checked.
- A **witness** exists precisely *to be compared*. Its value comes from the possibility of
  disagreement — the writer's claim set against the reader's finding, with the difference as a
  tamper signal.

`body_sha256` is stored for the same O(1)-append reason the scalars are, and it is honest **because
something compares it**. That is the shape to copy. So the close for a violating field is normally
**verify it, not delete it** — deleting `n_chromosomes` would reintroduce the O(N²) append wall the
whole head-only design exists to avoid, which is a real property, not a convenience.

This is also why the twist/writhe reading does not rescue a bare stored scalar: `Tw` and `Wr` are
*both derived* from one curve and `Lk = Tw + Wr` is a theorem, so nothing can drift. A stored,
uncompared scalar can. The two-perspectives structure is real — writer's claim versus reader's
finding — but you only have it once you actually compute the relation.

### The constructive alternative

The alternative to caching is almost never "pay twice" — it is **reuse work already being done**.
rc342 is the worked example: the derive already parses the manifest, so threading the digest out of
that parse cost nothing, where a second parse cost two opens per scan and broke a ratchet. Look for
the existing traversal before concluding a second encoding is needed.

## Consequences

- **Deriving may be slower, and that is accepted.** A measured CPU cost is not by itself grounds for
  a genome cache; it is grounds for a conversation about where a cache would live *outside* the
  genome, or about whether an existing traversal can carry the value.
- **Reviewers have a bright line.** "Where is the second encoding?" is answerable by inspection. A
  new head field, a new manifest key, or a format bump for a derivable value fails this ADR.
- **The sidecar-dissolution arc is ADR-backed**, not merely tracked.
- **This ADR is genome-scoped.** It does not govern codegen: the four generated registries,
  `_tool_docs` prose, and the Rosetta ledger are build-time projections of a single source,
  regenerated and gated so a desync fails loudly (ADR-0007's ripple, ADR-0010's lockstep rename).
  A build-time projection with a red-build desync gate is not a runtime cache. If that distinction
  ever blurs, it is a separate decision, not an exception claimed under this one.

## Related

- ADR-0003 — C-host standalone; the catalog is derived by scanning the body, never a stored
  plaintext TOC. This ADR names the principle ADR-0003 was already applying.
- ADR-0007 — release engineering; the registry ripple and the down-only ratchets, one of which
  (rc282's open-count) mechanically rejected the cache before a human did.
- ADR-0009 — multi-implementation parity; a derived value must derive identically in every
  projection.
- `[[feedback_simulate_with_biologys_actual_cascade_not_modified]]` — the cascade-identity stance
  this decision follows from.
- `[[project_genome_no_sidecar_dissolution_and_triaxial_hyperhelix]]` — the standing sidecar
  direction, now ADR-backed.
