"""Reader tests: a fresh session gets only the doc, and its answers are checked for real."""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

from . import FIXTURES_DIR
from .claude import parse_json_answer, run_claude
from .tasks import Task
from .workspace import copy_tree_lf, remove_tree

ALLOWED_COMMANDS = {
    "pantry", "python", "python3", "py", "pip", "pip3", "export", "cd", "mkdir", "echo", "test", "[", "exit",
    "true", "false", "ls", "cat", "unset", "set", "!", "if", "then", "else", "fi", "env",
}

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

QUIZ_PROMPT = """Answer each question using only the documentation below. If the documentation doesn't answer a question, choose E. Don't use general knowledge or guess.

{questions}

Reply with only a JSON object mapping each question number to a letter, for example {{"1": "A", "2": "E"}}.

<documentation>
{doc}
</documentation>
"""


def run_reader(task: Task, doc: str, *, model: str, out_dir: Path, sandbox_root: Path, venvs_dir: Path) -> dict:
    today = date.today()
    if task.reader == "quiz":
        return _run_quiz(task, doc, model=model, out_dir=out_dir, cwd=sandbox_root)
    prompt = EXEC_PROMPT.format(today=today.isoformat(), milk_date=(today + timedelta(days=10)).isoformat(), doc=doc)
    sandbox_root.mkdir(parents=True, exist_ok=True)
    session = run_claude(prompt, cwd=sandbox_root, model=model, transcript=out_dir / "reader-transcript.jsonl", tools=[])
    answer = parse_json_answer(session.result) or {}
    (out_dir / "reader-answer.json").write_text(json.dumps(answer, indent=2), encoding="utf-8")
    steps = {
        step: execute_step(step, answer.get(step), sandbox_root / step, today, venvs_dir)
        for step in task.exec_steps
    }
    passed = sum(1 for result in steps.values() if result["passed"])
    return {
        "type": "exec",
        "session": session.to_json(),
        "answer_parsed": bool(answer),
        "steps": steps,
        "passed": passed,
        "total": len(task.exec_steps),
        "score": passed / len(task.exec_steps),
    }


def _run_quiz(task: Task, doc: str, *, model: str, out_dir: Path, cwd: Path) -> dict:
    lines = []
    for number, question in enumerate(task.questions, start=1):
        lines.append(f"{number}. {question.text}")
        lines += [f"   {letter}. {option}" for letter, option in question.options.items()]
        lines.append("   E. The documentation doesn't say")
    prompt = QUIZ_PROMPT.format(questions="\n".join(lines), doc=doc)
    cwd.mkdir(parents=True, exist_ok=True)
    session = run_claude(prompt, cwd=cwd, model=model, transcript=out_dir / "reader-transcript.jsonl", tools=[])
    answer = parse_json_answer(session.result) or {}
    (out_dir / "reader-answer.json").write_text(json.dumps(answer, indent=2), encoding="utf-8")
    results = {}
    for number, question in enumerate(task.questions, start=1):
        given = str(answer.get(str(number), "")).strip().upper()[:1]
        results[str(number)] = {"given": given, "expected": question.answer, "passed": given == question.answer}
    passed = sum(1 for r in results.values() if r["passed"])
    return {
        "type": "quiz",
        "session": session.to_json(),
        "answer_parsed": bool(answer),
        "questions": results,
        "passed": passed,
        "total": len(task.questions),
        "score": passed / len(task.questions),
        "said_not_documented": sum(1 for r in results.values() if r["given"] == "E"),
    }


# ---------------------------------------------------------------------------
# Running the reader's commands


def _bash() -> str:
    if os.name == "nt":
        # Skip C:\Windows\System32\bash.exe, which is WSL, and find the bash that ships with Git.
        git = shutil.which("git")
        for parent in Path(git).resolve().parents if git else []:
            for candidate in (parent / "bin" / "bash.exe", parent / "usr" / "bin" / "bash.exe"):
                if candidate.exists():
                    return str(candidate)
        raise RuntimeError("Git Bash is required on Windows to run reader commands.")
    return "/bin/bash"


# pip may only install from local paths. These options would let it reach a package index or URL.
REMOTE_PIP = re.compile(r"--index-url|--extra-index-url|(?:^|\s)-i\s|--find-links|(?:^|\s)-f\s|git\+|https?://")


def disallowed_command(script: str) -> str | None:
    """Return why the script can't run: a command word that isn't allowed, or a remote pip source."""
    if REMOTE_PIP.search(script):
        return "a remote package source"
    for segment in re.split(r"&&|\|\||;|\||\n|\$\(|`", script):
        segment = segment.strip().lstrip("(").strip()
        if not segment:
            continue
        try:
            words = shlex.split(segment, posix=True)
        except ValueError:
            words = segment.split()
        while words and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]):
            words = words[1:]
        if words and words[0] not in ALLOWED_COMMANDS and not words[0].startswith(("#", ">", "<", "2>")):
            return f"'{words[0]}'"
    return None


