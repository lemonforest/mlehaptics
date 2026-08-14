"""``srmech.chemistry.reactions`` — reaction networks as exact-integer linear
algebra.

Three closed-form, exact-over-ℚ operators, each a composition of already
C-backed srmech primitives (``composition_of_c`` — no new C kernel, ABI stays
10):

``balance_reaction``
    Signed balanced integer coefficients = the integer nullspace of the
    **element × species** matrix ``A``. Composes ``QMat.nullspace`` (Class L)
    with the ``srmech.math.cyclic.primitive_integer_vector`` keystone (Class I ∘
    K ∘ C, rc378 `#T1049`) — the kernel column over ℚ becomes the smallest
    integer vector on its ray, first-nonzero-positive. The SIGN carries the
    direction: a NEGATIVE coefficient is a product. ``[H2, O2, H2O]`` →
    ``[2, 1, -2]`` (2 H₂ + 1 O₂ → 2 H₂O).

``conservation_laws``
    An integer basis of the conserved moieties = the LEFT-nullspace of the
    **species × reaction** stoichiometric matrix ``N`` (every ``γ`` with
    ``γᵀN = 0``). Composes ``QMat.T.nullspace`` (Class L) with the same keystone
    (Class I).

``deficiency``
    The Feinberg deficiency ``δ = n − ℓ − s = rank(L_complex) − rank(N)``:
    ``n`` distinct complexes, ``ℓ`` linkage classes (connected components of the
    complex graph), ``s = rank(N)``. Composes the Class-L
    ``dense_laplacian`` (``rank(L_complex) = n − ℓ`` exactly, since the
    combinatorial Laplacian of a graph has rank = vertices − components) with
    the Class-J ``QMat.rank``.

⚠️ TWO DIFFERENT MATRICES — the #1 correctness trap.
    ``balance_reaction`` builds **element × species** (rows are ELEMENTS, one
    column per SPECIES: entry = how many of that element the species carries).
    ``conservation_laws`` / ``deficiency`` build **species × reaction** (rows are
    SPECIES, one column per REACTION: entry = net stoichiometric change). They
    are transposed in role and must never be conflated.

Citation (science is the SSoT). The deficiency ``δ = n − ℓ − s`` is Feinberg's
Chemical Reaction Network Theory. It is definitional and stated self-contained
above; the standard references are M. Feinberg, *Foundations of Chemical
Reaction Network Theory*, Applied Mathematical Sciences vol. 202, Springer
(2019), and the open-access M. Feinberg, *Lectures on Chemical Reaction
Networks* (Mathematics Research Center, Univ. of Wisconsin, 1979/1980; hosted
at crnt.osu.edu). The paywalled Chem. Eng. Sci. **42** (1987) 2229–2268 origin
paper is NOT used as the attestation (paywalled-DOI discipline).

C-PARITY NOTE (`#T1050`). The three ops above are ``composition_of_c``. The
ergonomic input helper :func:`srmech.chemistry.formula.parse_formula` is a
genuine new string-processing capability (Class F/G); it ships pure-Python this
rc, and its JPL-clean caller-arena C peer ``srmech_parse_formula`` (bounded
tokenizer, explicit paren stack, ≤60-line functions, ≥2 asserts, no
malloc/goto) is a TRACKED immediate follow-up — an explicit deferral, not a
hidden gap.
"""
from __future__ import annotations

from typing import Iterable

from srmech.math.cyclic import primitive_integer_vector
from srmech.math.laplacian import dense_laplacian
from srmech.math.q import Q
from srmech.math.qmat import QMat

from .formula import parse_formula

__all__ = ["balance_reaction", "conservation_laws", "deficiency"]


# ── balance_reaction ───────────────────────────────────────────────────────

def _species_counts(species) -> list:
    """Coerce each species to an ``{element: count}`` dict — a formula string is
    parsed, a dict is copied (int-coerced), anything else is a TypeError."""
    counts = []
    for sp in species:
        if isinstance(sp, str):
            counts.append(parse_formula(sp))
        elif isinstance(sp, dict):
            counts.append({str(k): int(v) for k, v in sp.items()})
        else:
            raise TypeError(
                "balance_reaction: each species must be a formula str, an "
                f"{{element: count}} dict, or pass the whole element×species "
                f"matrix as a QMat; got {type(sp).__name__}")
    return counts


def _element_species_matrix(species) -> QMat:
    """The **element × species** matrix ``A`` (rows = elements sorted, columns =
    species; entry = element-count). A ``QMat`` passes straight through."""
    if isinstance(species, QMat):
        return species
    species = list(species)
    if not species:
        raise ValueError("balance_reaction: empty species list")
    counts = _species_counts(species)
    elements = sorted({el for c in counts for el in c})
    if not elements:
        raise ValueError("balance_reaction: no elements found across species")
    rows = [[Q(c.get(el, 0)) for c in counts] for el in elements]
    return QMat(rows)


