r"""R-RBS-LM-CONVERTKERNEL (#226) — the {{convert}} QUANTITY+UNIT notation as its own genome-encoded sublanguage kernel:
COMPREHEND `{{convert|VALUE|UNIT|...}}` into a TYPED QUANTITY (value, unit, DIMENSION), never strip it.

WHY this one matters beyond markup hygiene: a {{convert}} is the MASS/COUNT (quantization) determinative written EXPLICITLY
(F1203's load-bearing missing rule). Every convert carries a number AND its physical DIMENSION — length / mass / area /
temperature / … — which is exactly the discrete-count-vs-continuous-mass axis the substrate arc turns on
([[stance_bit_exact_is_phase_locked_cyclic_slots_not_flat]]). So the entity a convert modifies is typed by its dimension
(a river's 2000 ft = a LENGTH; a country's 52419 sqmi = an AREA) — the determinative English otherwise only distributes
weakly (F1201). Comprehending convert HARVESTS that determinative directly from the markup instead of discarding it.

Like understand_markup(F764)/understand_latex, this is a Class-B/F NOTATION grammar (no numeric primitive) that emits a
typed relationship contribution: (entity) --has_<dimension>--> (quantity). srmech 0.9.0rc209. No numpy, no Python abs
builtin, no Counter, no CAD. The `convert` chromosome's gene labels are the DIMENSIONs. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CONVERTKERNEL_...py
"""
import re

# unit token (normalized, lowercased) -> physical DIMENSION (the mass/count determinative class the quantity carries).
_UNITS = {
    "length": "m km cm mm um nm ft mi in yd nmi fathom furlong chain rod league ly pc au mile miles foot feet inch "
              "inches yard yards kilometre kilometer metre meter",
    "area": "m2 km2 cm2 mm2 sqft sqmi sqkm acre acres ha sqyd sqin hectare hectares sqmile sqm",
    "volume": "l ml m3 cm3 ft3 in3 yd3 gal impgal usgal qt pt floz bbl litre liter litres cc",
    "mass": "kg g mg t lb oz st ton lt cwt tonne tonnes pound pounds ounce ounces gram grams kilogram kilograms stone",
    "temperature": "c f k r c-change f-change k-change celsius fahrenheit kelvin",
    "time": "s min h d wk yr ka ma ga sec secs minute minutes hour hours day days week weeks month months year years",
    "speed": "mph kmh kn ms fps knot knots",
    "pressure": "pa kpa mpa bar atm psi mmhg inhg",
    "energy": "j kj mj gj kwh wh cal kcal ev btu",
    "power": "w kw mw gw hp",
    "frequency": "hz khz mhz ghz rpm",
    "angle": "deg rad arcmin arcsec",
    "data": "bit byte kb mb gb tb kib mib gib",
}
UNIT_DIM = {}
for _dim, _toks in _UNITS.items():
    for _u in _toks.split():
        UNIT_DIM[_u] = _dim
DIMENSIONS = tuple(_UNITS.keys())               # the `convert` chromosome's gene labels
_NUM = re.compile(r"[-+±–−]?\d[\d,]*\.?\d*")     # leading number (comma-grouped ok); range/± -> first value
_EXP = re.compile(r"^e(\d+)")                    # 'e6acre' = 10^6 acre: a value multiplier riding the unit token


def understand_convert(argstr):
    r"""Comprehend the args of {{convert|...}} (the string after 'convert|') into a typed quantity. Returns:
        value      : the leading numeric value (float; first of a range), scaled by any e6/e9 unit-prefix
        unit       : the (normalized) source unit token
        to_unit    : the target unit if present, else None
        dimension  : the physical dimension (length/mass/area/temperature/…) — the mass/count determinative class
        is_change  : True for a delta unit (C-change) — a difference, not an absolute quantity
        edge       : ('__entity__', 'has_'+dimension, 'quantity:<value><unit>') — the relationship contribution
    COMPREHEND, not strip: the number, the unit, AND the dimension class survive as a typed node.
    """
    parts = [p.strip() for p in argstr.split("|")]
    if not parts:
        return None
    m = _NUM.search(parts[0])
    value = None
    if m:
        try:
            value = float(m.group(0).replace(",", "").replace("−", "-").replace("–", "-").replace("±", ""))
        except ValueError:
            value = None
    # source unit = first arg after the value that is not an option (k=v) and not pure-numeric (precision digits)
    unit, to_unit, scale = None, None, 1.0
    rest = [p for p in parts[1:] if p and "=" not in p]
    units_seen = []
    for p in rest:
        raw = p.lower()
        ex = _EXP.match(raw)
        if ex:                                  # e6acre -> ×10^6, unit 'acre'
            scale *= 10.0 ** int(ex.group(1)); raw = raw[ex.end():]
        if raw in UNIT_DIM:
            units_seen.append(raw)
        elif raw.rstrip("2") + "2" == raw and (raw in UNIT_DIM):
            units_seen.append(raw)
    if units_seen:
        unit = units_seen[0]
        to_unit = units_seen[1] if len(units_seen) > 1 else None
    if value is not None:
        value *= scale
    dim = UNIT_DIM.get(unit)
    is_change = bool(unit and unit.endswith("-change"))
    qid = None
    if value is not None and unit:
        qv = int(value) if value == int(value) else value
        qid = f"quantity:{qv}{unit}"
    edge = ("__entity__", "has_" + dim, qid) if (dim and qid) else None
    return {"value": value, "unit": unit, "to_unit": to_unit, "dimension": dim,
            "is_change": is_change, "edge": edge}


if __name__ == "__main__":
    SAMPLES = ["15|C|F", "-40|C|F", "2000|ft|m", "52419|sqmi|km2|abbr=out|sp=us", "10|C-change|0",
               "22|e6acre|km2", "5|mi|km|0|adj=on", "56|in|mm", "1,200|kg|lb", "3.5|GW|hp"]
    print("=== CONVERTKERNEL — comprehend {{convert}} into a typed quantity (the mass/count determinative) ===\n")
    for s in SAMPLES:
        r = understand_convert(s)
        print(f"  {{{{convert|{s}}}}}")
        print(f"     value={r['value']}  unit={r['unit']}  to={r['to_unit']}  DIMENSION={r['dimension']}"
              f"{'  (Δ change)' if r['is_change'] else ''}")
        print(f"     edge: {r['edge']}\n")
