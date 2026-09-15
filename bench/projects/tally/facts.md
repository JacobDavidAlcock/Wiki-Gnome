# tally answer key

This file lists the facts a correct doc for tally must get right. It stays outside the `current/` folder, so writing sessions never see it. The judge compares generated docs against it.

`tally` is a Python library that records shared expenses in a group and works out who owes whom. It has no third-party dependencies.

## Install and import

| Fact | Value |
|---|---|
| Python version | 3.10 or later |
| Install from a clone | `pip install .` from the project's root folder. An editable install, `pip install -e .`, also works. |
| Distribution name in `pyproject.toml` | `tally-ledger` |
| Import name | `tally`, as in `import tally` or `from tally import Ledger` |
| Published to PyPI | No. `pip install tally` or `pip install tally-ledger` doesn't install this project. |
| Version | `2.0.0`, available as `tally.__version__` |
| Command-line interface | None. tally is a library only. |
| Run the tests | `python -m unittest` from the project's root folder |

## Money

- Every amount is an `int` in the currency's minor unit: pence for GBP, cents for USD and EUR. £12.50 is `1250`.
- A `float`, a `Decimal`, a string, a `bool`, `0` or a negative number raises `InvalidAmount`. `InvalidAmount` is a subclass of both `TallyError` and `ValueError`.
- `tally.format_amount(amount, currency)` formats minor units for display: `format_amount(1234, "GBP")` returns `"£12.34"`, `format_amount(-5, "USD")` returns `"-$0.05"`, and currencies without a symbol use the code, as in `"10.00 JPY"`. Symbols exist for GBP, USD and EUR only.

## Create a ledger and add members

- `Ledger(currency)` takes a 3-letter ISO 4217 code. There is no default. Lowercase is converted, so `Ledger("gbp").currency` is `"GBP"`. Anything else, such as `"£"`, raises `TallyError`.
- `ledger.add_member(name)` adds a member. Names are case-sensitive: `"Ana"` and `"ana"` are different members. Adding an existing name raises `DuplicateMember`. An empty name raises `TallyError`.
- Members must be added **before** they appear in an expense or payment. Using an unknown name anywhere raises `UnknownMember` and records nothing. Members are never added automatically.
- `ledger.members` is a tuple of names in the order they were added.
- `ledger.remove_member(name)` removes a member only when their balance is exactly 0. Otherwise it raises `UnsettledBalance`.

## Record expenses

`ledger.add_expense(payer, amount, *, split_between=None, weights=None, note="")` returns an `Expense`.

- `split_between` and `weights` are keyword-only.
- With neither, the expense is split equally between **all current members, including the payer**. Members added later don't share earlier expenses.
- `split_between` is a list of member names to split equally between. The payer is only included if listed.
- `weights` is a dict of member name to whole-number weight greater than 0, such as `{"Ana": 2, "Cai": 1}`. Only the named members share the expense.
- Passing both `split_between` and `weights` raises `TallyError`.
- Shares always add up to exactly the amount. Each share is rounded down, and any leftover minor units go one each to the participants **in the order they were added to the ledger**, earliest first. They don't go to the payer. For example, 1000 split between Ana, Ben and Cai (added in that order) gives Ana 334, Ben 333 and Cai 333.
- `Expense` is a frozen dataclass with `payer`, `amount`, `shares` (a dict of name to minor units) and `note`.

## Record payments

- `ledger.record_payment(sender, recipient, amount)` records money one member paid another, and returns a `Payment` with `sender`, `recipient` and `amount`.
- Paying yourself raises `InvalidAmount`. Unknown names raise `UnknownMember`.

## Balances

- `ledger.balance(name)` returns an `int` in minor units. **Positive means the member is owed money; negative means they owe money.**
- `ledger.balances()` returns a dict of every current member's balance, in the order members were added.
- Balances across all members add up to 0.
- `ledger.history` is a tuple of every `Expense` and `Payment`, in the order they were recorded.

## Settle up