class Sandbox:
    def __init__(self, root: Path, wheels: Path, venv: Path | None = None):
        remove_tree(root)
        root.mkdir(parents=True)
        copy_tree_lf(FIXTURES_DIR / "pantry", root / "pantry")
        (root / "kitchen").mkdir()
        (root / "home").mkdir()
        self.root = root
        self.wheels = wheels
        self.venv = venv
        shims = root / ".shims"
        shims.mkdir()
        for name, target in (("python3", "python"), ("pip3", "pip"), ("py", "python")):
            (shims / name).write_text(f'#!/bin/sh\nexec {target} "$@"\n', encoding="utf-8")

    @property
    def stock(self) -> Path:
        return self.root / "kitchen" / "stock.json"

    def write_stock(self, items: list[dict]) -> None:
        self.stock.write_text(json.dumps({"version": 1, "items": items}, indent=2), encoding="utf-8")

    def read_stock(self) -> dict | None:
        try:
            return json.loads(self.stock.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def run(self, script: str, timeout: int = 60) -> subprocess.CompletedProcess:
        bin_dir = self.venv / ("Scripts" if os.name == "nt" else "bin")
        env = {k: v for k, v in os.environ.items() if k not in {"PANTRY_FILE", "PYTHONPATH", "VIRTUAL_ENV"}}
        env.update({
            "PATH": os.pathsep.join([str(self.root / ".shims"), str(bin_dir), env.get("PATH", "")]),
            "VIRTUAL_ENV": str(self.venv),
            "HOME": str(self.root / "home"),
            "USERPROFILE": str(self.root / "home"),
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            **offline_pip_env(self.wheels),
        })
        try:
            return subprocess.run(
                [_bash(), "-c", script], cwd=self.root, env=env, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(script, 124, "", f"timed out after {timeout}s")


def offline_pip_env(wheels: Path) -> dict:
    """Stop pip from using PyPI. Build dependencies come from a local folder instead."""
    return {"PIP_NO_INDEX": "1", "PIP_FIND_LINKS": str(wheels)}


def download_build_wheels(wheels: Path) -> Path:
    """Fetch the only packages pantry needs to build, once, before any reader command runs."""
    if (wheels / "ready").exists():
        return wheels
    wheels.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "pip", "download", "-q", "-d", str(wheels), "setuptools>=61", "wheel"],
                   check=True, capture_output=True)
    (wheels / "ready").write_text("ok")
    return wheels


def make_venv(path: Path, install_pantry: bool, wheels: Path) -> Path:
    if (path / "ready").exists():
        return path
    remove_tree(path)
    subprocess.run([sys.executable, "-m", "venv", str(path)], check=True, capture_output=True)
    if install_pantry:
        python = path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run([str(python), "-m", "pip", "install", "-q", str(FIXTURES_DIR / "pantry")], check=True,
                       capture_output=True, env={**os.environ, **offline_pip_env(wheels)})
    (path / "ready").write_text("ok")
    return path


def _commands(value) -> str:
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value or "")


def _item(name: str, quantity: int, unit: str, expires: date | None) -> dict:
    return {"name": name, "quantity": quantity, "unit": unit, "expires": expires.isoformat() if expires else None}


def execute_step(step: str, value, root: Path, today: date, venvs_dir: Path) -> dict:
    script = _commands(value).strip()
    result = {"commands": script, "passed": False, "detail": ""}
    if not script:
        result["detail"] = "no commands given"
        return result
    bad = disallowed_command(script)
    if bad:
        result["detail"] = f"not run: uses {bad}, which the sandbox doesn't allow"
        return result

    wheels = venvs_dir / "wheels"
    if step == "install":
        sandbox = Sandbox(root, wheels)
        sandbox.venv = make_venv(root / ".venv", install_pantry=False, wheels=wheels)
        run = sandbox.run(script, timeout=300)
        check = sandbox.run("pantry --version")
        result["passed"] = check.returncode == 0 and "pantry" in check.stdout
        result["detail"] = (run.stderr or run.stdout)[-500:] if not result["passed"] else check.stdout.strip()
        return result

    sandbox = Sandbox(root, wheels, make_venv(venvs_dir / "installed", install_pantry=True, wheels=wheels))

    if step == "add":
        run = sandbox.run("set -e\n" + script)
        data = sandbox.read_stock() or {}
        items = {item.get("name"): item for item in data.get("items", [])}
        milk, eggs = items.get("milk"), items.get("eggs")
        milk_ok = bool(milk) and milk.get("quantity") == 2 and re.fullmatch(r"l|litres?|liters?|ltr", str(milk.get("unit")), re.I) \
            and milk.get("expires") == (today + timedelta(days=10)).isoformat()
        eggs_ok = bool(eggs) and eggs.get("quantity") == 12 and eggs.get("expires") is None
        result["passed"] = bool(milk_ok and eggs_ok)
        result["detail"] = f"exit {run.returncode}; stock={json.dumps(data.get('items'))}; {run.stderr[-300:]}"
        return result

    if step == "check":
        scenarios = {
            "soon": ([_item("milk", 1, "l", today + timedelta(days=2))], True),
            "fine": ([_item("rice", 1, "kg", today + timedelta(days=30)), _item("salt", 1, "item", None)], False),
            "expired": ([_item("cheese", 1, "item", today - timedelta(days=1))], True),
        }
        outcomes = {}
        for name, (items, should_fail) in scenarios.items():
            sandbox.write_stock(items)
            run = sandbox.run(script)
            outcomes[name] = {"exit": run.returncode, "ok": (run.returncode != 0) == should_fail}
        result["passed"] = all(o["ok"] for o in outcomes.values())
        result["detail"] = json.dumps(outcomes)
        return result

    if step == "env":
        sandbox.write_stock([_item("green tea", 40, "bag", None)])
        run = sandbox.run(script + "\npantry list")
        result["passed"] = run.returncode == 0 and "green tea" in run.stdout
        result["detail"] = f"exit {run.returncode}; {(run.stdout + run.stderr)[-300:]}"
        return result

    if step == "use":
        sandbox.write_stock([_item("eggs", 12, "item", None), _item("milk", 2, "l", None)])
        run = sandbox.run("set -e\n" + script)
        names = {item.get("name"): item for item in (sandbox.read_stock() or {}).get("items", [])}
        result["passed"] = "eggs" not in names and names.get("milk", {}).get("quantity") == 2
        result["detail"] = f"exit {run.returncode}; remaining={sorted(names)}; {run.stderr[-300:]}"
        return result

    raise ValueError(f"unknown step {step}")
