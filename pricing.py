LOCALITY_PRICES = {
    "Nemocnice": 1000,
    "Město": 1500,
    "Mimo město": 2000,
    "Těžko přístupný terén": 4000,
}

HEAVY_TREATMENT_EXTRA = 2000

DIAGNOSTIC_PRICES = {
    "RTG": 250,
    "CT": 500,
    "MRI": 750,
    "SONO": 150,
}

def calculate_price(location: str, base: int, heavy: bool, diagnostics: list[str]) -> int:
    """Return total price for treatment."""
    price = base + LOCALITY_PRICES.get(location, 0)
    if heavy:
        price += HEAVY_TREATMENT_EXTRA
    for item in diagnostics:
        price += DIAGNOSTIC_PRICES.get(item, 0)
    return price
