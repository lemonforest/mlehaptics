"""srmech profile loader — Task #199 implementation (ADR-0001).

Loads `srmech_profile.toml` descriptors declared by installed packages
via the ``srmech.profiles`` entry-point group, validates each against
the v1 schema, and exposes the ``srmech.profile(name)`` activation API.

Loader discipline (ADR-0001 §5.5)
---------------------------------
- **Eager enumeration at first srmech import.** Walks
  `importlib.metadata.entry_points(group="srmech.profiles")` once.
  No lazy-deferred discovery.
- **Boundary type-check.** Every profile descriptor is validated
  against the schema. Failures → enumerated-but-not-active; calling
  `srmech.profile(name)` for an invalid profile raises
  `InvalidProfileError` with the schema diagnostic.
- **Smoke-test cache.** Per-profile-version. ``~/.cache/srmech/
  profile_smoke_tests/<name>-<version>.toml``. Cache hit → skip.
  Cache miss / version bump → run; pass → cache + activate; fail →
  enumerated-but-not-active; calling raises ``SmokeTestFailedError``.
- **Bounded resource use.** Loader allocates per-profile structures
  once at enumeration time and reuses them. No reflection in hot
  paths. No eval/exec on profile-author strings.

Public API
----------
- ``list_profiles()`` — dict of profile-name -> ProfileStatus
- ``profile(name)`` — returns an active Profile object
- ``Profile.<bridge_surface>(args)`` — calls profile-declared bridge functions
- ``Profile.catalogs`` — info about registered catalog SSOT
- ``Profile.native`` — info about loaded plugin (if any; plugin tier)

Versioning
----------
This loader speaks ``profile_schema_version = "1.0"`` only. Profiles
declared against ``"2.0"`` etc. are enumerated but marked invalid
with a clear schema-version-mismatch diagnostic.
"""

from __future__ import annotations

import ctypes
import dataclasses
import datetime as _dt
import importlib
import importlib.metadata
import importlib.resources
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover  (py3.10 only)
    import tomli as tomllib  # type: ignore[no-redef]


# ──────────────────────────────────────────────────────────────────────
# Constants — bounded resource limits (JPL Rule 2 analog at Python level)
# ──────────────────────────────────────────────────────────────────────

#: srmech speaks this profile_schema_version. Profiles declared against
#: any other version are rejected at enumeration time with a clear
#: diagnostic. Bump when the v1 schema gets a breaking change.
SUPPORTED_PROFILE_SCHEMA_VERSION: str = "1.0"

#: The entry-point group name. Packages declare
#:   [project.entry-points."srmech.profiles"]
#:   name = "their_package:SRMECH_PROFILE_TOML"
ENTRY_POINT_GROUP: str = "srmech.profiles"

#: Hard cap on enumerated profile count. Defends against denial-of-
#: service via thousands of declared entry points. 64 is far above any
#: plausible real-world deployment.
MAX_ENUMERATED_PROFILES: int = 64

#: Smoke-test cache directory under the user's XDG_CACHE_HOME (Linux),
#: AppData/Local (Windows), or Library/Caches (macOS) by way of
#: Path.home() / ".cache".
_DEFAULT_CACHE_ROOT: Path = Path.home() / ".cache" / "srmech" / "profile_smoke_tests"


# ──────────────────────────────────────────────────────────────────────
# Error types
# ──────────────────────────────────────────────────────────────────────


class ProfileError(Exception):
    """Base class for profile-loader errors."""


class ProfileNotFoundError(ProfileError):
    """Raised when ``srmech.profile(name)`` is called for an
    unknown profile."""


class InvalidProfileError(ProfileError):
    """Raised when a profile is enumerated but its descriptor failed
    schema validation. The message names the failing field / constraint."""


class SmokeTestFailedError(ProfileError):
    """Raised when activating a profile whose smoke test failed (either
    on this load or on a cached prior run that hasn't been invalidated
    by a version bump)."""


