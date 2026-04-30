# ADR 0007: Athenian-calendar conversion fidelity

**Status:** Accepted (2026-04-29)

## Context

The Antikythera mechanism's back dial uses the Olympiad cycle, but ancient Greek users would have spoken about dates using the Athenian (Attic) calendar — twelve lunar months, year starting at the first new moon after the summer solstice, archonship year (e.g. "the year of Eponymos Apollodorus").

Three components matter:

1. **Lunar month name + day** — derivable from a uniform synodic-month model with ±1-day error vs. observed Athenian dates.
2. **Intercalary "Poseideon II"** — the 13th lunar month inserted in some years to keep the lunar year aligned with the solar year. Athenian intercalation was non-systematic.
3. **Archonship year** — the *most useful* date marker for historical research, but requires the canonical archon list (Develin 1989 covers -510 to -301 BCE; gaps and disputed reigns outside that period).

## Decision

v0.1.0 returns:

- ✅ Attic month name + day (uniform synodic-month model; ±1-day caveat documented).
- ❌ Intercalary "Poseideon II" — not modeled; lunar drift folded into year-counter.
- ❌ Archon name — `archon: None`; the Develin 1989 table is **not bundled**.

v0.2.0 will add the archon table for -510 to -301 BCE; outside that range we will raise `UnknownArchonError` rather than guess.

## Consequences

- Historians using `jd_to_athenian` for v0.1.0 get the lunar-month structure but must look up archonship from external sources.
- The `approximation_note` field in the response makes the limit explicit.
- v0.2.0 archon-table addition is a non-breaking minor-version bump (adds a field; doesn't remove or rename).

## Alternatives considered

- **Bundle Develin 1989 in v0.1.0.** Rejected on scope grounds — the archon table is a multi-month digitisation effort with disputed-reign judgement calls; defer to v0.2.
- **Use a less authoritative archon list.** Rejected — we'd ship wrong dates rather than honest "we don't know."
- **Refuse to answer Athenian queries entirely.** Rejected — the Attic-month structure is genuinely useful even without the archon name.

## References

- Pritchett, W. K. & Neugebauer, O. (1947). *The Calendars of Athens*.
- Develin, R. (1989). *Athenian Officials 684–321 B.C.*
