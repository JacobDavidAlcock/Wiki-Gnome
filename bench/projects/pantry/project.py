"""pantry: a small command-line tool that tracks food and warns before it expires.

Readers write shell commands. Its main traps: --file must come before the command, `expiring --check`
exits with status 3, and the default pantry file is in the working directory.
"""

import json
import re
from datetime import date, timedelta
from pathlib import Path

from harness.model import InventedPattern, Project, Question, Task
from harness.sandbox import commands_text, disallowed_shell

EXTRA_COMMANDS = frozenset({"pantry"})

EXEC_PROMPT = """You are a developer who has never used pantry. Your only source of information is the documentation below. Don't guess from general knowledge where the documentation answers a question; where it doesn't, make your best attempt.

Your setup:
- You are in a bash shell in an empty working folder.
- The pantry repository is already cloned into ./pantry.
- A Python virtual environment is already active, so `python` and `pip` use it. Don't create another one.
- The folder ./kitchen exists.
- Today is {today}.

Write the shell commands for each job. Each job starts in a new shell in the working folder, so nothing from an earlier job carries over: no changed directory and no environment variables.

1. "install": install pantry so the `pantry` command works.
2. "add": record 2 litres of milk that expire on {milk_date}, and 12 eggs with no expiry date, in the file kitchen/stock.json.
3. "check": one command for a daily cron job that exits with a non-zero status if anything in kitchen/stock.json has already expired or expires within the next 7 days, and exits with 0 otherwise. Give only the command, not the crontab schedule.
4. "env": make `pantry list`, with no options, read kitchen/stock.json for the rest of this shell session.
5. "use": kitchen/stock.json holds 12 eggs. Record that you used all of them.

Reply with only a JSON object, no other text:
{{"install": ["..."], "add": ["..."], "check": "...", "env": ["..."], "use": ["..."]}}

<documentation>
{doc}
</documentation>
"""

DOCSTRING_QUESTIONS = (
    Question(
        "What does `add_item` do when the item already exists but you pass a different unit?",
        {"A": "Adds the quantity and keeps the stored unit", "B": "Converts the quantity to the stored unit",
         "C": "Raises `PantryError`", "D": "Replaces the stored unit with the new one"},
        "C",
    ),
    Question(
        "What does `add_item` do with `expires` when the item already exists with an earlier expiry date?",
        {"A": "Replaces it with the new, later date", "B": "Keeps the earlier stored date",
         "C": "Raises `PantryError`", "D": "Clears the expiry date"},
        "B",
    ),
    Question(
        "What does `use_item` do when the quantity reaches zero?",
        {"A": "Keeps the item at quantity 0 and returns it", "B": "Removes the item and returns `None`",
         "C": "Raises `PantryError`", "D": "Removes the item and returns it"},
        "B",
    ),
    Question(
        "What path does `resolve_path(None)` return when `PANTRY_FILE` isn't set?",
        {"A": "`~/pantry.json`", "B": "`pantry.json` in the current working directory",
         "C": "It raises `PantryError`", "D": "`~/.config/pantry/pantry.json`"},
        "B",
    ),
    Question(
        "Does `expiring_within` include items that have already expired?",
        {"A": "Yes", "B": "No, only items expiring from today onwards",
         "C": "Only when `days` is 0", "D": "Only when `today` is passed explicitly"},
        "A",
    ),
    Question(
        "What does `load` return when the file doesn't exist?",
        {"A": "It raises `PantryError`", "B": "An empty dict", "C": "It creates the file and returns an empty dict",
         "D": "`None`"},
        "B",
    ),
    Question(
        "Which date formats does `parse_date` accept?",
        {"A": "Any format `dateutil` can parse", "B": "Only `YYYY-MM-DD`", "C": "Only `DD/MM/YYYY`",
         "D": "`YYYY-MM-DD` and `DD/MM/YYYY`"},
        "B",
    ),
    Question(
        "What does `normalise_name(\"  Brown  Rice \")` return?",
        {"A": "`\"Brown Rice\"`", "B": "`\"brown rice\"`", "C": "`\"brown  rice\"`", "D": "`\"brownrice\"`"},
        "B",
    ),
)

