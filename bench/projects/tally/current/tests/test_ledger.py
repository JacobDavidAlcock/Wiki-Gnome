import json
import tempfile
import unittest
from pathlib import Path

import tally
from tally import (
    DuplicateMember, InvalidAmount, Ledger, TallyError, Transfer, UnknownMember, UnsettledBalance, UnsupportedFormat,
)


def trio(currency="GBP"):
    ledger = Ledger(currency)
    for name in ("Ana", "Ben", "Cai"):
        ledger.add_member(name)
    return ledger


class MemberTests(unittest.TestCase):
    def test_members_keep_order(self):
        self.assertEqual(trio().members, ("Ana", "Ben", "Cai"))

    def test_duplicate_member(self):
        ledger = trio()
        with self.assertRaises(DuplicateMember):
            ledger.add_member("Ana")

    def test_names_are_case_sensitive(self):
        ledger = trio()
        ledger.add_member("ana")
        self.assertEqual(len(ledger.members), 4)

    def test_unknown_member_must_be_added_first(self):
        ledger = trio()
        with self.assertRaises(UnknownMember):
            ledger.add_expense("Zoe", 500)
        self.assertEqual(ledger.history, ())

    def test_remove_member_needs_zero_balance(self):
        ledger = trio()
        ledger.add_expense("Ana", 300)
        with self.assertRaises(UnsettledBalance):
            ledger.remove_member("Ben")
        ledger.record_payment("Ben", "Ana", 100)
        ledger.remove_member("Ben")
        self.assertEqual(ledger.members, ("Ana", "Cai"))

    def test_currency_is_normalised_and_checked(self):
        self.assertEqual(Ledger("gbp").currency, "GBP")
        with self.assertRaises(TallyError):
            Ledger("£")


class ExpenseTests(unittest.TestCase):
    def test_equal_split_includes_payer_by_default(self):
        ledger = trio()
        ledger.add_expense("Ana", 3000)
        self.assertEqual(ledger.balances(), {"Ana": 2000, "Ben": -1000, "Cai": -1000})

    def test_positive_balance_means_owed(self):
        ledger = trio()
        ledger.add_expense("Ana", 3000)
        self.assertGreater(ledger.balance("Ana"), 0)
        self.assertLess(ledger.balance("Ben"), 0)

    def test_default_split_uses_members_at_the_time(self):
        ledger = trio()
        ledger.add_expense("Ana", 3000)
        ledger.add_member("Dev")
        self.assertEqual(ledger.balance("Dev"), 0)

    def test_split_between(self):
        ledger = trio()
        ledger.add_expense("Ben", 1500, split_between=["Ben", "Cai"])
        self.assertEqual(ledger.balances(), {"Ana": 0, "Ben": 750, "Cai": -750})

    def test_payer_not_in_split(self):
        ledger = trio()
        ledger.add_expense("Ben", 900, weights={"Ana": 2, "Cai": 1})
        self.assertEqual(ledger.balances(), {"Ana": -600, "Ben": 900, "Cai": -300})

    def test_leftover_goes_to_earliest_added_members(self):
        ledger = trio()
        expense = ledger.add_expense("Cai", 1000, split_between=["Cai", "Ben", "Ana"])
        self.assertEqual(expense.shares, {"Ana": 334, "Ben": 333, "Cai": 333})
        self.assertEqual(sum(expense.shares.values()), 1000)

    def test_weighted_leftover(self):
        ledger = trio()
        expense = ledger.add_expense("Ana", 1000, weights={"Ben": 2, "Cai": 1})
        self.assertEqual(expense.shares, {"Ben": 667, "Cai": 333})

    def test_float_amount_rejected(self):
        ledger = trio()
        with self.assertRaises(InvalidAmount):
            ledger.add_expense("Ana", 12.5)
        with self.assertRaises(InvalidAmount):
            ledger.add_expense("Ana", 0)
        self.assertTrue(issubclass(InvalidAmount, ValueError))

    def test_split_and_weights_together(self):
        ledger = trio()
        with self.assertRaises(TallyError):
            ledger.add_expense("Ana", 900, split_between=["Ben"], weights={"Ben": 1})

    def test_payment_moves_balances(self):
        ledger = trio()
        ledger.add_expense("Ana", 3000)
        ledger.record_payment("Ben", "Ana", 1000)
        self.assertEqual(ledger.balances(), {"Ana": 1000, "Ben": 0, "Cai": -1000})


class SettleTests(unittest.TestCase):
    def test_settle_up_transfers(self):
        ledger = trio()
        ledger.add_expense("Ana", 6000)
        ledger.add_expense("Ben", 1500, split_between=["Ben", "Cai"])
        self.assertEqual(ledger.settle_up(), [Transfer("Cai", "Ana", 2750), Transfer("Ben", "Ana", 1250)])

    def test_settle_up_does_not_change_ledger(self):
        ledger = trio()
        ledger.add_expense("Ana", 3000)
        ledger.settle_up()
        self.assertEqual(ledger.balance("Ana"), 2000)

    def test_settled_ledger(self):
        self.assertEqual(trio().settle_up(), [])


class FileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "trip.json"

    def test_round_trip(self):
        ledger = trio("USD")
        ledger.add_expense("Ana", 1234, note="Dinner")
        ledger.record_payment("Ben", "Ana", 100)
        ledger.save(self.path)
        loaded = Ledger.load(self.path)
        self.assertEqual(loaded.balances(), ledger.balances())
        self.assertEqual(loaded.currency, "USD")
        self.assertEqual(json.loads(self.path.read_text())["format"], 2)

    def test_version_1_file_needs_upgrade(self):
        self.path.write_text(json.dumps({
            "version": 1, "currency": "GBP", "people": ["Ana", "Ben"],
            "expenses": [{"paid_by": "Ana", "amount": 10.01, "split": ["Ana", "Ben"]}],
            "payments": [{"from": "Ben", "to": "Ana", "amount": 2.5}],
        }))
        with self.assertRaises(UnsupportedFormat):
            Ledger.load(self.path)
        upgraded = tally.upgrade_file(self.path)
        self.assertEqual(upgraded.balances(), {"Ana": 250, "Ben": -250})
        self.assertEqual(Ledger.load(self.path).balances(), {"Ana": 250, "Ben": -250})


class FormatTests(unittest.TestCase):
    def test_format_amount(self):
        self.assertEqual(tally.format_amount(1234, "GBP"), "£12.34")
        self.assertEqual(tally.format_amount(-5, "USD"), "-$0.05")
        self.assertEqual(tally.format_amount(1000, "JPY"), "10.00 JPY")


if __name__ == "__main__":
    unittest.main()