class AbiMismatchError(ProfileError):
    """Plugin profile: the loaded native library's abi_version() return
    does not match the profile descriptor's expected_abi_version. The
    plugin is not activated."""


class ProfileSchemaVersionError(InvalidProfileError):
    """The descriptor's profile_schema_version is not one srmech
    supports. Distinct subclass so callers can special-case the
    "I might be too old to load this profile" case."""


# ──────────────────────────────────────────────────────────────────────
# Discovered-profile records
# ──────────────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class ProfileStatus:
    """Public-facing summary of one enumerated profile.

    A profile can be in one of three states:
    - ``ok`` — validated, ready to activate
    - ``invalid`` — descriptor failed schema validation
    - ``smoke_failed`` — descriptor valid but smoke test failed on a
      prior run (cached failure)

    The actual activation runs lazily on ``srmech.profile(name)``.
    """
    name: str
    version: str
    summary: str
    package: str
    status: str  # "ok" | "invalid" | "smoke_failed"
    diagnostic: str = ""


# ──────────────────────────────────────────────────────────────────────
# Schema validation
#
# Pure-Python minimal validator — covers the constraints that matter
# for the loader to refuse a malformed descriptor. Long-tail validation
# (pattern matches, enum values, etc.) is best-effort; we don't ship a
# jsonschema hard-dep just for that.
# ──────────────────────────────────────────────────────────────────────

_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")
_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(rc[0-9]+)?$")
_SCHEMA_VERSION_PATTERN = re.compile(r"^[0-9]+\.[0-9]+$")
_PACKAGE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_DOTTED_CALLABLE_PATTERN = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_.]*:[a-zA-Z_][a-zA-Z0-9_]*$"
)


def _require(condition: bool, msg: str) -> None:
    if not condition:
        raise InvalidProfileError(msg)


