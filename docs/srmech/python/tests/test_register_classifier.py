"""Unit tests for srmech.amsc.gap_suggester register_classifier /
register_probes — the cross-package decoupling APIs added in Task #197
Phase 3 (Deviation #1 resolution).

The classifier (``classify_dynamical_regime``) and probes roster
(``REGIME_PROBES``) live in ephemerides-spectral's ``_research/``
subpackage, not in srmech. Pre-Phase-3 the suggester resolved them
via in-package relative imports; post-Phase-3 the suggester relies on
downstream packages PUSHING the modules via these register APIs at
package-import time.

These tests:
* Confirm the register APIs accept arbitrary module-shaped objects
  (we use ``types.SimpleNamespace`` stubs, not real ephemerides
  modules — srmech tests must not depend on ephemerides).
* Confirm calling :func:`suggest_gap_collections` without registration
  raises a clear ``RuntimeError`` naming the missing register API.
* Confirm re-registration replaces the previous module (last-
  registered wins) without raising.
* Confirm idempotency: registering the same module twice doesn't
  blow up state.
"""
from __future__ import annotations

import types

import pytest

from srmech.amsc import gap_suggester


@pytest.fixture(autouse=True)
def _reset_registry():
    """Reset the registry before AND after every test so order doesn't
    matter and tests don't pollute each other.
    """
    gap_suggester._registered_classifier = None
    gap_suggester._registered_probes = None
    yield
    gap_suggester._registered_classifier = None
    gap_suggester._registered_probes = None


def _stub_classifier_module(*, regime_label: str = "stub_regime",
                            cal_ratio: float = 0.1,
                            ood: bool = False) -> types.SimpleNamespace:
    """Build a classifier-module stub matching the contract the
    suggester reads at call time."""
    def classify_dynamical_regime(feature_vector, *, ood_threshold):  # noqa: ARG001
        return {
            "nearest_regime": {"regime_label": regime_label},
            "calibration_ratio": cal_ratio,
            "out_of_distribution": ood,
        }
    return types.SimpleNamespace(
        classify_dynamical_regime=classify_dynamical_regime,
    )


def _stub_probes_module(probes=None) -> types.SimpleNamespace:
    """Build a probes-module stub matching the contract."""
    if probes is None:
        probes = []
    return types.SimpleNamespace(REGIME_PROBES=probes)


def _stub_probe(name: str, expected_regime=None, ood_expected: bool = False,
                feature=None):
    """Build a single probe matching the suggester's per-probe
    contract: .name, .expected_regime, .ood_expected, .feature_vector()."""
    if feature is None:
        feature = [0.0] * 7
    return types.SimpleNamespace(
        name=name,
        expected_regime=expected_regime,
        ood_expected=ood_expected,
        feature_vector=lambda: feature,
    )


# ──────────────────────────────────────────────────────────────────────
# register_classifier
# ──────────────────────────────────────────────────────────────────────


def test_register_classifier_sets_registry_state():
    stub = _stub_classifier_module()
    result = gap_suggester.register_classifier(stub)
    assert result == {"ok": True, "module": repr(stub)}
    assert gap_suggester._registered_classifier is stub


def test_register_classifier_replaces_on_re_registration():
    """Last-registered wins — re-registering replaces the prior module."""
    stub_a = _stub_classifier_module(regime_label="A")
    stub_b = _stub_classifier_module(regime_label="B")
    gap_suggester.register_classifier(stub_a)
    gap_suggester.register_classifier(stub_b)
    assert gap_suggester._registered_classifier is stub_b


def test_register_classifier_idempotent_same_module():
    """Registering the same module twice doesn't blow up state."""
    stub = _stub_classifier_module()
    gap_suggester.register_classifier(stub)
    gap_suggester.register_classifier(stub)
    assert gap_suggester._registered_classifier is stub


# ──────────────────────────────────────────────────────────────────────
# register_probes
# ──────────────────────────────────────────────────────────────────────


def test_register_probes_sets_registry_state():
    stub = _stub_probes_module()
    result = gap_suggester.register_probes(stub)
    assert result == {"ok": True, "module": repr(stub)}
    assert gap_suggester._registered_probes is stub


def test_register_probes_replaces_on_re_registration():
    stub_a = _stub_probes_module([_stub_probe("alpha")])
    stub_b = _stub_probes_module([_stub_probe("beta")])
    gap_suggester.register_probes(stub_a)
    gap_suggester.register_probes(stub_b)
    assert gap_suggester._registered_probes is stub_b


# ──────────────────────────────────────────────────────────────────────
# suggest_gap_collections — error paths when not registered
# ──────────────────────────────────────────────────────────────────────


def test_suggest_raises_runtime_error_when_classifier_missing():
    """Calling without a registered classifier raises a clear
    actionable error naming the register API."""
    # probes registered, classifier missing
    gap_suggester.register_probes(_stub_probes_module())
    with pytest.raises(RuntimeError, match="no classifier registered"):
        gap_suggester.suggest_gap_collections(descriptors={})


def test_suggest_raises_runtime_error_when_probes_missing():
    """Calling without registered probes raises a clear actionable
    error."""
    gap_suggester.register_classifier(_stub_classifier_module())
    with pytest.raises(RuntimeError, match="no probes registered"):
        gap_suggester.suggest_gap_collections(descriptors={})


def test_suggest_runtime_error_names_register_api():
    """The error message guides the consumer to the right register
    API call."""
    gap_suggester.register_probes(_stub_probes_module())
    try:
        gap_suggester.suggest_gap_collections(descriptors={})
    except RuntimeError as exc:
        assert "register_classifier" in str(exc)
    else:
        pytest.fail("expected RuntimeError")


# ──────────────────────────────────────────────────────────────────────
# suggest_gap_collections — happy path with stubs
# ──────────────────────────────────────────────────────────────────────


def test_suggest_runs_end_to_end_with_stubs():
    """End-to-end smoke: stubbed classifier + stubbed probes +
    explicit descriptors map → returns the expected result shape."""
    probe_surprise = _stub_probe(
        "alpha", expected_regime=None, ood_expected=False
    )
    gap_suggester.register_classifier(
        _stub_classifier_module(
            regime_label="stable", cal_ratio=0.42, ood=False
        )
    )
    gap_suggester.register_probes(_stub_probes_module([probe_surprise]))

    result = gap_suggester.suggest_gap_collections(
        ood_threshold=0.85,
        descriptors={},  # explicit empty -> no candidate matching
    )
    assert result["ok"] is True
    assert result["n_probes"] == 1
    # Surprise probe (expected_regime=None, ood_expected=False) →
    # always counts as a gap.
    assert result["n_gaps"] == 1
    assert result["suggestions"][0]["probe_name"] == "alpha"
    assert result["suggestions"][0]["gap_kind"] == "surprise"


def test_suggest_with_no_probes_is_zero_gaps():
    """Empty probe roster → zero gaps, empty suggestions."""
    gap_suggester.register_classifier(_stub_classifier_module())
    gap_suggester.register_probes(_stub_probes_module([]))
    result = gap_suggester.suggest_gap_collections(descriptors={})
    assert result["n_probes"] == 0
    assert result["n_gaps"] == 0
    assert result["suggestions"] == []


# ──────────────────────────────────────────────────────────────────────
# Public API surface
# ──────────────────────────────────────────────────────────────────────


def test_register_apis_in_module_all():
    assert "register_classifier" in gap_suggester.__all__
    assert "register_probes" in gap_suggester.__all__
