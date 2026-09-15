"""tally: a Python library that records shared expenses and works out who owes whom.

Readers write Python scripts. Its main traps: amounts are int minor units, members must be added first,
a positive balance means the member is owed, uneven splits use weights, and Ledger.load is a class method.
"""

import re
from pathlib import Path

from harness.model import InventedPattern, Project, Question, Task
from harness.sandbox import disallowed_python

EXEC_PROMPT = """You are a developer who has never used tally. Your only source of information is the documentation below. Don't guess from general knowledge where the documentation answers a question; where it doesn't, make your best attempt.

Your setup:
- You are in an empty working folder.
- The tally repository is already cloned into ./tally.
- A Python virtual environment is already active, so `python` and `pip` use it. Don't create another one.

Write code for each job.

1. "install": the shell commands that install tally so `import tally` works.

Jobs 2 to 6 are each a complete Python script, run on its own with `python job.py` from the working folder. Print exactly what the job asks for and nothing else.

2. "balance": Create a ledger in pounds sterling (GBP) with members Ana, Ben and Cai, added in that order. Ana pays £30.00 for a dinner shared equally by all three. Print Ben's balance as a whole number of pence: negative if Ben owes money, positive if Ben is owed money.
3. "weights": Create a GBP ledger with members Ana, Ben and Cai, added in that order. Ben pays £9.00 for a taxi that only Ana and Cai share, with Ana paying twice as much as Cai. Print Ana's balance, then Cai's balance, in pence, each on its own line, with the same sign rule as job 2.
4. "settle": Create a GBP ledger with members Ana, Ben and Cai, added in that order. Ana pays £60.00 for groceries shared equally by all three. Then Ben pays £15.00 for coffee shared equally by Ben and Cai only. Print the transfers that would settle every debt, in the order tally gives them, one per line in the form SENDER -> RECIPIENT: AMOUNT, with AMOUNT in pence.
5. "save_load": Create a US dollar (USD) ledger with members Dev and Eli. Dev pays $12.34 shared equally by both. Save the ledger to trip.json, load it back from trip.json as a new ledger object, and print Eli's balance from the loaded ledger in cents, with the same sign rule as job 2.
6. "error": Create a GBP ledger whose only member is Ana. Then try to record a £5.00 expense paid by Zoe, who isn't a member. Catch the exception tally raises and print only the name of its class.

Reply with only a JSON object, no other text. Give each script as a single string:
{{"install": ["..."], "balance": "...", "weights": "...", "settle": "...", "save_load": "...", "error": "..."}}

<documentation>
{doc}
</documentation>
"""

EXPECTED_OUTPUT = {
    "balance": ["-1000"],
    "weights": ["-600", "-300"],
    "settle": ["Cai -> Ana: 2750", "Ben -> Ana: 1250"],
    "save_load": ["-617"],
    "error": ["UnknownMember"],
}

