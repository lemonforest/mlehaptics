r"""R-RBS-LM-CHEMKERNEL (#226) — the <ce>/<chem> (mhchem) REACTION notation as its own genome-encoded sublanguage
kernel: COMPREHEND a chemical/nuclear reaction into a REACTION GRAPH (species = nodes, reactant->product = edges),
never strip it.

WHY it's the same shape as the others: a reaction `2 Na + 2 H2O -> 2 NaOH + H2` IS a relationship graph — the species
are NODES, the arrow is a typed EDGE (each reactant --reacts_to--> each product), with stoichiometric coefficients and
arrow CONDITIONS (catalyst / temperature / — for nuclear — decay mode + half-life) as edge annotations. A nuclear decay
chain `^{226}_{88}Ra ->[β-][42.2 min] ^{227}_{89}Ac` is the same: nuclide nodes + decays_to edges. So understand_chem
is a NOTATION->relationship-graph translator, sibling to understand_latex / understand_convert / understand_markup.

This also closes the LATEXKERNEL's now-#1 blind spot: `\ce{...}` nested inside <math> (mhchem-in-TeX) — sublanguages
nest, and the router (#225) dispatches <math>-with-\ce to this kernel. Class-B/F FORM grammar (no numeric primitive).
srmech 0.9.0rc209. No numpy, no Python abs builtin, no Counter, no CAD. The `chem` chromosome's gene labels are the
reaction-form classes. Run:
  /tmp/srmech_v/venv/bin/python3 docs/srmech/rbs_lm_research/R-RBS-LM-CHEMKERNEL_...py
"""
import re

# the `chem` chromosome's FORM classes (gene labels).
CHEM_FORM_CLASSES = ("species", "coefficient", "reaction_arrow", "equilibrium_arrow", "decay_arrow",
                     "condition", "charge", "nuclide", "state_phase")
# arrow token -> (canonical reltype, reverse?) ; longest-first so '<=>' beats '<-' etc (handled by the alternation order)
_ARROW = re.compile(r"(<=>>|<<=>|<=>|<->|-{2,}>|->|<-|⟶|→|⇌)((?:\[[^\]]*\])*)")
_NUCLIDE = re.compile(r"\^\{?(\d+)\}?_\{?(\d+)\}?\s*\\?([A-Za-z]+)")   # ^{A}_{Z}El
_COEFF = re.compile(r"^\s*(\d+)\s+(?=[A-Za-z\^\[\\])")                 # leading stoichiometric coefficient
_STATE = re.compile(r"\((s|l|g|aq|v)\)$", re.I)


def _reltype(arrow, nuclear):
    if arrow in ("<=>", "<->", "<=>>", "<<=>", "⇌"):
        return "equilibrium"
    return "decays_to" if nuclear else "reacts_to"


def _norm_species(s):
    r"""normalize one species token to a graph node id: nuclide -> 'El-A'; molecule -> compact formula with charge."""
    s = s.strip()
    m = _NUCLIDE.match(s)
    if m:
        return f"{m.group(3)}-{m.group(1)}"                            # ^{226}_{88}Ra -> Ra-226
    s = _STATE.sub("", s).strip()                                     # drop a trailing (s)/(l)/(g)/(aq)
    s = re.sub(r"\^\{?(\d*[+-])\}?", r"\1", s)                        # charge ^{+}/^{2-} -> trailing +/2-
    s = s.replace("\\", "").replace("{", "").replace("}", "")        # drop braces/backslashes
    s = re.sub(r"\s+", "", s)                                         # collapse internal spaces (H2 O -> H2O)
    return s


def _species_list(seg):
    r"""split one side of a reaction into (coefficient, node) species, splitting on top-level ' + '."""
    out = []
    for part in re.split(r"\s\+\s|(?<=[)\]0-9a-z+-])\+(?=[A-Z\^\d\\\[])", seg):
        part = part.strip()
        if not part:
            continue
        coef = 1
        cm = _COEFF.match(part)
        if cm:
            coef = int(cm.group(1)); part = part[cm.end():]
        node = _norm_species(part)
        if node and re.search(r"[A-Za-z]", node):
            out.append((coef, node))
    return out