def _validate_descriptor(data: Dict[str, Any], source_hint: str) -> None:
    """Validate a parsed `srmech_profile.toml` against the v1 schema.

    Raises :class:`InvalidProfileError` (or subclass) with a clear
    diagnostic on any failure. Returns normally on success.

    `source_hint` is the originating path or entry-point name — used
    in error messages so the failing descriptor is identifiable.
    """
    # ── Top level ──────────────────────────────────────────────────
    _require(isinstance(data, dict),
             f"{source_hint}: top-level must be a TOML table")
    _require("profile_schema_version" in data,
             f"{source_hint}: missing top-level 'profile_schema_version'")
    schema_version = data["profile_schema_version"]
    _require(isinstance(schema_version, str)
             and _SCHEMA_VERSION_PATTERN.match(schema_version),
             f"{source_hint}: profile_schema_version "
             f"{schema_version!r} must match MAJOR.MINOR")
    if schema_version != SUPPORTED_PROFILE_SCHEMA_VERSION:
        raise ProfileSchemaVersionError(
            f"{source_hint}: profile_schema_version "
            f"{schema_version!r} not supported; srmech speaks "
            f"{SUPPORTED_PROFILE_SCHEMA_VERSION!r}. Either bump srmech "
            f"or downgrade the profile's schema version."
        )

    _require("profile" in data and isinstance(data["profile"], dict),
             f"{source_hint}: missing or malformed [profile] section")
    p = data["profile"]

    # ── [profile] required fields ───────────────────────────────────
    for required_field in ("name", "version", "summary", "package",
                           "srmech_requires"):
        _require(required_field in p,
                 f"{source_hint}: [profile] missing required field "
                 f"{required_field!r}")

    name = p["name"]
    _require(isinstance(name, str) and _NAME_PATTERN.match(name),
             f"{source_hint}: [profile].name {name!r} must match "
             f"^[a-z][a-z0-9_-]*$ (lowercase, alphanumeric + dash/underscore)")
    _require(1 <= len(name) <= 64,
             f"{source_hint}: [profile].name length must be 1..64")

    version = p["version"]
    _require(isinstance(version, str) and _VERSION_PATTERN.match(version),
             f"{source_hint}: [profile].version {version!r} must match "
             f"MAJOR.MINOR.PATCH[rcN]")

    summary = p["summary"]
    _require(isinstance(summary, str) and 1 <= len(summary) <= 200,
             f"{source_hint}: [profile].summary must be 1..200 char string")

    package = p["package"]
    _require(isinstance(package, str) and _PACKAGE_PATTERN.match(package),
             f"{source_hint}: [profile].package {package!r} must match "
             f"^[a-z][a-z0-9_]*$")

    srmech_requires = p["srmech_requires"]
    _require(isinstance(srmech_requires, str) and srmech_requires,
             f"{source_hint}: [profile].srmech_requires must be "
             f"non-empty string")

    # ── [profile.catalogs] (optional) ───────────────────────────────
    if "catalogs" in p:
        c = p["catalogs"]
        _require(isinstance(c, dict),
                 f"{source_hint}: [profile.catalogs] must be a table")
        if "attested_root" in c:
            _require(isinstance(c["attested_root"], str),
                     f"{source_hint}: [profile.catalogs].attested_root "
                     f"must be a string")

    # ── [profile.bridge] (optional) ─────────────────────────────────
    if "bridge" in p:
        b = p["bridge"]
        _require(isinstance(b, dict),
                 f"{source_hint}: [profile.bridge] must be a table")
        for fn_name, target in b.items():
            _require(isinstance(target, str)
                     and _DOTTED_CALLABLE_PATTERN.match(target),
                     f"{source_hint}: [profile.bridge].{fn_name} = "
                     f"{target!r} must match 'module.path:callable_name'")

    # ── [profile.native] (optional; plugin tier) ────────────────────
    if "native" in p:
        n = p["native"]
        _require(isinstance(n, dict),
                 f"{source_hint}: [profile.native] must be a table")
        for required_field in ("library", "install_path",
                               "abi_version_function",
                               "expected_abi_version"):
            _require(required_field in n,
                     f"{source_hint}: [profile.native] missing required "
                     f"field {required_field!r}")
        _require(isinstance(n["expected_abi_version"], int)
                 and n["expected_abi_version"] >= 1,
                 f"{source_hint}: [profile.native].expected_abi_version "
                 f"must be a positive integer")

    # ── [profile.interpreted] (reserved; v0.3.0 warns + skips) ──────
    if "interpreted" in p:
        warnings.warn(
            f"{source_hint}: [profile.interpreted] is RESERVED in "
            f"srmech_profile.toml v1.0 (ADR-0001 §5.6 future tier). "
            f"This srmech version does not implement interpreted-runtime "
            f"plugins; the block is ignored. Profile will activate without it.",
            FutureWarning,
            stacklevel=2,
        )


# ──────────────────────────────────────────────────────────────────────
# Discovery — eager enumeration at first import
# ──────────────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class _EnumeratedDescriptor:
    """Internal record held in the loader's enumeration table."""
    name: str
    version: str
    summary: str
    package: str
    raw: Dict[str, Any]  # parsed TOML
    source_hint: str    # path / entry-point name
    status: str         # "ok" | "invalid" | "smoke_failed"
    diagnostic: str     # populated when status != "ok"


# Module-level cache; built once at first _enumerate_profiles() call.
_ENUMERATION: Optional[Dict[str, _EnumeratedDescriptor]] = None

#: Module-level cache of activated profiles by name.
_ACTIVE_PROFILES: Dict[str, "Profile"] = {}


