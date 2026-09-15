# Pantry answer key

This file lists the facts a correct doc for `pantry/` must get right. It stays outside the `pantry/` folder so writing sessions never see it. The accuracy checker and the judge compare generated docs against it.

`pantry` is a command-line tool that tracks food in your kitchen and warns you before it expires. It is written in Python with no third-party dependencies.

## Install and run

| Fact | Value |
|---|---|
| Python version | 3.10 or later |
| Install from a clone | `pip install .` from the `pantry/` folder. An editable install, `pip install -e .`, also works. |
| Command after install | `pantry` |
| Run without installing | `python -m pantry` from the `pantry/` folder |
| Package name in `pyproject.toml` | `pantry-cli` |
| Published to PyPI | No. `pip install pantry` or `pip install pantry-cli` does not install this project. |
| Version | `0.2.0`, shown by `pantry --version` as `pantry 0.2.0` |
| Run the tests | `python -m unittest` from the `pantry/` folder |

## Global options

| Option | Behaviour |
|---|---|
| `--file PATH` | Uses `PATH` as the pantry file. Must come **before** the command: `pantry --file x.json list` works, `pantry list --file x.json` exits with status 2. |
| `--version` | Prints the version and exits. |

## Pantry file location

The first match wins:

1. `--file PATH`
2. The `PANTRY_FILE` environment variable
3. `pantry.json` in the **current working directory**, not the home directory

Reading a missing file acts as an empty pantry and does not create the file. Only `add` and `use` write the file.

## Commands

### `pantry add NAME QUANTITY [--unit UNIT] [--expires YYYY-MM-DD]`

- `QUANTITY` is a whole number, 1 or more. `0`, negatives and decimals exit with status 2.
- `--unit` defaults to `item`.
- `--expires` must be `YYYY-MM-DD`. Any other format exits with status 1 and prints `pantry: error: invalid date '16/09/2026'; use YYYY-MM-DD`.
- Names are case-insensitive and extra spaces are collapsed: `Brown  Rice` is stored as `brown rice`.
- Adding an item that already exists adds to its quantity. If the new date is earlier, it replaces the stored expiry date; a later date is ignored.
- Adding an existing item with a different unit exits with status 1: `pantry: error: flour is stored in 'kg', not 'g'`. Units are never converted.
- Prints the new total, e.g. `milk: 2 l`.

### `pantry list [--format table|json] [--sort name|expires]`

- `--format` defaults to `table`. `json` prints a JSON array of items.
- `--sort` defaults to `name`. With `expires`, items without an expiry date come last.
- An empty pantry prints `Pantry is empty.`
- Table columns: `NAME`, `QTY`, `UNIT`, `EXPIRES`. An item without a date shows `-`.

### `pantry use NAME [QUANTITY]`

- `QUANTITY` defaults to 1.
- Using the last of an item removes it and prints `Used the last of eggs; removed it from the pantry.`
- Using more than is stored exits with status 1: `pantry: error: only 2 item of eggs left`.
- Using an unknown item exits with status 1: `pantry: error: no item named 'caviar'`.

### `pantry expiring [--days N] [--check]`

- Lists items that expire within `N` days of today, including items that have **already** expired. `--days` defaults to 3; `0` means today or earlier.
- An item expiring exactly `N` days from today is included.
- Output is sorted by expiry date, then by name, e.g. `milk (2 l): expires in 1 day`, `eggs (6 item): expired 5 days ago`, `bread (1 item): expires today`.
- If nothing matches, it prints `Nothing expires in the next 3 days.` and exits with status 0.
- Without `--check`, it always exits with status 0. With `--check`, it exits with status **3** when at least one item is listed, for use in cron jobs and scripts.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | A pantry error: bad date, unit mismatch, unknown item, not enough left, unreadable or unwritable file |
| 2 | Invalid command-line usage, reported by `argparse` |
| 3 | `expiring --check` found at least one item |

## File format

```json
{
  "version": 1,
  "items": [
    {"name": "milk", "quantity": 2, "unit": "l", "expires": "2026-09-16"}
  ]
}
```

- Items are saved sorted by name. `expires` is `null` when no date is set.
- Any `version` other than `1` exits with status 1: `unsupported format version 2; expected 1`. A file with no `version` field, such as one written by 0.1.0, fails the same way with `unsupported format version None; expected 1`.
- Invalid JSON exits with status 1.
- Writes go to `pantry.json.tmp` first and then replace the file, so a crash can't leave a half-written pantry.

## Things that don't exist

A doc that mentions any of these has invented them:

- A `remove`, `delete`, `edit`, `search` or `init` command
- A config file, or any environment variable other than `PANTRY_FILE`
- A default file in the home directory
- Unit conversion
- Any third-party dependency
- A PyPI package, Docker image or Homebrew formula

## Changes since 0.1.0

The 0.1.0 source is in `pantry-0.1.0/`. The changelog task compares it with `pantry/`.

| Change | Type | What existing users notice |
|---|---|---|
| Pantry files now need `"version": 1` | Breaking | A file written by 0.1.0 fails to load with exit status 1. Adding `"version": 1` to the top-level object fixes it. |
| `expiring` includes items that have already expired | Behaviour change | Expired items now appear, as `expired N days ago`. In 0.1.0 they were hidden. |
| Item names are case-insensitive and extra spaces are collapsed | Behaviour change | New names are stored lowercased, so `Milk` and `milk` are one item. Names already stored with capitals by 0.1.0 are never renamed: `use Milk` can't find an item stored as `Milk`, and `add Milk` creates a second, separate `milk` item. |
| Adding an item with a different unit is an error | Behaviour change | 0.1.0 silently added the quantity and kept the old unit. 0.2.0 exits with status 1. |
| `expiring --check` | New | Exits with status 3 when at least one item is listed. |
| `list --sort name\|expires` | New | Sorts by expiry date, undated items last. |
