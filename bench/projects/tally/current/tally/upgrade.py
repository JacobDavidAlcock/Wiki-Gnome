import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from .errors import UnsupportedFormat
from .ledger import Ledger


def _minor_units(amount) -> int:
    return int((Decimal(str(amount)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def upgrade_file(path) -> Ledger:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format") == 2:
        return Ledger.load(path)
    if data.get("version") != 1:
        raise UnsupportedFormat(f"{path} is neither a tally 1 nor a tally 2 file")

    ledger = Ledger(data["currency"])
    for name in data["people"]:
        ledger.add_member(name)
    # tally 1 stored decimal amounts and rounded each share separately. Shares are recalculated
    # with tally 2's rules, so a balance can move by a minor unit or two.
    for expense in data["expenses"]:
        ledger.add_expense(expense["paid_by"], _minor_units(expense["amount"]),
                           split_between=expense["split"], note=expense.get("note", ""))
    for payment in data["payments"]:
        ledger.record_payment(payment["from"], payment["to"], _minor_units(payment["amount"]))
    ledger.save(path)
    return ledger