DOCSTRING_QUESTIONS = (
    Question(
        "What does `Ledger.add_expense` do when `amount` is `12.5`?",
        {"A": "Treats it as £12.50 and stores 1250", "B": "Rounds it to 13", "C": "Raises `InvalidAmount`",
         "D": "Stores it unchanged"},
        "C",
    ),
    Question(
        "When you call `add_expense` without `split_between` or `weights`, who shares the expense?",
        {"A": "Only the payer", "B": "Every current member, including the payer",
         "C": "Every current member except the payer", "D": "Every member, including members added later"},
        "B",
    ),
    Question(
        "What does a positive value from `Ledger.balance` mean?",
        {"A": "The member owes money", "B": "The member is owed money", "C": "The member has settled up",
         "D": "Balances are never positive"},
        "B",
    ),
    Question(
        "When an expense doesn't divide exactly, where do the leftover minor units go?",
        {"A": "To the payer", "B": "One each to participants, in the order they were added to the ledger",
         "C": "They are dropped", "D": "To the participant with the largest share"},
        "B",
    ),
    Question(
        "Does `Ledger.settle_up` change the ledger?",
        {"A": "Yes, it records a payment for each transfer", "B": "No, it only returns the transfers",
         "C": "Yes, it resets every balance to 0", "D": "Only when called with `apply=True`"},
        "B",
    ),
    Question(
        "What happens if you pass both `split_between` and `weights` to `add_expense`?",
        {"A": "`weights` wins", "B": "`split_between` wins", "C": "It raises `TallyError`",
         "D": "The shares are averaged"},
        "C",
    ),
    Question(
        "What does `Ledger.remove_member` do for a member whose balance isn't 0?",
        {"A": "Removes them and splits their balance between the others", "B": "Raises `UnsettledBalance`",
         "C": "Sets their balance to 0 and removes them", "D": "Removes them and keeps their balance in history"},
        "B",
    ),
    Question(
        "What does `Ledger.load` do with a file saved by tally 1?",
        {"A": "Loads it normally", "B": "Converts it and saves it in the new format",
         "C": "Raises `UnsupportedFormat`", "D": "Returns an empty ledger"},
        "C",
    ),
    Question(
        "What happens when `add_expense` names a payer who hasn't been added with `add_member`?",
        {"A": "The payer is added automatically", "B": "It raises `UnknownMember`", "C": "The expense is ignored",
         "D": "It raises `DuplicateMember`"},
        "B",
    ),
)

CHANGELOG_QUESTIONS = (
    Question(
        "How do you record a £12.50 expense in tally 2.0?",
        {"A": '`add_expense("Ana", 12.5)`', "B": '`add_expense("Ana", "12.50")`', "C": '`add_expense("Ana", 1250)`',
         "D": '`add_expense("Ana", Decimal("12.50"))`'},
        "C",
    ),
    Question(
        'In 1.0, `balance("Ben")` returned `5.0` because Ben owed £5.00. What does 2.0 return for the same ledger?',
        {"A": "`5.0`", "B": "`-5.0`", "C": "`500`", "D": "`-500`"},
        "D",
    ),
    Question(
        "What does `settle_up()` return in 2.0?",
        {"A": "A list of `(from, to, amount)` tuples, as in 1.0",
         "B": "A list of `Transfer` objects with `sender`, `recipient` and `amount`",
         "C": "A dict of balances", "D": "Nothing; it records the payments"},
        "B",
    ),
    Question(
        "You have a file saved by tally 1.0. How do you open it in 2.0?",
        {"A": "`Ledger.load(path)` reads it directly", "B": "Run `tally.upgrade_file(path)` once, then use `Ledger.load(path)`",
         "C": "`tally.load(path)` still works for old files", "D": "It can't be opened"},
        "B",
    ),
    Question(
        "In 1.0, `add_expense` added anyone who wasn't in the ledger yet. What happens in 2.0?",
        {"A": "The same", "B": "It raises `UnknownMember`", "C": "It ignores the unknown name",
         "D": "It prints a warning and adds them"},
        "B",
    ),
    Question(
        "Which argument did 2.0 add for splitting an expense unevenly?",
        {"A": "`weights`", "B": "`ratios`", "C": "`shares`", "D": "`split_by`"},
        "A",
    ),
    Question(
        "What does `Ledger()` with no arguments do in 2.0?",
        {"A": "Creates a GBP ledger, as in 1.0", "B": "Creates a USD ledger",
         "C": "Fails, because the currency is required", "D": "Creates a ledger with no currency"},
        "C",
    ),
)

TASKS = [
    Task(
        id="readme",
        kind="Tutorial and reference",
        prompt="Write a README.md for this project.",
        doc_path="README.md",
        reader="exec",
        jobs=("install", "balance", "weights", "settle", "save_load", "error"),
    ),
    Task(
        id="api-reference",
        kind="Reference",
        prompt="Write API reference documentation for the tally package. Save it as docs/api.md.",
        doc_path="docs/api.md",
        reader="exec",
        jobs=("balance", "weights", "settle", "save_load", "error"),
    ),
    Task(
        id="docstrings",
        kind="Reference (docstrings)",
        prompt="Add docstrings to the public classes and methods in tally/ledger.py.",
        doc_path="tally/ledger.py",
        reader="quiz",
        questions=DOCSTRING_QUESTIONS,
        code_doc=True,
    ),
    Task(
        id="changelog",
        kind="Changelog",
        prompt="Write a CHANGELOG.md entry for version 2.0.0. The previous release is tagged v1.0.0.",
        doc_path="CHANGELOG.md",
        reader="quiz",
        questions=CHANGELOG_QUESTIONS,
        setup="changelog",
    ),
]