def _resolve_entry_point_toml(ep: importlib.metadata.EntryPoint) -> Path:
    """Resolve an entry point declaring a profile to the on-disk path
    of its ``srmech_profile.toml`` descriptor.

    Three entry-point value forms are supported:

    1. **Package only** (recommended, profile-author boilerplate-free):
       ``chess = "chess_spectral"``. The loader imports the package
       and locates ``srmech_profile.toml`` via
       ``importlib.resources.files(package)``.

    2. **Module attribute pointing at a Path/str** (explicit):
       ``chess = "chess_spectral:_SRMECH_PROFILE_PATH"``. The loader
       resolves the attribute; it must be a ``Path`` or ``str``
       pointing at the descriptor.

    3. **Function returning a Path/str** (for descriptors generated
       at import time, rare): ``chess = "chess_spectral:_get_path"``
       where ``_get_path()`` returns the path. The loader detects
       callables and invokes them with no arguments.

    Phase 1c bug-fix (v0.3.1): v0.3.0 only supported form 2. Adding
    forms 1 + 3 makes the loader compatible with the conventional
    "package name only" entry-point declaration used by every
    real-world Python plugin discovery pattern (pytest, flake8,
    setuptools_scm) without requiring profile authors to add
    boilerplate constants to their ``__init__.py``.
    """
    target = ep.load()

    # Form 1: package-only entry point — locate srmech_profile.toml
    # as a package resource via importlib.resources.
    import types
    if isinstance(target, types.ModuleType):
        # The target IS the package. Look for srmech_profile.toml
        # under its files() tree.
        try:
            resource = (
                importlib.resources.files(target) / "srmech_profile.toml"
            )
        except (TypeError, ModuleNotFoundError) as exc:
            raise InvalidProfileError(
                f"entry-point {ep.name!r} ({ep.value!r}) imported as "
                f"module {target.__name__!r}, but importlib.resources "
                f"could not enumerate package files: {exc}"
            ) from exc
        # importlib.resources returns a Traversable; for filesystem-
        # installed packages it has __fspath__. For zipped imports
        # (rare for installed packages) we fall back to as_file().
        try:
            return Path(str(resource))
        except (TypeError, ValueError) as exc:
            raise InvalidProfileError(
                f"entry-point {ep.name!r} ({ep.value!r}): package "
                f"resource {resource!r} could not be resolved to a "
                f"filesystem path: {exc}"
            ) from exc

    # Form 2: attribute already a Path.
    if isinstance(target, Path):
        return target

    # Form 2: attribute is a string.
    if isinstance(target, str):
        return Path(target)

    # Form 3: attribute is a callable returning a Path/str.
    if callable(target):
        try:
            result = target()
        except Exception as exc:
            raise InvalidProfileError(
                f"entry-point {ep.name!r} ({ep.value!r}) is a callable; "
                f"calling it raised {type(exc).__name__}: {exc}"
            ) from exc
        if isinstance(result, Path):
            return result
        if isinstance(result, str):
            return Path(result)
        raise InvalidProfileError(
            f"entry-point {ep.name!r} ({ep.value!r}) callable returned "
            f"{type(result).__name__}; expected Path or str"
        )

    raise InvalidProfileError(
        f"entry-point {ep.name!r} ({ep.value!r}) resolved to "
        f"{type(target).__name__}; expected a package (module), a Path or "
        f"str attribute pointing at srmech_profile.toml, or a callable "
        f"returning a Path or str"
    )


def _read_descriptor(toml_path: Path, source_hint: str) -> Dict[str, Any]:
    """Read + parse a srmech_profile.toml descriptor."""
    _require(toml_path.exists(),
             f"{source_hint}: profile descriptor {toml_path} does not exist")
    with toml_path.open("rb") as f:
        return tomllib.load(f)