CHANGELOG_QUESTIONS = (
    Question(
        "You upgrade from 0.1.0 to 0.2.0 and keep your existing pantry file. What happens?",
        {"A": "It works unchanged", "B": "pantry migrates it automatically",
         "C": "It fails to load until you add `\"version\": 1` to it", "D": "pantry deletes it and starts empty"},
        "C",
    ),
    Question(
        "How does `pantry expiring` treat items that have already expired, compared with 0.1.0?",
        {"A": "They are still hidden", "B": "They are now listed", "C": "They are now removed automatically",
         "D": "Nothing changed; they were always listed"},
        "B",
    ),
    Question(
        "Which exit code does `pantry expiring --check` use when it finds items?",
        {"A": "1", "B": "2", "C": "3", "D": "4"},
        "C",
    ),
    Question(
        "You run `pantry add flour 500 --unit g`, but flour is stored in `kg`. What happens in 0.2.0?",
        {"A": "pantry converts 500 g to 0.5 kg", "B": "pantry adds 500 and keeps `kg`, as in 0.1.0",
         "C": "The command fails with an error", "D": "pantry changes the unit to `g`"},
        "C",
    ),
    Question(
        "Your 0.1.0 file has an item stored as `Milk`. What does `pantry use Milk` do in 0.2.0?",
        {"A": "Works as before", "B": "Fails because no item named `milk` exists",
         "C": "Renames the item to `milk` and uses it", "D": "Uses both `Milk` and `milk`"},
        "B",
    ),
    Question(
        "Which option did 0.2.0 add to `pantry list`?",
        {"A": "`--sort`", "B": "`--filter`", "C": "`--reverse`", "D": "`--all`"},
        "A",
    ),
)

TASKS = [
    Task(
        id="readme",
        kind="Tutorial and reference",
        prompt="Write a README.md for this project.",
        doc_path="README.md",
        reader="exec",
        jobs=("install", "add", "check", "env", "use"),
    ),
    Task(
        id="cli-reference",
        kind="Reference",
        prompt="Write reference documentation for the pantry command-line interface. Save it as docs/cli.md.",
        doc_path="docs/cli.md",
        reader="exec",
        jobs=("add", "check", "env", "use"),
    ),
    Task(
        id="howto-alerts",
        kind="How-to guide",
        prompt=(
            "Write a how-to guide that shows how to get a daily warning when food in the pantry is about "
            "to expire. Save it as docs/expiry-alerts.md."
        ),
        doc_path="docs/expiry-alerts.md",
        reader="exec",
        jobs=("check",),
    ),
    Task(
        id="docstrings",
        kind="Reference (docstrings)",
        prompt="Add docstrings to the functions in pantry/store.py.",
        doc_path="pantry/store.py",
        reader="quiz",
        questions=DOCSTRING_QUESTIONS,
        code_doc=True,
    ),
    Task(
        id="changelog",
        kind="Changelog",
        prompt="Write a CHANGELOG.md entry for version 0.2.0. The previous release is tagged v0.1.0.",
        doc_path="CHANGELOG.md",
        reader="quiz",
        questions=CHANGELOG_QUESTIONS,
        setup="changelog",
    ),
    Task(
        id="rewrite",
        kind="Edit an existing doc",
        prompt="docs/usage.md is out of date and hard to follow. Rewrite it.",
        doc_path="docs/usage.md",
        reader="exec",
        jobs=("add", "check", "env", "use"),
        setup="rewrite",
    ),
]

# Each pattern matches a claim that contradicts facts.md.
INVENTED_PATTERNS = {
    "pypi-install": InventedPattern(
        r"\bpip3?\s+install\s+(?:-U\s+|--upgrade\s+|--user\s+)*pantry(?:-cli)?\b(?![./\\-])",
        "Installs pantry from PyPI, where it isn't published",
    ),
    "invented-command": InventedPattern(
        r"\bpantry\s+(?:remove|delete|rm|edit|search|init|update|clear)\b",
        "Uses a pantry command that doesn't exist",
    ),
    "home-default-file": InventedPattern(
        r"(?:~|\$HOME|%USERPROFILE%)[/\\]\.?(?:config[/\\])?pantry",
        "Says the pantry file lives in the home directory",
        # A line that sets the file on purpose, such as `export PANTRY_FILE=~/pantry.json`, isn't a claim about the default.
        skip_lines=r"PANTRY_FILE\s*=|--file\b",
    ),
    "file-after-command": InventedPattern(
        r"\bpantry\s+(?:add|list|use|expiring)\b[^\n`]*?\s--file\b",
        "Puts --file after the command, which fails",
    ),
    "invented-env-var": InventedPattern(
        r"\bPANTRY_(?!FILE\b)[A-Z_]+\b",
        "Uses an environment variable other than PANTRY_FILE",
    ),
    "invented-distribution": InventedPattern(
        r"\bbrew\s+install\b|\bdocker\s+(?:run|pull)\b|\bpipx\s+install\s+pantry\b",
        "Installs pantry from a package source that doesn't exist",
    ),
}


