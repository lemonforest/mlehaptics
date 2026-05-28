# siona

**`siona` is a co-name for [`srmech`](https://pypi.org/project/srmech/)** (Stored-Relationship Mechanism). It is a **metadata-only metapackage**: it ships no code of its own — its only job is to pull in `srmech` (`>=0.4.4`), whose wheel bundles the `import siona` alias. After install, `import siona` resolves to exactly the same objects as `import srmech`.

```bash
pip install siona      # installs srmech>=0.4.4; the alias comes from srmech's wheel
```

```python
import siona
print(siona.__version__)               # == srmech.__version__

from siona.amsc import cascade         # same module object as srmech.amsc.cascade
cascade.chiral_flip([1, 2, 3])         # -> [3, 2, 1]
```

`siona` and `srmech` are interchangeable import names for one codebase. There is **no forked logic** anywhere — the native C library, the 14-class A–N primitive vocabulary, the QM/QFT/SM operations layer, the AMSC provenance framework, the signal-processing surface, and the tool-schema all live in `srmech`, which remains the single source of truth. The `siona/` package (which mirrors every `srmech.*` submodule under `siona.*`) is shipped **inside the srmech wheel** from srmech v0.4.4 onward, so `pip install srmech` alone already gives you `import siona`. This metapackage exists only so that `pip install siona` resolves to the same place.

> **Why metadata-only?** If both `siona` and `srmech` shipped a `siona/` directory, installing them together would collide on disk. Keeping `siona/` solely in the srmech wheel means there is exactly one owner of the path, so `pip install srmech siona` is conflict-free.

- Canonical package: <https://pypi.org/project/srmech/>
- Source / issues: <https://github.com/lemonforest/mlehaptics>

License: GPL-3.0-or-later (same as `srmech`).