def balance_reaction(species, *, all_balances: bool = False):
    """Balance a reaction → signed primitive integer coefficients.

    A balanced reaction is a vector ``v`` in the kernel of the **element ×
    species** matrix ``A`` (element conservation: ``A·v = 0``). Each kernel
    column over ℚ is reduced to the smallest integer vector on its ray by the
    ``primitive_integer_vector`` keystone, canonical sign = first nonzero entry
    positive. Read reactant vs product from the SIGN: a NEGATIVE coefficient is
    a product.

    Args:
        species: the reaction's species, as either
            * a ``list`` whose entries are formula strings (``"H2O"``) and/or
              ``{element: count}`` dicts (``{"H": 2, "O": 1}``) — mixable, or
            * a raw element×species ``QMat`` (rows = elements, columns =
              species).
        all_balances: when the kernel has dimension > 1 (an underdetermined
            reaction with several independent balances), ``True`` returns every
            primitive basis vector instead of raising.

    Returns:
        ``list[int]`` — the signed primitive coefficients (kernel dimension 1,
        the usual case). When ``all_balances=True``, ``list[list[int]]`` — one
        primitive vector per independent balance.

    Raises:
        ValueError: the reaction is UNBALANCEABLE (``A`` has full column rank →
            trivial kernel), or UNDERDETERMINED (kernel dimension > 1) and
            ``all_balances`` is ``False``.
        TypeError: an unsupported species entry type.

    Worked: ``balance_reaction(["H2", "O2", "H2O"]) == [2, 1, -2]`` — 2 H₂ + O₂
    → 2 H₂O (H₂O negative = product). ``composition_of_c`` (Class L nullspace ∘
    Class I/K/C keystone).
    """
    A = _element_species_matrix(species)
    basis = A.nullspace()
    if not basis:
        raise ValueError(
            "balance_reaction: no non-trivial balance exists — the element×"
            "species matrix has full column rank (trivial kernel), so the "
            "reaction is unbalanceable as given. Check the species set.")
    primitives = [primitive_integer_vector(col) for col in basis]
    if all_balances:
        return primitives
    if len(primitives) > 1:
        raise ValueError(
            f"balance_reaction: the reaction is underdetermined — {len(primitives)}"
            " independent balances exist (kernel dimension > 1). Pass "
            "all_balances=True to get them all, or add species to constrain it.")
    return primitives[0]


# ── conservation_laws ──────────────────────────────────────────────────────

def _as_qmat(matrix, *, what: str) -> QMat:
    """Coerce a stoichiometric matrix to ``QMat`` (a ``QMat`` passes through; a
    nested int/``Q``/``(num, den)`` sequence is built)."""
    if isinstance(matrix, QMat):
        return matrix
    rows = [list(r) for r in matrix]
    if not rows:
        raise ValueError(f"{what}: empty stoichiometric matrix")
    return QMat(rows)


def conservation_laws(N) -> list:
    """The conserved moieties of a reaction network — an integer basis of the
    LEFT-nullspace of the stoichiometric matrix ``N``.

    A conservation law is a vector ``γ`` (over species) with ``γᵀN = 0``: a
    linear combination of species whose total is invariant under every reaction
    (mass / charge / moiety conservation). The left-nullspace of ``N`` is
    ``ker(Nᵀ)``, so this is ``N.T.nullspace()`` with each kernel column reduced
    by the ``primitive_integer_vector`` keystone.

    ⚠️ ``N`` is the **species × reaction** stoichiometric matrix of a NETWORK
    (rows = species, columns = reactions; entry = net change of that species in
    that reaction) — the TRANSPOSE-in-role of ``balance_reaction``'s element×
    species matrix.

    Args:
        N: the stoichiometric matrix as a ``QMat`` or a nested sequence of
            ``int`` / ``Q`` / ``(num, den)`` (rows = species, columns =
            reactions).

    Returns:
        ``list[list[int]]`` — one primitive integer conservation vector per basis
        element of the left-nullspace (length = number of species each). The
        list is empty when ``N`` has full row rank (no conserved moiety).

    Worked: for Michaelis–Menten ``E + S ⇌ ES → E + P`` (species E, S, ES, P)
    this returns two laws — total enzyme (E + ES) and total substrate-matter
    (S + ES + P). ``composition_of_c`` (Class L left-nullspace ∘ Class I keystone).
    """
    M = _as_qmat(N, what="conservation_laws")
    basis = M.T.nullspace()
    return [primitive_integer_vector(col) for col in basis]


# ── deficiency ─────────────────────────────────────────────────────────────

