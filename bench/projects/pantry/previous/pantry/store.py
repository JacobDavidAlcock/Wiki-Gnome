import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

DEFAULT_FILE = "pantry.json"
ENV_VAR = "PANTRY_FILE"


class PantryError(Exception):
    pass


@dataclass
class Item:
    name: str
    quantity: int
    unit: str
    expires: date | None = None

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "expires": self.expires.isoformat() if self.expires else None,
        }

    @classmethod
    def from_json(cls, data: dict) -> "Item":
        expires = parse_date(data["expires"]) if data.get("expires") else None
        return cls(data["name"], int(data["quantity"]), data["unit"], expires)


def parse_date(text: str) -> date:
    try:
        return datetime.strptime(text, "%Y-%m-%d").date()
    except ValueError:
        raise PantryError(f"invalid date {text!r}; use YYYY-MM-DD") from None


def resolve_path(cli_path: str | None) -> Path:
    if cli_path:
        return Path(cli_path)
    env_path = os.environ.get(ENV_VAR)
    if env_path:
        return Path(env_path)
    return Path.cwd() / DEFAULT_FILE


def load(path: Path) -> dict[str, Item]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PantryError(f"{path} is not valid JSON ({exc.msg})") from None
    except OSError as exc:
        raise PantryError(f"cannot read {path} ({exc.strerror})") from None
    return {item["name"]: Item.from_json(item) for item in data["items"]}


def save(path: Path, items: dict[str, Item]) -> None:
    payload = {"items": [items[name].to_json() for name in sorted(items)]}
    # Write to a temporary file first so a crash never leaves a half-written pantry.
    tmp_path = path.with_name(path.name + ".tmp")
    try:
        tmp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(path)
    except OSError as exc:
        raise PantryError(f"cannot write {path} ({exc.strerror})") from None


def add_item(items: dict[str, Item], name: str, quantity: int, unit: str, expires: date | None) -> Item:
    existing = items.get(name)
    if existing is None:
        items[name] = Item(name, quantity, unit, expires)
        return items[name]
    existing.quantity += quantity
    if expires and (existing.expires is None or expires < existing.expires):
        existing.expires = expires
    return existing


def use_item(items: dict[str, Item], name: str, quantity: int) -> Item | None:
    existing = items.get(name)
    if existing is None:
        raise PantryError(f"no item named {name!r}")
    if quantity > existing.quantity:
        raise PantryError(f"only {existing.quantity} {existing.unit} of {name} left")
    existing.quantity -= quantity
    if existing.quantity == 0:
        del items[name]
        return None
    return existing


def expiring_within(items: dict[str, Item], days: int, today: date) -> list[Item]:
    found = [
        item for item in items.values()
        if item.expires is not None and 0 <= (item.expires - today).days <= days
    ]
    return sorted(found, key=lambda item: (item.expires, item.name))