def _enumerate_profiles() -> Dict[str, _EnumeratedDescriptor]:
    """Walk every installed ``srmech.profiles`` entry point + validate.

    Idempotent: builds the enumeration table once on first call and
    returns the cached table thereafter. The cache is a process-
    lifetime singleton — re-enumerating would defeat the eager-at-boot
    discipline (ADR-0001 §5.5).
    """
    global _ENUMERATION
    if _ENUMERATION is not None:
        return _ENUMERATION

    out: Dict[str, _EnumeratedDescriptor] = {}
    entry_points = list(
        importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)
    )

    if len(entry_points) > MAX_ENUMERATED_PROFILES:
        warnings.warn(
            f"srmech: discovered {len(entry_points)} profiles via the "
            f"{ENTRY_POINT_GROUP!r} entry-point group, exceeding the "
            f"hard cap of {MAX_ENUMERATED_PROFILES}. Only the first "
            f"{MAX_ENUMERATED_PROFILES} will be enumerated.",
            RuntimeWarning,
            stacklevel=2,
        )
        entry_points = entry_points[:MAX_ENUMERATED_PROFILES]

    for ep in entry_points:
        source_hint = f"entry-point[{ep.name!r}] @ {ep.value!r}"
        try:
            toml_path = _resolve_entry_point_toml(ep)
            raw = _read_descriptor(toml_path, source_hint)
            _validate_descriptor(raw, source_hint)
        except InvalidProfileError as exc:
            # Pre-name extraction: try to get name from raw even on
            # validation failure, fall back to entry-point name.
            tentative_name = ep.name
            tentative_version = "?"
            tentative_summary = ""
            tentative_package = "?"
            try:
                p = raw["profile"]  # type: ignore[index]
                tentative_name = p.get("name", ep.name)
                tentative_version = p.get("version", "?")
                tentative_summary = p.get("summary", "")
                tentative_package = p.get("package", "?")
            except (NameError, KeyError, TypeError):
                pass
            out[tentative_name] = _EnumeratedDescriptor(
                name=tentative_name,
                version=tentative_version,
                summary=tentative_summary,
                package=tentative_package,
                raw={},
                source_hint=source_hint,
                status="invalid",
                diagnostic=str(exc),
            )
            continue
        except Exception as exc:  # noqa: BLE001
            # Unknown errors during entry-point load — still surface them
            # rather than crashing the host process.
            out[ep.name] = _EnumeratedDescriptor(
                name=ep.name,
                version="?",
                summary="",
                package="?",
                raw={},
                source_hint=source_hint,
                status="invalid",
                diagnostic=f"unexpected loader error: {exc!r}",
            )
            continue

        # Validation passed
        p = raw["profile"]
        out[p["name"]] = _EnumeratedDescriptor(
            name=p["name"],
            version=p["version"],
            summary=p["summary"],
            package=p["package"],
            raw=raw,
            source_hint=source_hint,
            status="ok",
            diagnostic="",
        )

    _ENUMERATION = out
    return out


# ──────────────────────────────────────────────────────────────────────
# Smoke-test cache
# ──────────────────────────────────────────────────────────────────────


def _cache_dir() -> Path:
    """Resolve the smoke-test cache directory. Overridable via the
    SRMECH_PROFILE_CACHE_DIR environment variable for test isolation."""
    override = os.environ.get("SRMECH_PROFILE_CACHE_DIR")
    if override:
        return Path(override)
    return _DEFAULT_CACHE_ROOT


def _cache_path(profile_name: str, profile_version: str) -> Path:
    return _cache_dir() / f"{profile_name}-{profile_version}.toml"


def _read_smoke_cache(profile_name: str, profile_version: str) \
        -> Optional[Dict[str, Any]]:
    """Read the smoke-test cache entry for a profile-version. Returns
    None on cache miss or malformed cache file (treated as miss)."""
    p = _cache_path(profile_name, profile_version)
    if not p.exists():
        return None
    try:
        with p.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _write_smoke_cache(
    profile_name: str,
    profile_version: str,
    *,
    status: str,
    duration_ms: int,
    n_assertions: int,
    failure: str = "",
) -> None:
    """Persist a smoke-test cache entry. Best-effort — failure to write
    just means the test will re-run next time, which is the safe default."""
    from . import __version__ as srmech_version
    p = _cache_path(profile_name, profile_version)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "[smoke_test]",
            f'profile = "{profile_name}"',
            f'profile_version = "{profile_version}"',
            f'srmech_version = "{srmech_version}"',
            f'ran_at = "{_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}"',
            f'status = "{status}"',
            f"duration_ms = {duration_ms}",
            f"n_assertions = {n_assertions}",
        ]
        if failure:
            # Use multi-line TOML literal to avoid quoting headaches.
            escaped = failure.replace('"""', '"""')
            lines.append(f'failure = """{escaped}"""')
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        warnings.warn(
            f"srmech: failed to write smoke-test cache to {p}; "
            f"the test will re-run on next load.",
            RuntimeWarning,
            stacklevel=2,
        )