- `ledger.settle_up()` returns a list of `Transfer` objects that would bring every balance to 0. It **doesn't change the ledger**. Call `record_payment` for each transfer once the money has actually moved.
- `Transfer` is a frozen dataclass with `sender`, `recipient` and `amount`. It is not a tuple and can't be unpacked.
- Transfers are chosen by repeatedly matching the member who owes the most with the member owed the most. Ties go to the member added first.
- Example: Ana, Ben and Cai. Ana pays 6000 split between all three; Ben pays 1500 split between Ben and Cai. `settle_up()` returns `[Transfer("Cai", "Ana", 2750), Transfer("Ben", "Ana", 1250)]`.
- A settled ledger returns `[]`.

## Save and load

- `ledger.save(path)` writes JSON. `path` can be a `str` or a `Path`.
- `Ledger.load(path)` is a **class method** that returns a new `Ledger`. There is no module-level `tally.load`.
- The file has `"format": 2`, plus `currency`, `members` and `entries`.
- Loading any other file, including a tally 1 file, raises `UnsupportedFormat`.
- `tally.upgrade_file(path)` converts a tally 1 file to format 2 in place and returns the `Ledger`. It converts decimal amounts to minor units and recalculates shares with tally 2's rounding, so balances can differ from tally 1 by a minor unit. Calling it on a format 2 file loads it unchanged.

## Errors

| Exception | Raised when |
|---|---|
| `TallyError` | Base class for every tally error. Also raised for a bad currency, an empty name, bad weights, or passing both `split_between` and `weights`. |
| `InvalidAmount` | An amount isn't a positive `int`, or a member pays themselves. Also a `ValueError`. |
| `UnknownMember` | A name isn't a member. Also a `KeyError`. |
| `DuplicateMember` | `add_member` is called with an existing name. |
| `UnsettledBalance` | `remove_member` is called for a member whose balance isn't 0. |
| `UnsupportedFormat` | `Ledger.load` or `upgrade_file` gets a file it can't read. |

All exceptions are importable from `tally`.

## Things that don't exist

A doc that mentions any of these has invented them:

- A command-line tool, a config file or environment variables
- Automatic member creation
- Currency conversion or mixing currencies in one ledger
- Methods such as `Ledger.from_file`, `ledger.split`, `ledger.settle()`, `ledger.pay()` or `ledger.add_person` in tally 2
- A PyPI package, Docker image or conda package

## Changes since 1.0.0

The 1.0.0 source is in `previous/`. The changelog task compares it with `current/`.

| Change | Type | What existing users notice |
|---|---|---|
| Amounts are `int` minor units instead of `float` major units | Breaking | `add_expense("Ana", 12.50)` now raises `InvalidAmount`. Pass `1250`. Balances and transfer amounts are ints in minor units too. |
| Balance sign reversed | Breaking | In 1.0, a positive balance meant the person owed money. In 2.0, positive means they are owed. A 1.0 balance of `5.0` for someone owing £5 is `-500` in 2.0. |
| Members must be added first | Breaking | 1.0 added unknown people automatically in `add_expense`. 2.0 raises `UnknownMember`. |
| `add_person` renamed to `add_member`; `UnknownPerson` renamed to `UnknownMember`; `Ledger.people` renamed to `Ledger.members` (now a tuple) | Breaking | Old names raise `AttributeError` or `ImportError`. |
| `settle_up()` returns `Transfer` objects | Breaking | 1.0 returned `(from, to, amount)` tuples. Use `.sender`, `.recipient` and `.amount`. |
| `tally.load(path)` replaced by `Ledger.load(path)` | Breaking | The module-level function is gone. |
| File format 2 | Breaking | 2.0 can't load 1.0 files. Run `tally.upgrade_file(path)` once on each file. |
| `Ledger()` needs a currency | Breaking | 1.0 defaulted to `"GBP"`. |
| `record_payment` parameters renamed | Breaking | `from_person` and `to_person` are now `sender` and `recipient`. Positional calls still work. |
| Exact rounding | Changed | 1.0 rounded each share to 2 decimal places, so shares could add up to a penny more or less than the expense. 2.0 shares always add up exactly. |
| `split` renamed to `split_between` and made keyword-only | Breaking | `add_expense("Ana", 900, ["Ben"])` no longer works. |
| `weights` for uneven splits | Added | |
| `remove_member`, `history`, `format_amount`, `upgrade_file` | Added | |
| Exception classes `InvalidAmount`, `DuplicateMember`, `UnsettledBalance`, `UnsupportedFormat` | Added | |
