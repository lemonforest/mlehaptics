# siona

**Siona is a grounded, can't-hallucinate RBS-HDC instrument** — storage + retrieval (k=3 chiral *addressing*) of spectrally-encoded knowledge, built on **[`srmech`](https://pypi.org/project/srmech/)** (Stored-Relationship Mechanism) as its lean math core.

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

The core operation is the **de Bruijn fiber walk**: a body is stored as its minimal-unique-window shape, and recall *walks* that shape from a seed to regenerate the whole sequence — GPU-free, no stored prose, exact when the walk is unique. It is symbol-agnostic (it operates on integer ids), so the same op serves text tokens, DNA bases (de Bruijn graphs are the genome-assembly algorithm), or any discrete stream.

This is the "LM as a k=3 chiral-axis addressing system over a storage substrate" thesis, packaged: srmech is the lean substrate-math; Siona is the addressing/retrieval layer that rides on it.

## Status

- `0.1.0rc1` is **pure-Python** (portable `py3-none-any`); it depends on `srmech>=0.7.4`.
- A C-native de Bruijn accelerator (a `[profile.native]` tier) is a planned follow-on platform-wheel release.
- TestPyPI release-candidates are published first; a clean (non-rc) tag promotes to PyPI.

- Math core: <https://pypi.org/project/srmech/>
- Source / issues: <https://github.com/lemonforest/mlehaptics>

License: GPL-3.0-or-later (same as `srmech`).