def _run_smoke_test(descriptor: _EnumeratedDescriptor) -> Tuple[str, str, int]:
    """Run the auto-derived smoke test for a profile.

    Returns ``(status, failure_message, n_assertions)`` where status is
    "passed" or "failed". For v0.3.0 the smoke test is intentionally
    minimal: every declared bridge surface must be importable + callable
    (not invoked yet — that requires synthesized inputs which depend on
    tool_schema declarations not all profiles will have).

    Plugin-profile native loading happens in :class:`Profile`'s
    activation; this function only validates the Python-side
    declarations.
    """
    import time
    p = descriptor.raw["profile"]
    started_ns = time.monotonic_ns()
    n_assertions = 0
    failures: List[str] = []

    # 1. Every bridge surface's target string parses and the named
    #    module/callable can be imported.
    for fn_name, target in p.get("bridge", {}).items():
        n_assertions += 1
        try:
            mod_path, attr_name = target.split(":", 1)
            mod = importlib.import_module(mod_path)
            obj = getattr(mod, attr_name)
            if not callable(obj):
                failures.append(
                    f"bridge surface {fn_name!r} resolved to "
                    f"non-callable {obj!r}"
                )
        except (ImportError, AttributeError, ValueError) as exc:
            failures.append(
                f"bridge surface {fn_name!r} -> {target!r}: {exc!r}"
            )

    # 2. Catalogs section, if present, must point at an existing root.
    catalogs = p.get("catalogs")
    if catalogs and "attested_root" in catalogs:
        n_assertions += 1
        try:
            pkg = importlib.import_module(p["package"])
            pkg_root = Path(pkg.__file__).resolve().parent if pkg.__file__ \
                else None
            if pkg_root is not None:
                catalog_path = pkg_root / catalogs["attested_root"]
                if not catalog_path.exists():
                    failures.append(
                        f"catalog root {catalogs['attested_root']!r} not "
                        f"found at {catalog_path}"
                    )
        except ImportError as exc:
            failures.append(
                f"package {p['package']!r} for catalog root resolution: "
                f"{exc!r}"
            )

    duration_ms = (time.monotonic_ns() - started_ns) // 1_000_000
    if failures:
        return ("failed", "; ".join(failures), n_assertions)
    return ("passed", "", n_assertions)


# ──────────────────────────────────────────────────────────────────────
# Profile object — the activation product
# ──────────────────────────────────────────────────────────────────────


