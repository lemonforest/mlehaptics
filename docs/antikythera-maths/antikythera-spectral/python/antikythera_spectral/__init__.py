"""antikythera-spectral — HDC encoder + Pyodide bridge for the Antikythera mechanism.

v0.1.0rc1 ships only the version stamp; bridge / encoder / facades land in
subsequent phases of the v0.1.0 release branch.

Public-API surface (will fill in as phases ship):

    antikythera_spectral.bridge        -- 28-method Pyodide bridge (§5 of plan)
    antikythera_spectral.encoder       -- HDC encoder facade
    antikythera_spectral.decoder       -- HDC decoder facade
    antikythera_spectral.dials         -- dial / cycle accessor
    antikythera_spectral.dates         -- 4-calendar conversion
    antikythera_spectral.visibility    -- heliacal rising / setting
    antikythera_spectral.eclipses      -- frozen-data accessor
    antikythera_spectral.eclipses_search -- sky-driven eclipse enumeration
    antikythera_spectral.operator      -- §11.6.16 workflow simulation
    antikythera_spectral.compare       -- DE-kernel + model comparators
    antikythera_spectral.reconstructions -- Freeth / Wright / Price comparator
    antikythera_spectral.whatif        -- arbitrary-gear-ratio re-encoder
    antikythera_spectral.archaeology   -- fragment-keyed gear inventory
    antikythera_spectral.goalyear      -- Babylonian Goal-Year overlay
    antikythera_spectral.animation     -- time-series state export
    antikythera_spectral.hypotheses    -- H-battery facade

See the planning document at
``docs/antikythera-maths/ANTIKYTHERA_SPECTRAL_PYPI_PLAN_v0.1.0.md`` for the
phase-by-phase rollout plan.
"""

from __future__ import annotations

from antikythera_spectral.version import __version__

__all__ = ["__version__"]
