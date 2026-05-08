"""Attested data tree for the v0.25.0 collector framework.

Each subdirectory is one attested source: descriptor TOML +
JSON Schema + committed NDJSON. The framework discovers
descriptors at runtime by walking this directory.

Empty ``__init__.py`` ensures scikit-build-core / hatchling
include the data files in built wheels.
"""
