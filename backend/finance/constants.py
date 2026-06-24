ALLOWED_CURRENCIES: tuple[str, ...] = (
    "PLN",
    "EUR",
    "USD",
    "GBP",
    "CHF",
    "CZK",
    "SEK",
    "NOK",
    "DKK",
    "HUF",
    "RON",
    "UAH",
    "JPY",
    "CNY",
    "AUD",
    "CAD",
    "NZD",
    "TRY",
    "BRL",
    "INR",
)

CURRENCY_LABELS: dict[str, str] = {
    "PLN": "Polski złoty",
    "EUR": "Euro",
    "USD": "Dolar amerykański",
    "GBP": "Funt brytyjski",
    "CHF": "Frank szwajcarski",
    "CZK": "Korona czeska",
    "SEK": "Korona szwedzka",
    "NOK": "Korona norweska",
    "DKK": "Korona duńska",
    "HUF": "Forint węgierski",
    "RON": "Lej rumuński",
    "UAH": "Hrywna ukraińska",
    "JPY": "Jen japoński",
    "CNY": "Juan chiński",
    "AUD": "Dolar australijski",
    "CAD": "Dolar kanadyjski",
    "NZD": "Dolar nowozelandzki",
    "TRY": "Lira turecka",
    "BRL": "Real brazylijski",
    "INR": "Rupia indyjska",
}

CATEGORY_COLOR_PALETTE: tuple[str, ...] = (
    "#7C9EB2",  # slate
    "#4DB6A0",  # teal
    "#6BC9A8",  # mint
    "#5B9BD5",  # sky
    "#7B8CDE",  # indigo
    "#9B7ED9",  # violet
    "#D97B8C",  # rose
    "#E8956A",  # coral
    "#E0B252",  # amber
    "#A8C66C",  # lime
    "#C4A77D",  # sand
    "#B48EAD",  # mauve
)

DEFAULT_CATEGORY_COLOR = CATEGORY_COLOR_PALETTE[0]
