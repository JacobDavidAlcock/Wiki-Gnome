"""Benchmark tasks, conditions and reader questions."""

from dataclasses import dataclass, field
from pathlib import Path

from . import BASELINES_DIR, PROMPT_FILE, SKILL_DIR

EXEC_STEPS = ("install", "add", "check", "env", "use")


@dataclass(frozen=True)
class Condition:
    id: str
    description: str
    append_system_prompt: str | None = None
    skill_dir: Path | None = None


def load_conditions() -> dict[str, Condition]:
    conditions = [
        Condition("none", "No guidance"),
        Condition(
            "oneline",
            "One-line prompt",
            append_system_prompt="When you write documentation, write clear docs like Stripe's.",
        ),
        Condition(
            "prompt",
            "Wiki-Gnome prompt.md",
            append_system_prompt=PROMPT_FILE.read_text(encoding="utf-8"),
        ),
        Condition("skill", "Wiki-Gnome skill", skill_dir=SKILL_DIR),
    ]
    for version_dir in sorted(p for p in BASELINES_DIR.glob("*") if p.is_dir()):
        version = version_dir.name
        conditions.append(Condition(
            f"prompt-{version}",
            f"Wiki-Gnome prompt.md, {version}",
            append_system_prompt=(version_dir / "prompt.md").read_text(encoding="utf-8"),
        ))
        conditions.append(Condition(
            f"skill-{version}", f"Wiki-Gnome skill, {version}", skill_dir=version_dir / SKILL_DIR.name,
        ))
    return {condition.id: condition for condition in conditions}


@dataclass(frozen=True)
class Question:
    text: str
    options: dict[str, str]
    answer: str


@dataclass(frozen=True)
class Task:
    id: str
    kind: str
    prompt: str
    doc_path: str
    reader: str  # "exec" or "quiz"
    exec_steps: tuple[str, ...] = ()
    questions: tuple[Question, ...] = field(default_factory=tuple)


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

TASKS = {
    task.id: task
    for task in [
        Task(
            id="readme",
            kind="Tutorial and reference",
            prompt="Write a README.md for this project.",
            doc_path="README.md",
            reader="exec",
            exec_steps=EXEC_STEPS,
        ),
        Task(
            id="cli-reference",
            kind="Reference",
            prompt="Write reference documentation for the pantry command-line interface. Save it as docs/cli.md.",
            doc_path="docs/cli.md",
            reader="exec",
            exec_steps=("add", "check", "env", "use"),
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
            exec_steps=("check",),
        ),
        Task(
            id="docstrings",
            kind="Reference (docstrings)",
            prompt="Add docstrings to the functions in pantry/store.py.",
            doc_path="pantry/store.py",
            reader="quiz",
            questions=DOCSTRING_QUESTIONS,
        ),
        Task(
            id="changelog",
            kind="Changelog",
            prompt="Write a CHANGELOG.md entry for version 0.2.0. The previous release is tagged v0.1.0.",
            doc_path="CHANGELOG.md",
            reader="quiz",
            questions=CHANGELOG_QUESTIONS,
        ),
        Task(
            id="rewrite",
            kind="Edit an existing doc",
            prompt="docs/usage.md is out of date and hard to follow. Rewrite it.",
            doc_path="docs/usage.md",
            reader="exec",
            exec_steps=("add", "check", "env", "use"),
        ),
    ]
}
