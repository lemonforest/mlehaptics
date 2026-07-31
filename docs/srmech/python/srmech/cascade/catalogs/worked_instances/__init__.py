"""Worked-instance descriptors — a named cascade run, declared end to end.

A worked instance is not an op and not a class: it is a *specific* composition
recorded as a descriptor — a name, a purpose, and the ordered ``ops`` it runs —
so the claim it demonstrates can be re-executed rather than merely read.
``triality_s3_klein4.toml`` is the shipped one: the S3 outer-automorphism /
Klein-4 chirality worked instance.

``tests/test_ssot_coherence_scan.py`` is the consumer — it checks every
``*.toml`` here is well-formed (name / purpose / ops) and that every op named
resolves — and it ratchets the count, so a new worked instance is a conscious
bump rather than a silent addition.

Moved here from ``srmech/amsc/_research/worked_instances/`` by ADR-0010's first
execution slice (rc364). The ``__init__.py`` marker is new: this directory
previously shipped only because both build backends copy the package tree
wholesale. That worked, but it rested on a heuristic rather than on a
declaration — and rc364 exists because the same class of assumption had already
cost two alias descriptors their place in the wheel. The three sibling catalog
directories all carry a marker now.
"""

from __future__ import annotations

__all__: list = []
