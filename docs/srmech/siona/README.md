# siona

**`siona` is a co-name for [`srmech`](https://pypi.org/project/srmech/)** (Stored-Relationship Mechanism). It is a thin packaging alias — installing `siona` installs `srmech`, and `import siona` resolves to exactly the same objects as `import srmech`.

```bash
pip install siona      # pulls in srmech as its only dependency
```

```python
import siona
print(siona.__version__)               # == srmech.__version__

from siona.amsc import cascade         # same module object as srmech.amsc.cascade
cascade.chiral_flip([1, 2, 3])         # -> [3, 2, 1]
```

`siona` and `srmech` are interchangeable import names for one codebase. There is **no forked logic** here: the native C library, the 14-class A–N primitive vocabulary, the QM/QFT/SM operations layer, the AMSC provenance framework, the signal-processing surface, and the tool-schema all live in `srmech`, which remains the single source of truth. Every `srmech.*` submodule is mirrored under `siona.*`.

- Canonical package: <https://pypi.org/project/srmech/>
- Source / issues: <https://github.com/lemonforest/mlehaptics>

License: GPL-3.0-or-later (same as `srmech`).