def _normalize_complex(c) -> dict:
    """A network COMPLEX → an ``{species: coeff}`` dict, zeros dropped. Accepts a
    dict, a bare species-name str (coeff 1), or the zero complex (``""`` / ``"0"``
    / ``"∅"`` / ``None`` / ``{}``)."""
    if c is None or c == "" or c == "0" or c == "∅":
        return {}
    if isinstance(c, str):
        return {c: 1}
    if isinstance(c, dict):
        return {str(k): int(v) for k, v in c.items() if int(v) != 0}
    raise TypeError(
        "deficiency: each complex must be a {species: coeff} dict, a species "
        f"name str, or the zero complex (''/'0'/None); got {type(c).__name__}")


def _complex_key(d: dict):
    """A hashable canonical identity for a complex (order-independent)."""
    return tuple(sorted(d.items()))


def _stoichiometric_matrix(reaction_pairs: list, species: list) -> QMat:
    """The **species × reaction** matrix ``N`` from normalized (reactant,
    product) complex dicts: column = product-vector − reactant-vector."""
    index = {sp: i for i, sp in enumerate(species)}
    cols = []
    for reactant, product in reaction_pairs:
        col = [0] * len(species)
        for sp, coeff in reactant.items():
            col[index[sp]] -= coeff
        for sp, coeff in product.items():
            col[index[sp]] += coeff
        cols.append(col)
    # transpose the column list into rows (species × reaction)
    rows = [[Q(cols[j][i]) for j in range(len(cols))] for i in range(len(species))]
    return QMat(rows)


def deficiency(reactions: Iterable, *, with_components: bool = False):
    """The Feinberg deficiency ``δ`` of a chemical reaction network.

    ``δ = n − ℓ − s = rank(L_complex) − rank(N)`` where ``n`` = number of
    distinct complexes, ``ℓ`` = number of linkage classes (connected components
    of the complex graph), and ``s = rank(N)`` = dimension of the stoichiometric
    subspace. The deficiency is a non-negative integer fixed by network topology
    alone (independent of rate constants). ``rank(L_complex) = n − ℓ`` is
    computed as the exact rank of the combinatorial graph Laplacian of the
    complex graph (Class-L ``dense_laplacian``; a graph Laplacian has rank =
    vertices − components); ``rank(N)`` is the Class-J ``QMat.rank``.

    Args:
        reactions: an iterable of ``(reactant, product)`` pairs. Each complex is
            an ``{species: coeff}`` dict (``{"A": 2}`` for the complex 2A;
            ``{"A": 1, "B": 1}`` for A+B), a bare species-name str (coeff 1), or
            the zero complex (``""`` / ``"0"`` / ``None`` for ∅ in a
            synthesis/degradation step).
        with_components: when ``True`` return the full breakdown dict instead of
            the bare integer.

    Returns:
        ``int`` — the deficiency ``δ`` (default). When ``with_components=True``,
        ``{"deficiency": δ, "n_complexes": n, "n_linkage_classes": ℓ,
        "rank_stoichiometric": s}``.

    Raises:
        ValueError: an empty reaction list.

    Worked: the isomerization ``A ⇌ B`` has ``δ = 0``; the network
    ``2A → A+B → 2B → 2A`` has ``δ = 1`` (n=3, ℓ=1, s=1). Citation: Feinberg,
    *Foundations of Chemical Reaction Network Theory* (Springer AMS 202, 2019).
    ``composition_of_c`` (Class L Laplacian ∘ Class J rank).
    """
    reaction_pairs = []
    for rxn in reactions:
        reactant, product = rxn
        reaction_pairs.append((_normalize_complex(reactant),
                               _normalize_complex(product)))
    if not reaction_pairs:
        raise ValueError("deficiency: empty reaction list")

    # Distinct complexes (nodes) in first-seen order, and the species roster.
    complex_index: dict = {}
    complexes: list = []
    species_seen: dict = {}
    for reactant, product in reaction_pairs:
        for comp in (reactant, product):
            key = _complex_key(comp)
            if key not in complex_index:
                complex_index[key] = len(complexes)
                complexes.append(comp)
            for sp in comp:
                species_seen.setdefault(sp, None)
    species = sorted(species_seen)
    n = len(complexes)

    # Complex graph: one undirected edge per reaction between DISTINCT complexes
    # (self-edges — reactant complex == product complex — carry no linkage and
    # would corrupt the Laplacian's diagonal, so they are skipped).
    edges = []
    for reactant, product in reaction_pairs:
        a = complex_index[_complex_key(reactant)]
        b = complex_index[_complex_key(product)]
        if a != b:
            edges.append((a, b))

    # rank(L_complex) = n − ℓ, exact: the integer-valued combinatorial Laplacian
    # lifts losslessly into QMat, and QMat.rank is exact over ℚ.
    rank_L = QMat.from_mat(dense_laplacian(n, edges)).rank()
    ell = n - rank_L

    N = _stoichiometric_matrix(reaction_pairs, species)
    s = N.rank()
    delta = rank_L - s

    if with_components:
        return {
            "deficiency": delta,
            "n_complexes": n,
            "n_linkage_classes": ell,
            "rank_stoichiometric": s,
        }
    return delta