def understand_chem(src):
    r"""Comprehend an mhchem <ce> reaction into a reaction graph. Returns:
        species   : ordered unique species nodes (molecules / ions / nuclides)
        reactions : [{reactants:[(coef,node)], products:[(coef,node)], reltype, conditions:[...]}]
        edges     : [(reactant_node, reltype, product_node, condition_str)] — the typed reaction relationships
        is_nuclear: True if any nuclide / decay notation is present
    COMPREHEND, not strip: every species is a node; the arrow (+ its conditions) is the typed edge.
    """
    s = src.replace("\\ ", " ").replace("\\,", " ").replace("\\;", " ").replace("\\quad", " ")
    s = re.sub(r"\\ce\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", r"\1", s)   # unwrap nested \ce{...}
    s = s.replace("\\longrightarrow", "->").replace("\\rightarrow", "->").replace("\\to", "->")
    s = s.replace("\\longleftrightarrow", "<->").replace("\\rightleftharpoons", "<=>")
    s = re.sub(r"\\(uparrow|downarrow|gas|sld)", " ", s)              # phase markers (gas evolved / precipitate)
    is_nuclear = bool(_NUCLIDE.search(s) or re.search(r"\\(alpha|beta|gamma)\b", s))

    arrows = list(_ARROW.finditer(s))
    reactions, edges, species, seen = [], [], [], set()
    if not arrows:                                                    # a bare formula list, no reaction
        for _c, node in _species_list(s):
            if node not in seen:
                seen.add(node); species.append(node)
        return {"species": species, "reactions": [], "edges": [], "is_nuclear": is_nuclear}

    bounds = [0] + [a.end() for a in arrows]
    starts = [a.start() for a in arrows] + [len(s)]
    segments = [s[bounds[k]:starts[k]] for k in range(len(bounds))]    # species groups between arrows
    for k, a in enumerate(arrows):
        left = _species_list(segments[k])
        right = _species_list(segments[k + 1])
        arrow = a.group(1)
        conds = re.findall(r"\[([^\]]*)\]", a.group(2) or "")
        conds = [re.sub(r"[\\{}]", "", c).strip() for c in conds if c.strip()]
        rt = _reltype(arrow, is_nuclear)
        reactions.append({"reactants": left, "products": right, "reltype": rt, "conditions": conds})
        cstr = "|".join(conds)
        for _cr, r in left:
            for _cp, p in right:
                edges.append((r, rt, p, cstr))
        for _c, node in left + right:
            if node not in seen:
                seen.add(node); species.append(node)
    return {"species": species, "reactions": reactions, "edges": edges, "is_nuclear": is_nuclear}


if __name__ == "__main__":
    SAMPLES = [
        r"2 Na \ + \ 2 H2O \ \longrightarrow \ 2 NaOH \ + \ H2 \uparrow",
        r"2 Na \ + \ 2 C2H2 \ ->[\ce{150 \ ^{o}C}] \ 2 NaC2H \ + \ H2",
        r"LiR \ + \ Ni(CO)4 \ \longrightarrow Li^{+}[RCONi(CO)3]^{-}",
        r"^{226}_{88}Ra + ^{1}_{0}n -> ^{227}_{88}Ra ->[\beta^-][42.2 \ min] ^{227}_{89}Ac",
        r"^{9}_{4}Be + ^{4}_{2}He -> ^{12}_{6}C + ^{1}_{0}n + \gamma",
        r"N2 + 3 H2 <=> 2 NH3",
    ]
    print("=== CHEMKERNEL — comprehend <ce> into a reaction graph (not strip) ===\n")
    for s in SAMPLES:
        r = understand_chem(s)
        tag = " [NUCLEAR]" if r["is_nuclear"] else ""
        print(f"  {s}{tag}")
        print(f"    species : {r['species']}")
        for rx in r["reactions"]:
            lhs = " + ".join(f"{c if c > 1 else ''}{n}" for c, n in rx["reactants"])
            rhs = " + ".join(f"{c if c > 1 else ''}{n}" for c, n in rx["products"])
            cc = f"  [{'; '.join(rx['conditions'])}]" if rx["conditions"] else ""
            print(f"    reaction: {lhs}  --{rx['reltype']}-->  {rhs}{cc}")
        print()
