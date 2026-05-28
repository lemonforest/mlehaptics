"""``python -m srmech`` entry — delegates to :func:`srmech.cli.main`.

Adding this module makes ``python -m srmech status ...`` work as
documented in the v0.4.6rc2 introspection spec, even when the
console-script entry point isn't on PATH (the common case in
editable installs / source-tree development).
"""

from __future__ import annotations

import sys

from .cli import main


if __name__ == "__main__":
    sys.exit(main())
