"""Curated ingredient / E-number corpus for the ingredient classifier.

This is a research-grade starter set drawn from publicly-documented
halal-monitoring sources (JAKIM, MUI, HFA guidance documents). Final
adjudication of any specific E-number is the prerogative of the
relevant Shariah authority; this corpus encodes the *typical* lattice
position used by major regulators as a deterministic prior.
"""

from __future__ import annotations

from ghc_traceability.types import Verdict

# Haram keywords (lowercase substrings).
HARAM_KEYWORDS: list[str] = [
    "pork",
    "lard",
    "bacon",
    "ham ",
    "prosciutto",
    "pepperoni",
    "blood sausage",
    "alcohol",
    "ethanol",
    "wine",
    "beer",
    "rum",
    "vodka",
    "whisky",
    "whiskey",
    "rice wine",
    "carrion",
    "khinzir",
    "babi",
]

# Mashbuh (doubtful) keywords — typically require certified provenance.
MASHBUH_KEYWORDS: list[str] = [
    "gelatin",
    "rennet",
    "lecithin",
    "lipase",
    "pepsin",
    "shortening",
    "mono- and diglycerides",
    "mono and diglycerides",
    "monoglycerides",
    "glycerin",
    "glycerine",
    "glycerol",
    "natural flavor",
    "natural flavour",
    "natural flavoring",
    "natural flavouring",
    "vanilla extract",
    "casein",
    "whey",
    "tallow",
    "stearic acid",
    "stearate",
]

# E-numbers with their typical lattice classification. Sources include
# JAKIM Halal/Haram E-codes guidance and MUI's haram E-number lists.
E_NUMBER_LATTICE: dict[str, Verdict] = {
    # Confirmed haram (animal-derived where the animal is non-halal,
    # or alcohol-derived).
    "E120": Verdict.HARAM,    # cochineal / carmine (insect-derived; jurists differ)
    "E441": Verdict.HARAM,    # gelatin (when porcine)
    "E542": Verdict.HARAM,    # bone phosphate (typically porcine)
    "E904": Verdict.HARAM,    # shellac (insect-derived; jurists differ)
    "E1518": Verdict.HARAM,   # glyceryl triacetate / triacetin (alcohol)
    # Doubtful — depend on source.
    "E322": Verdict.MASHBUH,  # lecithin
    "E422": Verdict.MASHBUH,  # glycerol
    "E430": Verdict.MASHBUH,  # polyoxyethylene stearate
    "E431": Verdict.MASHBUH,
    "E470": Verdict.MASHBUH,  # fatty acid salts
    "E471": Verdict.MASHBUH,  # mono/diglycerides
    "E472a": Verdict.MASHBUH,
    "E472b": Verdict.MASHBUH,
    "E472c": Verdict.MASHBUH,
    "E472e": Verdict.MASHBUH,
    "E473": Verdict.MASHBUH,
    "E474": Verdict.MASHBUH,
    "E475": Verdict.MASHBUH,
    "E476": Verdict.MASHBUH,
    "E477": Verdict.MASHBUH,
    "E478": Verdict.MASHBUH,
    "E481": Verdict.MASHBUH,
    "E482": Verdict.MASHBUH,
    "E483": Verdict.MASHBUH,
    "E491": Verdict.MASHBUH,
    "E492": Verdict.MASHBUH,
    "E493": Verdict.MASHBUH,
    "E494": Verdict.MASHBUH,
    "E495": Verdict.MASHBUH,
    "E570": Verdict.MASHBUH,  # stearic acid
    "E572": Verdict.MASHBUH,  # magnesium stearate
    "E631": Verdict.MASHBUH,  # disodium inosinate
    "E635": Verdict.MASHBUH,  # disodium 5'-ribonucleotides
}


def lookup_e_number(token: str) -> Verdict | None:
    """Return the lattice classification for a token if it is a known
    E-number, else `None`."""
    return E_NUMBER_LATTICE.get(token.upper())


def keyword_verdict(text: str) -> Verdict | None:
    """Return a verdict if any keyword unambiguously matches, else
    `None`. Haram keywords short-circuit; mashbuh keywords trigger
    only if no haram keyword matched."""
    lower = " " + text.lower() + " "
    if any(k in lower for k in HARAM_KEYWORDS):
        return Verdict.HARAM
    if any(k in lower for k in MASHBUH_KEYWORDS):
        return Verdict.MASHBUH
    return None
