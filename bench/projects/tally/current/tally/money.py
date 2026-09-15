from .errors import InvalidAmount

SYMBOLS = {"GBP": "£", "USD": "$", "EUR": "€"}


def check_amount(amount) -> int:
    # bool is a subclass of int, but True is never a sensible amount of money.
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise InvalidAmount(
            f"amounts are whole numbers in minor units, such as pence or cents; got {amount!r}"
        )
    if amount <= 0:
        raise InvalidAmount(f"amounts must be greater than 0; got {amount}")
    return amount


def split(amount: int, weights: list[int]) -> list[int]:
    total_weight = sum(weights)
    shares = [amount * weight // total_weight for weight in weights]
    # Flooring can leave a few minor units over. Hand them out one at a time, in order.
    for index in range(amount - sum(shares)):
        shares[index % len(shares)] += 1
    return shares


def format_amount(amount: int, currency: str) -> str:
    sign = "-" if amount < 0 else ""
    major, minor = divmod(abs(amount), 100)
    symbol = SYMBOLS.get(currency)
    if symbol:
        return f"{sign}{symbol}{major}.{minor:02d}"
    return f"{sign}{major}.{minor:02d} {currency}"
