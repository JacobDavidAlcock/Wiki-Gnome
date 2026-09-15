"""Deterministic checks: invented facts, broken code and style metrics."""

import ast
import re
import subprocess
import sys
from pathlib import Path

from . import workspace
from .tasks import Task

# Each pattern matches a claim that contradicts bench/fixtures/pantry-facts.md.
INVENTED_PATTERNS = {
    "pypi-install": (
        r"\bpip3?\s+install\s+(?:-U\s+|--upgrade\s+|--user\s+)*pantry(?:-cli)?\b(?![./\\-])",
        "Installs pantry from PyPI, where it isn't published",
    ),
    "invented-command": (
        r"\bpantry\s+(?:remove|delete|rm|edit|search|init|update|clear)\b",
        "Uses a pantry command that doesn't exist",
    ),
    "home-default-file": (
        r"(?:~|\$HOME|%USERPROFILE%)[/\\]\.?(?:config[/\\])?pantry",
        "Says the pantry file lives in the home directory",
    ),
    "file-after-command": (
        r"\bpantry\s+(?:add|list|use|expiring)\b[^\n`]*?\s--file\b",
        "Puts --file after the command, which fails",
    ),
    "invented-env-var": (
        r"\bPANTRY_(?!FILE\b)[A-Z_]+\b",
        "Uses an environment variable other than PANTRY_FILE",
    ),
    "invented-distribution": (
        r"\bbrew\s+install\b|\bdocker\s+(?:run|pull)\b|\bpipx\s+install\s+pantry\b",
        "Installs pantry from a package source that doesn't exist",
    ),
}

BANNED_WORDS = [
    "simply", "just", "obviously", "of course", "easily", "powerful", "seamless", "seamlessly",
    "best-in-class", "blazing fast", "please note", "it should be noted",
]
FILLER_HEADINGS = re.compile(r"^#{1,6}\s*(introduction|overview|conclusion|summary|welcome)\b", re.IGNORECASE | re.MULTILINE)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


# A line that sets the file on purpose, such as `export PANTRY_FILE=~/pantry.json`, isn't a claim about the default.
CHOSEN_FILE_LINE = re.compile(r"PANTRY_FILE\s*=|--file\b")


def invented_facts(text: str) -> list[dict]:
    found = []
    for check_id, (pattern, description) in INVENTED_PATTERNS.items():
        lines = text.splitlines()
        if check_id == "home-default-file":
            lines = [line for line in lines if not CHOSEN_FILE_LINE.search(line)]
        matches = sorted({m.group(0).strip() for m in re.finditer(pattern, "\n".join(lines), re.IGNORECASE)})
        if matches:
            found.append({"id": check_id, "description": description, "matches": matches[:5]})
    return found


def prose_only(text: str) -> str:
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"^(?: {4}|\t).*$", " ", text, flags=re.MULTILINE)
    return re.sub(r"`[^`\n]*`", "CODE", text)


def style_metrics(text: str) -> dict:
    prose = prose_only(text)
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", prose)
    lowered = prose.lower()
    sentences = [s for s in re.split(r"(?<=[.!?])\s+|\n\s*\n|\n[-*\d]", prose) if len(s.split()) >= 3]
    banned = {w: len(re.findall(rf"\b{re.escape(w)}\b", lowered)) for w in BANNED_WORDS}
    return {
        "words": len(words),
        "banned_words": {w: n for w, n in banned.items() if n},
        "banned_per_1000_words": round(1000 * sum(banned.values()) / max(len(words), 1), 2),
        "the_user": len(re.findall(r"\bthe users?\b", lowered)),
        "avg_sentence_words": round(sum(len(s.split()) for s in sentences) / max(len(sentences), 1), 1),
        "filler_headings": len(FILLER_HEADINGS.findall(text)),
        "exclamations": prose.count("!"),
        "emoji": len(EMOJI.findall(text)),
    }


def _strip_docstrings(tree: ast.AST) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return tree


def code_changed(before: str, after: str) -> bool:
    """True when the code differs once docstrings are ignored."""
    try:
        return ast.dump(_strip_docstrings(ast.parse(before))) != ast.dump(_strip_docstrings(ast.parse(after)))
    except SyntaxError:
        return True


def docstring_coverage(source: str) -> dict:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"documented": 0, "total": 0}
    nodes = [n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
    documented = sum(1 for n in nodes if ast.get_docstring(n))
    return {"documented": documented, "total": len(nodes)}


def docstrings_only(source: str) -> str:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ""
    nodes = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
    return "\n\n".join(doc for doc in (ast.get_docstring(n) for n in nodes) if doc)


def docstring_view(source: str) -> str:
    """Signatures and docstrings only, the way a reader sees them in an editor tooltip."""
    tree = ast.parse(source)
    kept = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kept.append(_skeleton(node))
        elif isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant):
            kept.append(node)
    return ast.unparse(ast.Module(body=kept, type_ignores=[]))


def _skeleton(node):
    doc = ast.get_docstring(node, clean=False)
    body = [ast.Expr(ast.Constant(doc))] if doc else []
    if isinstance(node, ast.ClassDef):
        body += [
            _skeleton(n) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) else n
            for n in node.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.AnnAssign))
        ]
        node.decorator_list = []
    node.body = body or [ast.Expr(ast.Constant(...))]
    return node


def workspace_checks(ws: Path) -> dict:
    changed = workspace.changed_files(ws)
    code_edits = []
    for rel in changed:
        if not rel.endswith(".py"):
            continue
        before = workspace.original_file(ws, rel)
        after_path = ws / rel
        if before is None or not after_path.exists() or code_changed(before, after_path.read_text(encoding="utf-8")):
            code_edits.append(rel)
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "-q"], cwd=ws, capture_output=True, text=True, timeout=300,
    )
    return {
        "changed_files": changed,
        "code_edits": code_edits,
        "tests_pass": tests.returncode == 0,
    }


def reader_text(task: Task, ws: Path) -> str | None:
    """The text a reader gets: the doc itself, or the docstrings for the docstring task."""
    path = ws / task.doc_path
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    if task.id == "docstrings":
        try:
            return docstring_view(text)
        except SyntaxError:
            return None
    return text