# A changelog may describe the 1.0 API correctly, so patterns for old usage skip that task.
OLD_API_OK = ("changelog",)

INVENTED_PATTERNS = {
    "pypi-install": InventedPattern(
        r"\bpip3?\s+install\s+(?:-U\s+|--upgrade\s+|--user\s+)*tally(?:-ledger)?\b(?![./\\-])",
        "Installs tally from PyPI, where it isn't published",
    ),
    "float-amount": InventedPattern(
        r"\b(?:add_expense|record_payment)\([^)\n]*?,\s*\d+\.\d+|\bamount\s*=\s*\d+\.\d+",
        "Passes a decimal amount, which raises InvalidAmount",
        skip_tasks=OLD_API_OK,
    ),
    "module-load": InventedPattern(
        r"\btally\.load\(|from\s+tally\s+import\s+[^\n]*\bload\b",
        "Uses a module-level load function, which was removed in 2.0",
        skip_tasks=OLD_API_OK,
    ),
    "old-api": InventedPattern(
        r"\.add_person\(|\bUnknownPerson\b|\bledger\.people\b",
        "Uses a tally 1 name that no longer exists",
        skip_tasks=OLD_API_OK,
    ),
    "tuple-transfers": InventedPattern(
        r"for\s+\(?\s*\w+\s*,\s*\w+\s*,\s*\w+\s*\)?\s+in\s+[\w.]*settle_up\(",
        "Unpacks settle_up() results as tuples, but they are Transfer objects",
        skip_tasks=OLD_API_OK,
    ),
    "invented-method": InventedPattern(
        r"\bLedger\.(?:from_file|open|read|from_json)\(|\bledger\.(?:settle|pay|split)\(",
        "Uses a Ledger method that doesn't exist",
    ),
    "invented-cli": InventedPattern(
        r"(?m)^\s*\$?\s*tally\s+(?:add|list|balance|settle|init|new)\b",
        "Uses a tally command-line tool, which doesn't exist",
    ),
}


def _lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]


def score_job(job: str, value, context) -> dict:
    code = str(value or "").strip()
    result = {"code": code, "passed": False, "detail": ""}
    if not code:
        result["detail"] = "no script given"
        return result
    bad = disallowed_python(code, "tally")
    if bad:
        result["detail"] = f"not run: uses {bad}, which the sandbox doesn't allow"
        return result
    sandbox = context.sandbox()
    run = sandbox.run_python(code)
    got = _lines(run.stdout)
    expected = EXPECTED_OUTPUT[job]
    result["passed"] = run.returncode == 0 and got == expected
    result["detail"] = f"exit {run.returncode}; printed {got!r}; expected {expected!r}; {run.stderr[-300:]}"
    return result


def build(project_dir: Path) -> Project:
    return Project(
        id="tally",
        dir=project_dir,
        description="a small Python library called tally",
        tasks={task.id: task for task in TASKS},
        invented_patterns=INVENTED_PATTERNS,
        clone_name="tally",
        # The sandbox holds a ./tally folder, which `import tally` could pick up as a namespace package.
        # Only an installed tally has __version__.
        install_check='python -c "import tally; print(tally.__version__)"',
        install_check_output="2.0.0",
        exec_prompt=EXEC_PROMPT,
        exec_prompt_values=lambda today: {},
        score_job=score_job,
        writer_allowed=["Bash(python:*)"],
        previous_tag="v1.0.0",
        workspace_ignores=("*.json",),
    )
