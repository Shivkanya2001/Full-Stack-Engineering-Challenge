from decimal import ROUND_HALF_EVEN, Decimal

# ISO 4217 minor unit exponents
CURRENCY_EXPONENTS: dict[str, int] = {
    "USD": 2,
    "EUR": 2,
    "GBP": 2,
    "JPY": 0,
    "CAD": 2,
    "AUD": 2,
    "CHF": 2,
}


def normalize_currency(currency: str) -> str:
    return currency.upper().strip()


def validate_currency(currency: str, supported: list[str]) -> str:
    normalized = normalize_currency(currency)
    if normalized not in supported:
        raise ValueError(f"Unsupported currency: {currency}")
    return normalized


def to_minor_units(amount: Decimal, currency: str) -> int:
    exponent = CURRENCY_EXPONENTS.get(normalize_currency(currency), 2)
    quantize_exp = Decimal(10) ** -exponent
    quantized = amount.quantize(quantize_exp, rounding=ROUND_HALF_EVEN)
    return int(quantized * (Decimal(10) ** exponent))


def from_minor_units(minor_units: int, currency: str) -> Decimal:
    exponent = CURRENCY_EXPONENTS.get(normalize_currency(currency), 2)
    return Decimal(minor_units) / (Decimal(10) ** exponent)


def format_amount(minor_units: int, currency: str) -> str:
    amount = from_minor_units(minor_units, currency)
    exponent = CURRENCY_EXPONENTS.get(normalize_currency(currency), 2)
    return f"{amount:.{exponent}f} {normalize_currency(currency)}"


def convert_amount(
    amount_minor: int,
    source_currency: str,
    target_currency: str,
    rate: Decimal,
) -> int:
    source = normalize_currency(source_currency)
    target = normalize_currency(target_currency)
    if source == target:
        return amount_minor

    source_amount = from_minor_units(amount_minor, source)
    converted = source_amount * rate
    return to_minor_units(converted, target)