def _item(name: str, quantity: int, unit: str, expires: date | None) -> dict:
    return {"name": name, "quantity": quantity, "unit": unit, "expires": expires.isoformat() if expires else None}


def _stock(items: list[dict]) -> dict:
    return {"version": 1, "items": items}


def score_job(job: str, value, context) -> dict:
    script = commands_text(value).strip()
    result = {"commands": script, "passed": False, "detail": ""}
    if not script:
        result["detail"] = "no commands given"
        return result
    bad = disallowed_shell(script, EXTRA_COMMANDS)
    if bad:
        result["detail"] = f"not run: uses {bad}, which the sandbox doesn't allow"
        return result

    sandbox = context.sandbox()
    (sandbox.root / "kitchen").mkdir()
    today = context.today
    stock = "kitchen/stock.json"

    if job == "add":
        run = sandbox.run_shell("set -e\n" + script)
        data = sandbox.read_json(stock) or {}
        items = {item.get("name"): item for item in data.get("items", [])}
        milk, eggs = items.get("milk"), items.get("eggs")
        milk_ok = bool(milk) and milk.get("quantity") == 2 \
            and re.fullmatch(r"l|litres?|liters?|ltr", str(milk.get("unit")), re.I) \
            and milk.get("expires") == (today + timedelta(days=10)).isoformat()
        eggs_ok = bool(eggs) and eggs.get("quantity") == 12 and eggs.get("expires") is None
        result["passed"] = bool(milk_ok and eggs_ok)
        result["detail"] = f"exit {run.returncode}; stock={json.dumps(data.get('items'))}; {run.stderr[-300:]}"
        return result

    if job == "check":
        scenarios = {
            "soon": ([_item("milk", 1, "l", today + timedelta(days=2))], True),
            "fine": ([_item("rice", 1, "kg", today + timedelta(days=30)), _item("salt", 1, "item", None)], False),
            "expired": ([_item("cheese", 1, "item", today - timedelta(days=1))], True),
        }
        outcomes = {}
        for name, (items, should_fail) in scenarios.items():
            sandbox.write_json(stock, _stock(items))
            run = sandbox.run_shell(script)
            outcomes[name] = {"exit": run.returncode, "ok": (run.returncode != 0) == should_fail}
        result["passed"] = all(o["ok"] for o in outcomes.values())
        result["detail"] = json.dumps(outcomes)
        return result

    if job == "env":
        sandbox.write_json(stock, _stock([_item("green tea", 40, "bag", None)]))
        run = sandbox.run_shell(script + "\npantry list")
        result["passed"] = run.returncode == 0 and "green tea" in run.stdout
        result["detail"] = f"exit {run.returncode}; {(run.stdout + run.stderr)[-300:]}"
        return result

    if job == "use":
        sandbox.write_json(stock, _stock([_item("eggs", 12, "item", None), _item("milk", 2, "l", None)]))
        run = sandbox.run_shell("set -e\n" + script)
        names = {item.get("name"): item for item in (sandbox.read_json(stock) or {}).get("items", [])}
        result["passed"] = "eggs" not in names and names.get("milk", {}).get("quantity") == 2
        result["detail"] = f"exit {run.returncode}; remaining={sorted(names)}; {run.stderr[-300:]}"
        return result

    raise ValueError(f"unknown job {job}")


def build(project_dir: Path) -> Project:
    return Project(
        id="pantry",
        dir=project_dir,
        description="a small command-line tool called pantry",
        tasks={task.id: task for task in TASKS},
        invented_patterns=INVENTED_PATTERNS,
        clone_name="pantry",
        install_check="pantry --version",
        install_check_output="pantry",
        exec_prompt=EXEC_PROMPT,
        exec_prompt_values=lambda today: {
            "today": today.isoformat(),
            "milk_date": (today + timedelta(days=10)).isoformat(),
        },
        score_job=score_job,
        writer_allowed=["Bash(python -m pantry:*)", "Bash(python -m unittest:*)"],
        previous_tag="v0.1.0",
        clear_env=("PANTRY_FILE",),
        extra_commands=EXTRA_COMMANDS,
        workspace_ignores=("pantry.json", "pantry.json.tmp"),
    )
