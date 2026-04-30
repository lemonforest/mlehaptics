"""antikythera-spectral codegen — emit frozen data tables from research/.

Each ``emit_*.py`` script in this directory reads from
``docs/antikythera-maths/research/`` (the SSOT for cycles, gears,
anchors, periods, etc.) and writes JSON / NPZ output into
``../python/antikythera_spectral/_data/``.

The orchestrator ``regenerate.py`` runs every emitter and writes a
``manifest.json`` carrying:

- the package version (matches ``pyproject.toml``),
- the source-commit hash (from ``GIT_COMMIT`` env var, set by
  ``regenerate.py`` from ``git rev-parse HEAD``),
- the per-file SHA-256 sums (so a downstream consumer can verify
  the wheel's data hasn't been tampered with).

Run ``python codegen/regenerate.py`` from this directory's parent
to refresh all data files. CI runs ``test_data_freshness.py`` to
fail the build if the committed JSON / NPZ has drifted from the
research-scaffold source.
"""
