# Calendar systems supported by antikythera-spectral

The package converts between Julian Day and four calendar systems. Each has caveats; this document records them once so a future user reading the bridge JSON understands what they're looking at.

## Gregorian (proleptic)

The modern civil calendar, extended *backward* before its 1582-10-15 introduction (the proleptic Gregorian rule set). For dates before 1582-10-15, the proleptic Gregorian and the actual historical Julian calendar differ; for dates before 1500 CE, the offset is 10 days.

Use `jd_to_gregorian(jd)` if you want a calendrically clean modern-style date for any JD. Use `jd_to_julian_calendar(jd)` if you're working with historical sources whose dates are in the Julian calendar.

Round-trip: `gregorian_to_jd(year, month, day, …, era='CE'|'BCE')` is exact.

## Julian (historical)

The actual calendar in use 45 BCE through 1582-10-15 CE. Differs from proleptic Gregorian by 10–14 days depending on era.

Use `jd_to_julian_calendar(jd)` when reading dates *as they were originally recorded* by historical observers.

## Olympiad

The four-year cycle Greek historians used to date events: "in the third year of the 169th Olympiad." Olympiad I.1 is the date of the first Olympic Games, 776-07-01 BCE proleptic Julian = JD 1438178.0.

The Antikythera mechanism's back dial **physically displays** the Olympiad cycle; Freeth, Jones, Steele & Bitsakis 2008 (*Nature* 454:614) reconstruct the dial layout. Year-in-Olympiad is 1..4.

## Athenian (Attic)

Twelve lunar months, year starting at the first new moon after the summer solstice:

```
Hekatombaion (mid-Jul .. mid-Aug)
Metageitnion
Boedromion
Pyanepsion
Maimakterion
Poseideon  (mid-Dec .. mid-Jan; intercalary slot is "Poseideon II")
Gamelion
Anthesterion
Elaphebolion
Mounichion
Thargelion
Skirophorion (mid-Jun .. mid-Jul)
```

### Caveats (per ADR 0007)

The Attic calendar was **observational** — Athenian magistrates declared the new month after seeing the new moon. Rome's later calendar reforms (45 BCE Julian) and even Athenian intercalation practice introduced systematic deviations from a uniform synodic-month model.

`antikythera-spectral` v0.1.0 returns the Attic month + day from a uniform 29.530588861-day synodic model. Expected ±1-day uncertainty vs. observed Athenian dates.

The intercalary "Poseideon II" month (the 13th month inserted in some years to keep the lunar-year aligned with the solar year) is **not modelled** in v0.1.0; lunar-cycle drift is folded into the year-counter instead of an explicit intercalation rule.

The **archonship name** (e.g. "the year of Eponymos Apollodorus") is the most useful Athenian date marker for historical research, but it requires the canonical archon table (Develin 1989, *Athenian Officials 684-321 B.C.*). v0.1.0 does **not** bundle this table; `archon` is set to `None`. v0.2.0 will add it for the period -510 to -301 BCE; outside that range we will raise `UnknownArchonError` rather than guess.

For research-grade Athenian dates, cross-check against:

- Pritchett, W. K. & Neugebauer, O. (1947). *The Calendars of Athens*.
- Develin, R. (1989). *Athenian Officials 684–321 B.C.*

## ΔT and time-of-day precision

`gregorian_to_jd(year, month, day, hour, minute, second)` returns a JD on the assumption the input is Universal Time. For Hellenistic-era queries, the ~3-hour ΔT uncertainty (see [DELTA_T_MODEL.md](DELTA_T_MODEL.md)) means asking for "noon at -200-09-22" produces a JD that's ±3 hours uncertain at the level of the actual TDB time the ephemeris would use.

This is fine for day-level queries (the kind the Antikythera mechanism actually predicts) and a cause for caution on hour-level queries.
