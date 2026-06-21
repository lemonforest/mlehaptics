"""Single source of truth for srmech's version string.

The version is also declared in ``pyproject.toml``; both must agree.
The ``srmech-publish.yml`` workflow grep-asserts agreement at tag time.
"""

__version__ = "0.9.0rc16"
