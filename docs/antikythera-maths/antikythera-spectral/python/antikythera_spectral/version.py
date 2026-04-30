"""Version stamp.

Read by ``__init__.py``'s lazy-import path so users can ask for
``antikythera_spectral.__version__`` without paying for the rest of the
package's imports (numpy / skyfield / scipy etc.).

The version string MUST match ``pyproject.toml``'s ``[project].version`` —
the publish workflow's tag-version-check step parses both files and
fails the build on mismatch.
"""

__version__: str = "0.2.0"
