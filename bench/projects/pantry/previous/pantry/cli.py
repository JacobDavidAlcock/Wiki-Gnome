import argparse
import json
import sys
from datetime import date

from . import __version__
from .store import (
    PantryError,
    add_item,
    expiring_within,
    load,
    parse_date,
    resolve_path,
    save,
    use_item,
)

EXIT_OK = 0
EXIT_ERROR = 1


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {value}")
    return value


def non_negative_int(text: str) -> int:
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError(f"must be 0 or more, got {value}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pantry")
    parser.add_argument("--file", metavar="PATH")
    parser.add_argument("--version", action="version", version=f"pantry {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add")
    add.add_argument("name")
    add.add_argument("quantity", type=positive_int)
    add.add_argument("--unit", default="item")
    add.add_argument("--expires", metavar="YYYY-MM-DD")

    listing = commands.add_parser("list")
    listing.add_argument("--format", choices=["table", "json"], default="table")

    use = commands.add_parser("use")
    use.add_argument("name")
    use.add_argument("quantity", type=positive_int, nargs="?", default=1)

    expiring = commands.add_parser("expiring")
    expiring.add_argument("--days", type=non_negative_int, default=3)

    return parser


def describe_expiry(expires: date, today: date) -> str:
    delta = (expires - today).days
    if delta == 0:
        return "expires today"
    return f"expires in {delta} day{'s' if delta != 1 else ''}"


def run_add(args, items) -> int:
    expires = parse_date(args.expires) if args.expires else None
    item = add_item(items, args.name, args.quantity, args.unit, expires)
    print(f"{item.name}: {item.quantity} {item.unit}")
    return EXIT_OK


def run_list(args, items) -> int:
    ordered = sorted(items.values(), key=lambda i: i.name)

    if args.format == "json":
        print(json.dumps([item.to_json() for item in ordered], indent=2))
        return EXIT_OK
    if not ordered:
        print("Pantry is empty.")
        return EXIT_OK

    width = max(len("NAME"), *(len(item.name) for item in ordered))
    print(f"{'NAME':<{width}}  {'QTY':>5}  {'UNIT':<8}  EXPIRES")
    for item in ordered:
        expires = item.expires.isoformat() if item.expires else "-"
        print(f"{item.name:<{width}}  {item.quantity:>5}  {item.unit:<8}  {expires}")
    return EXIT_OK


def run_use(args, items) -> int:
    remaining = use_item(items, args.name, args.quantity)
    if remaining is None:
        print(f"Used the last of {args.name}; removed it from the pantry.")
    else:
        print(f"{remaining.name}: {remaining.quantity} {remaining.unit} left")
    return EXIT_OK


def run_expiring(args, items) -> int:
    today = date.today()
    found = expiring_within(items, args.days, today)
    if not found:
        print(f"Nothing expires in the next {args.days} days.")
        return EXIT_OK
    for item in found:
        print(f"{item.name} ({item.quantity} {item.unit}): {describe_expiry(item.expires, today)}")
    return EXIT_OK


COMMANDS = {
    "add": run_add,
    "list": run_list,
    "use": run_use,
    "expiring": run_expiring,
}

WRITES = {"add", "use"}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        path = resolve_path(args.file)
        items = load(path)
        status = COMMANDS[args.command](args, items)
        if args.command in WRITES:
            save(path, items)
        return status
    except PantryError as exc:
        print(f"pantry: error: {exc}", file=sys.stderr)
        return EXIT_ERROR