class Profile:
    """An activated profile.

    Created by :func:`profile`. Exposes bridge surfaces as attributes
    and the native plugin (if present) as ``self.native`` — a bound
    ctypes library with the declared symbols available.
    """

    def __init__(
        self,
        name: str,
        version: str,
        summary: str,
        package: str,
        raw: Dict[str, Any],
        source_hint: str,
    ) -> None:
        self.name = name
        self.version = version
        self.summary = summary
        self.package = package
        self._raw = raw
        self._source_hint = source_hint

        # Resolve bridge surfaces once at activation; cache the bound
        # callables. JPL Rule 3 analog at Python level.
        self._bridge: Dict[str, Callable[..., Any]] = {}
        self._resolve_bridge()

        # Register catalog roots if declared.
        self.catalogs: Optional[Dict[str, str]] = self._raw["profile"].get("catalogs")
        self._register_catalogs()

        # Load + bind plugin if declared (plugin tier).
        self.native: Optional[ctypes.CDLL] = None
        self._native_meta: Optional[Dict[str, Any]] = None
        self._maybe_load_native()

    def _resolve_bridge(self) -> None:
        """Import + bind every bridge surface. Failures raise (this
        runs at activation time; the smoke test should have already
        caught import errors, so failures here indicate either a
        smoke-test gap or a runtime environment difference)."""
        for fn_name, target in self._raw["profile"].get("bridge", {}).items():
            mod_path, attr_name = target.split(":", 1)
            mod = importlib.import_module(mod_path)
            self._bridge[fn_name] = getattr(mod, attr_name)

    def _register_catalogs(self) -> None:
        """If [profile.catalogs] declared an attested_root, register
        it into srmech's universal catalog bridge."""
        if not self.catalogs:
            return
        attested_root = self.catalogs.get("attested_root")
        if not attested_root:
            return
        try:
            pkg = importlib.import_module(self.package)
            if pkg.__file__ is None:
                return  # namespace package without __file__; skip
            pkg_root = Path(pkg.__file__).resolve().parent
            catalog_path = pkg_root / attested_root
        except ImportError:
            return  # already caught by smoke test; defensive
        from .amsc.catalog import register_attested_root
        source = self.catalogs.get("source", self.name)
        register_attested_root(catalog_path, source=source)

    def _maybe_load_native(self) -> None:
        """If [profile.native] is declared, load the plugin and verify
        the ABI handshake."""
        n = self._raw["profile"].get("native")
        if not n:
            return

        try:
            pkg_files = importlib.metadata.files(self.package)
        except importlib.metadata.PackageNotFoundError:
            raise InvalidProfileError(
                f"{self._source_hint}: native plugin requires package "
                f"{self.package!r} but it is not installed"
            ) from None

        if pkg_files is None:
            raise InvalidProfileError(
                f"{self._source_hint}: package {self.package!r} has no "
                f"installed-files manifest (cannot locate native lib)"
            )

        lib_basenames = _candidate_lib_names(n["library"])
        lib_path: Optional[Path] = None
        for f in pkg_files:
            if Path(f.name).name in lib_basenames:
                lib_path = Path(f.locate()).resolve()
                if lib_path.exists():
                    break
                lib_path = None

        if lib_path is None:
            raise InvalidProfileError(
                f"{self._source_hint}: native plugin library "
                f"{n['library']!r} not found in package {self.package!r} "
                f"(looked for {lib_basenames})"
            )

        lib = ctypes.CDLL(str(lib_path))

        # ABI handshake.
        abi_fn_name = n["abi_version_function"]
        abi_fn = getattr(lib, abi_fn_name, None)
        if abi_fn is None:
            raise AbiMismatchError(
                f"{self._source_hint}: plugin library exports no "
                f"{abi_fn_name!r} symbol"
            )
        abi_fn.argtypes = []
        abi_fn.restype = ctypes.c_int
        observed = int(abi_fn())
        if observed != n["expected_abi_version"]:
            raise AbiMismatchError(
                f"{self._source_hint}: plugin library reports ABI "
                f"{observed}, profile declares expected_abi_version="
                f"{n['expected_abi_version']!r}"
            )

        # Bind declared symbols.
        for sym_name, sig in n.get("symbols", {}).items():
            sym = getattr(lib, sym_name, None)
            if sym is None:
                raise InvalidProfileError(
                    f"{self._source_hint}: plugin library missing declared "
                    f"symbol {sym_name!r}"
                )
            # ctypes argtype/restype binding happens here in a future
            # iteration; for v0.3.0 the symbol is bound by name only.

        self.native = lib
        self._native_meta = {
            "library_path": str(lib_path),
            "abi_version": observed,
        }

    def __getattr__(self, key: str) -> Any:
        """Bridge surfaces are accessed as profile.<function_name>."""
        if key.startswith("_"):
            raise AttributeError(key)
        if key in self._bridge:
            return self._bridge[key]
        raise AttributeError(
            f"profile {self.name!r} has no bridge surface {key!r}; "
            f"declared bridge surfaces: {sorted(self._bridge.keys())}"
        )

    def __repr__(self) -> str:
        kind = "plugin" if self.native is not None else "simple"
        return (f"<Profile {self.name}@{self.version} ({kind}); "
                f"{len(self._bridge)} bridge surface(s)>")


