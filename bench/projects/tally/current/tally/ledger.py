import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .errors import DuplicateMember, InvalidAmount, TallyError, UnknownMember, UnsettledBalance, UnsupportedFormat
from .money import check_amount, split

FORMAT = 2


@dataclass(frozen=True)
class Transfer:
    sender: str
    recipient: str
    amount: int


@dataclass(frozen=True)
class Expense:
    payer: str
    amount: int
    shares: dict[str, int]
    note: str = ""


@dataclass(frozen=True)
class Payment:
    sender: str
    recipient: str
    amount: int


@dataclass
class Ledger:
    currency: str
    _members: list[str] = field(default_factory=list, init=False, repr=False)
    _entries: list = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        code = str(self.currency).upper()
        if not re.fullmatch(r"[A-Z]{3}", code):
            raise TallyError(f"currency must be a 3-letter ISO 4217 code, such as GBP; got {self.currency!r}")
        self.currency = code

    @property
    def members(self) -> tuple[str, ...]:
        return tuple(self._members)

    @property
    def history(self) -> tuple:
        return tuple(self._entries)

    def add_member(self, name: str) -> None:
        if not name:
            raise TallyError("member names can't be empty")
        if name in self._members:
            raise DuplicateMember(f"{name!r} is already a member")
        self._members.append(name)

    def remove_member(self, name: str) -> None:
        self._require(name)
        balance = self.balance(name)
        if balance != 0:
            raise UnsettledBalance(f"{name!r} has a balance of {balance}; settle it before removing them")
        self._members.remove(name)

    def add_expense(self, payer: str, amount: int, *, split_between=None, weights=None, note: str = "") -> Expense:
        check_amount(amount)
        self._require(payer)
        if split_between is not None and weights is not None:
            raise TallyError("pass split_between or weights, not both")
        if weights is not None:
            for name, weight in weights.items():
                self._require(name)
                if isinstance(weight, bool) or not isinstance(weight, int) or weight <= 0:
                    raise TallyError(f"weights must be whole numbers greater than 0; got {weight!r} for {name!r}")
            participants = {name: weight for name, weight in weights.items()}
        else:
            names = list(self._members) if split_between is None else list(split_between)
            if not names:
                raise TallyError("an expense needs at least one participant")
            for name in names:
                self._require(name)
            participants = {name: 1 for name in names}
        # Shares follow the order members were added, so leftover minor units go to the earliest members.
        ordered = [name for name in self._members if name in participants]
        amounts = split(amount, [participants[name] for name in ordered])
        expense = Expense(payer, amount, dict(zip(ordered, amounts)), note)
        self._entries.append(expense)
        return expense

    def record_payment(self, sender: str, recipient: str, amount: int) -> Payment:
        check_amount(amount)
        self._require(sender)
        self._require(recipient)
        if sender == recipient:
            raise InvalidAmount("a payment needs two different members")
        payment = Payment(sender, recipient, amount)
        self._entries.append(payment)
        return payment

    def balance(self, name: str) -> int:
        self._require(name)
        return self._balances().get(name, 0)

    def balances(self) -> dict[str, int]:
        all_balances = self._balances()
        return {name: all_balances.get(name, 0) for name in self._members}

    def settle_up(self) -> list[Transfer]:
        order = {name: index for index, name in enumerate(self._members)}
        balances = {name: amount for name, amount in self.balances().items() if amount}
        transfers = []
        while balances:
            debtor = min((n for n in balances if balances[n] < 0), key=lambda n: (balances[n], order[n]))
            creditor = max((n for n in balances if balances[n] > 0), key=lambda n: (balances[n], -order[n]))
            amount = min(-balances[debtor], balances[creditor])
            transfers.append(Transfer(debtor, creditor, amount))
            for name, change in ((debtor, amount), (creditor, -amount)):
                balances[name] += change
                if balances[name] == 0:
                    del balances[name]
        return transfers

    def save(self, path) -> None:
        entries = []
        for entry in self._entries:
            if isinstance(entry, Expense):
                entries.append({"type": "expense", "payer": entry.payer, "amount": entry.amount,
                                "shares": entry.shares, "note": entry.note})
            else:
                entries.append({"type": "payment", "sender": entry.sender, "recipient": entry.recipient,
                                "amount": entry.amount})
        data = {"format": FORMAT, "currency": self.currency, "members": self._members, "entries": entries}
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path) -> "Ledger":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("format") != FORMAT:
            raise UnsupportedFormat(
                f"{path} is not a tally {FORMAT} file. To convert a file from tally 1, run tally.upgrade_file(path)."
            )
        ledger = cls(data["currency"])
        ledger._members = list(data["members"])
        for entry in data["entries"]:
            if entry["type"] == "expense":
                ledger._entries.append(Expense(entry["payer"], entry["amount"], dict(entry["shares"]), entry["note"]))
            else:
                ledger._entries.append(Payment(entry["sender"], entry["recipient"], entry["amount"]))
        return ledger

    def _require(self, name: str) -> None:
        if name not in self._members:
            raise UnknownMember(f"{name!r} is not a member; add them with add_member() first")

    def _balances(self) -> dict[str, int]:
        totals: dict[str, int] = {}
        for entry in self._entries:
            if isinstance(entry, Expense):
                totals[entry.payer] = totals.get(entry.payer, 0) + entry.amount
                for name, share in entry.shares.items():
                    totals[name] = totals.get(name, 0) - share
            else:
                totals[entry.sender] = totals.get(entry.sender, 0) + entry.amount
                totals[entry.recipient] = totals.get(entry.recipient, 0) - entry.amount
        return totals
