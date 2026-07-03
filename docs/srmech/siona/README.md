# siona

**Siona is a grounded RBS-HDC instrument** — storage + retrieval (k=3 chiral *addressing*) of spectrally-encoded knowledge, built on **[`srmech`](https://pypi.org/project/srmech/)** (Stored-Relationship Mechanism) as its lean math core.

> **On hallucination (the honest claim):** every Siona emission is a *read of stored relationships*, and
> when the read is uncertain the cascade **says so** — a calibrated honest-STOP ("I'm not sure") instead of
> a confident guess, and honest-OPEN instead of an invented answer (it reports its confidence, not a guess;
> gaps → ask, not fabricate). This is a different failure class from current-generation LLM hallucination
> (free-running confabulation from a generative sampler): Siona can still *err* — a translation kernel can
> mis-ground, a homograph can select the wrong sense — but such errors are **traceable mis-reads of stored
> content**, auditable back to the relationship that produced them, never fabrications from nothing.

> **Un-mirror note (0.1.0rc1):** earlier `siona` releases (≤ 0.0.4) were a metadata-only *co-name alias* for `srmech` — `import siona` resolved to `import srmech`. That alias has been retired (srmech removed the in-wheel `siona` alias). **`siona` is now its own package**: the inference layer, not a second name for the math core. `srmech` remains the single source of truth for the 14-class A–N vocabulary, the Klein-4 HDC, and the native library; `siona` *depends on it* and adds the recall/inference surface on top.

```bash
pip install siona      # pulls srmech (the math core) + registers the `siona` srmech profile
```

## What it is

Siona is a **srmech profile plugin**: installing it registers a `siona` entry-point in srmech's `srmech.profiles` group, so

```python
import srmech
prof = srmech.profile("siona")     # discover + ABI/smoke-check + activate

import siona
toks = siona.walk(ids, k)          # de Bruijn fiber walk — reconstruct a sequence from its shape
body = siona.recall(title, instrument_path, index_path)   # full-body recall by title (walk an RBS-HDC instrument)
```

The core operation is the **de Bruijn fiber walk**: a body is stored as its sequence shape (the relationships — which token follows which), and recall *walks* that shape from a seed to regenerate the whole sequence — GPU-free, no stored prose, exact when the walk is unique. It is symbol-agnostic (it operates on integer ids), so the same op serves text tokens, DNA bases (de Bruijn graphs are the genome-assembly algorithm), or any discrete stream. The store holds the **fiber** (the sequence); a token's Klein-4 HV is a deterministic *projection* recomputed on demand at inference, never persisted per position.

This is the "LM as a k=3 chiral-axis addressing system over a storage substrate" thesis, packaged: srmech is the lean substrate-math; Siona is the addressing/retrieval layer that rides on it.

## Status

- `0.1.0rc1` is **pure-Python** (portable `py3-none-any`); it depends on `srmech>=0.8.1` (the live MIT-licensed math core).
- Recall rides the loose RBS-HDC instrument (an NDJSON of per-body shapes + a title→offset index). A single-file **native srmech genome** of the body corpus (via `srmech.amsc.genome`), a C-native de Bruijn accelerator (a `[profile.native]` tier), and error-correcting recall (`klein4_triality_cycle`) are follow-on releases. The native-genome path is gated on two srmech format fixes — bit-packed leaves (the genome stores each 2-bit Klein-4 lane as a full byte → 4× bloat) and a non-quadratic high-chromosome pack (see the research subtree's UPSTREAM_NOTES §55).
- TestPyPI release-candidates are published first; a clean (non-rc) tag promotes to PyPI.

- Math core: <https://pypi.org/project/srmech/>
- Source / issues: <https://github.com/lemonforest/mlehaptics>

License: MIT (same as `srmech`).

## The interactive session (`siona` at your shell)

```
$ siona
siona 0.1.0rc1 — board: english
ready — 355 tools grounded. every line is one turn; 'exit' or Ctrl-D to leave.
siona> remember that water boils at 100 celsius
[siona.remember] noted (1 items)
siona> compute the gcd of the boiling point of water and 48
[srmech] gcd(100, 48) = 4 [operand [100] resolved from: "that water boils at 100 celsius"]
siona> ingest the kernel fahrenheit is celsius times 9 over 5 plus 32
[siona.remember] noted (2 items)
siona> water boils at what fahrenheit
[siona.answer] 212 fahrenheit (EXACT: (100*9 + 32*5)/5 = 212/1, reduced via srmech gcd)
siona> siona what can you do
[siona.help] my commands (8, from my live schema): remember, recall, forget, show, define, continue_text, help, answer
```

Every `[srmech]` line is a **real, natively-dispatched srmech operation** selected by grounding against the
live `tool_schema` and executed — not a template. Boards: `--board english` (default) | `bislama` (the
UDHR-attested board) | `merged` (bilingual code-switching) | any board TOML path.

## The same loop as a library (`siona.infer`)

```python
import siona
s = siona.Session()                      # registers siona's own tools into srmech's live tool_schema registry
s.turn("siona remember that water boils at 100 celsius")
s.turn("siona ingest the kernel fahrenheit is celsius times 9 over 5 plus 32")
s.turn("compute the gcd of the boiling point of water and 48")
#  -> gcd(100, 48) = 4   [operand [100] resolved from: "water boils at 100 celsius"]
s.turn("siona water boils at what fahrenheit")
#  -> 212 fahrenheit (EXACT: (100*9 + 32*5)/5 = 212/1, reduced via srmech gcd)
```

One loop, two surfaces, one memory: utterances route by **declared operator frames + operand shape**
(no similarity thresholds), ground against srmech's **live** `tool_schema` (order-carrying encoding —
never a bag), drive real srmech ops via **signature-fit** on typed parameters, and read results into a
**never-compacted working memory**. A turn may reference a value remembered in an earlier turn, and
ingested **knowledge kernels** compose answers **exact-rationally** (integer num/den, srmech `gcd`
reduction — no floats). `siona what can you do` answers from the live registered schema
(self-introspection).

## Language boards (`siona.boards`)

The substrate is **byte/glyph** — every word of every script byte-composes to its vector
(script-agnostic; anagram-distinct). Intent operators (`what / remember / compute / …`) live in
per-language **board profiles** (`Board`, `load_board` TOML descriptors): **English is board #1, not
the architecture.** The shared-invariant layer above boards follows the Rosetta architecture — of
which ni-Vanuatu sand drawing is a living ~80-language exemplar (reached dignity-first as an attested
structural exemplar and pointer; the tradition's content is held by the Ni-Vanuatu community).

**Lean wheel, distributed kernels.** The **wheel** stays pure mechanism — no corpora bundled inside
it — so the install is small and knowledge loads by path at runtime. But knowledge **kernels are
distributed**, as attested **companion data artifacts** alongside the package (e.g. the sparse
Laplacian-encoded smallwiki kernel). Redistribution is license-compliant *by construction*: a
CC-BY-SA source (the Wikipedia data dump) may be redistributed with attribution, and every acquired
fact in a Siona kernel carries a **Mathematical Provenance Record** (MPR) — source URL, license,
retrieval time, and the exact record's SHA-256 — which **is** that attribution, at dataset granularity
today and per-record when a citation needs it directly. The research notebooks live in the
[mlehaptics](https://github.com/lemonforest/mlehaptics) repo (Read the Docs).
