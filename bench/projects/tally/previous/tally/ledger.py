import json
from pathlib import Path


class TallyError(Exception):
    pass


class UnknownPerson(TallyError):
    pass


class Ledger:
    def __init__(self, currency: str = "GBP"):
        self.currency = currency
        self.people: list[str] = []
        self.expenses: list[dict] = []
        self.payments: list[dict] = []

    def add_person(self, name: str) -> None:
        if name not in self.people:
            self.people.append(name)

    def add_expense(self, paid_by: str, amount: float, split=None, note: str = "") -> None:
        if amount <= 0:
            raise TallyError("amount must be positive")
        # People who aren't in the ledger yet are added automatically.
        self.add_person(paid_by)
        names = list(self.people) if split is None else list(split)
        for name in names:
            self.add_person(name)
        self.expenses.append({"paid_by": paid_by, "amount": float(amount), "split": names, "note": note})

    def record_payment(self, from_person: str, to_person: str, amount: float) -> None:
        for name in (from_person, to_person):
            if name not in self.people:
                raise UnknownPerson(name)
        self.payments.append({"from": from_person, "to": to_person, "amount": float(amount)})

    def balance(self, name: str) -> float:
        if name not in self.people:
            raise UnknownPerson(name)
        return self.balances()[name]

    def balances(self) -> dict[str, float]:
        # A positive balance means the person owes money.
        owes = {name: 0.0 for name in self.people}
        for expense in self.expenses:
            share = round(expense["amount"] / len(expense["split"]), 2)
            owes[expense["paid_by"]] -= expense["amount"]
            for name in expense["split"]:
                owes[name] += share
        for payment in self.payments:
            owes[payment["from"]] -= payment["amount"]
            owes[payment["to"]] += payment["amount"]
        return {name: round(amount, 2) for name, amount in owes.items()}

    def settle_up(self) -> list[tuple[str, str, float]]:
        balances = {name: amount for name, amount in self.balances().items() if abs(amount) >= 0.01}
        transfers = []
        while balances:
            debtor = max(balances, key=lambda n: balances[n])
            creditor = min(balances, key=lambda n: balances[n])
            if balances[debtor] <= 0 or balances[creditor] >= 0:
                break
            amount = round(min(balances[debtor], -balances[creditor]), 2)
            transfers.append((debtor, creditor, amount))
            balances[debtor] = round(balances[debtor] - amount, 2)
            balances[creditor] = round(balances[creditor] + amount, 2)
            balances = {n: a for n, a in balances.items() if abs(a) >= 0.01}
        return transfers

    def save(self, path) -> None:
        data = {"version": 1, "currency": self.currency, "people": self.people,
                "expenses": self.expenses, "payments": self.payments}
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load(path) -> Ledger:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ledger = Ledger(data["currency"])
    ledger.people = list(data["people"])
    ledger.expenses = list(data["expenses"])
    ledger.payments = list(data["payments"])
    return ledger