def _candidate_lib_names(library_base: str) -> Tuple[str, ...]:
    """Generate candidate filenames for a plugin's library across
    platforms. Same pattern srmech uses for its own _native lib."""
    if sys.platform == "win32":
        return (f"{library_base}.dll", f"lib{library_base}.dll")
    if sys.platform == "darwin":
        return (f"lib{library_base}.dylib",)
    return (f"lib{library_base}.so",)


# ──────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────


def list_profiles() -> Dict[str, ProfileStatus]:
    """Return a dict of profile_name -> :class:`ProfileStatus` for
    every enumerated profile. Enumeration is eager + cached;
    subsequent calls return the same view."""
    enum = _enumerate_profiles()
    return {
        name: ProfileStatus(
            name=d.name,
            version=d.version,
            summary=d.summary,
            package=d.package,
            status=d.status,
            diagnostic=d.diagnostic,
        )
        for name, d in enum.items()
    }


def profile(name: str) -> Profile:
    """Activate a profile by name. Returns a :class:`Profile`.

    On first call for a given name:
    - looks up the descriptor in the enumeration table
    - if descriptor status is "invalid", raises :class:`InvalidProfileError`
    - if smoke-test cache is missing for this profile-version, runs
      the smoke test; on failure raises :class:`SmokeTestFailedError`
    - on success, builds a Profile object and caches it

    Subsequent calls return the cached Profile object.
    """
    assert name, "profile name must be non-empty"
    if name in _ACTIVE_PROFILES:
        return _ACTIVE_PROFILES[name]

    enum = _enumerate_profiles()
    if name not in enum:
        raise ProfileNotFoundError(
            f"no profile named {name!r}; enumerated profiles: "
            f"{sorted(enum.keys())}"
        )

    d = enum[name]
    if d.status == "invalid":
        raise InvalidProfileError(
            f"profile {name!r} ({d.source_hint}): {d.diagnostic}"
        )

    # Smoke test cache check.
    cache = _read_smoke_cache(d.name, d.version)
    if cache is not None:
        st = cache.get("smoke_test", {})
        status = st.get("status")
        if status == "passed":
            pass  # cache hit; activate
        elif status == "failed":
            raise SmokeTestFailedError(
                f"profile {name!r} (cache: {_cache_path(d.name, d.version)}): "
                f"{st.get('failure', 'unknown failure')}"
            )
        else:
            cache = None  # malformed cache; re-run

    if cache is None:
        # Cache miss — run the smoke test.
        status, failure, n_assertions = _run_smoke_test(d)
        # We don't have an exact duration captured cleanly here in
        # the cache-write path; recompute.
        _write_smoke_cache(
            d.name, d.version,
            status=status,
            duration_ms=0,  # populated inside _run_smoke_test future iteration
            n_assertions=n_assertions,
            failure=failure,
        )
        if status != "passed":
            raise SmokeTestFailedError(
                f"profile {name!r}: smoke test failed: {failure}"
            )

    prof = Profile(
        name=d.name,
        version=d.version,
        summary=d.summary,
        package=d.package,
        raw=d.raw,
        source_hint=d.source_hint,
    )
    _ACTIVE_PROFILES[name] = prof
    return prof


def reset_for_testing() -> None:
    """Test helper: clear the enumeration + activation caches so a
    test can re-enumerate from scratch. NOT for production use."""
    global _ENUMERATION
    _ENUMERATION = None
    _ACTIVE_PROFILES.clear()


__all__ = [
    "AbiMismatchError",
    "ENTRY_POINT_GROUP",
    "InvalidProfileError",
    "MAX_ENUMERATED_PROFILES",
    "Profile",
    "ProfileError",
    "ProfileNotFoundError",
    "ProfileSchemaVersionError",
    "ProfileStatus",
    "SUPPORTED_PROFILE_SCHEMA_VERSION",
    "SmokeTestFailedError",
    "list_profiles",
    "profile",
    "reset_for_testing",
]
