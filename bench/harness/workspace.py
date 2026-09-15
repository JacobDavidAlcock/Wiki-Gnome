"""Builds throwaway project folders for writing sessions."""

import os
import shutil
import stat
import subprocess
from pathlib import Path

from . import FIXTURES_DIR
from .tasks import Condition, Task

IGNORED_NAMES = {"__pycache__", "build", ".pytest_cache"}
GIT_EXCLUDES = ".claude/\n__pycache__/\n*.egg-info/\nbuild/\npantry.json\npantry.json.tmp\n"


def remove_tree(path: Path) -> None:
    # Git marks object files read-only, which stops rmtree on Windows.
    def make_writable(func, target, _exc):
        os.chmod(target, stat.S_IWRITE)
        func(target)

    if path.exists():
        shutil.rmtree(path, onerror=make_writable)


def copy_tree_lf(src: Path, dst: Path) -> None:
    """Copy a fixture with LF line endings, so diffs don't depend on the host's git settings."""
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        if any(part in IGNORED_NAMES or part.endswith(".egg-info") for part in rel.parts):
            continue
        target = dst / rel
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            data = path.read_bytes()
            target.write_bytes(data.replace(b"\r\n", b"\n") if _is_text(path) else data)


def _is_text(path: Path) -> bool:
    return path.suffix in {".py", ".md", ".toml", ".json", ".txt", ""}


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "user.name=Pantry Maintainer", "-c", "user.email=maintainer@example.com", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def _clear_except_git(path: Path) -> None:
    for child in path.iterdir():
        if child.name != ".git":
            remove_tree(child) if child.is_dir() else child.unlink()


def create_workspace(path: Path, task: Task, condition: Condition) -> None:
    remove_tree(path)
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    git(path, "config", "core.autocrlf", "false")
    (path / ".git" / "info").mkdir(parents=True, exist_ok=True)
    (path / ".git" / "info" / "exclude").write_text(GIT_EXCLUDES, encoding="utf-8")

    if task.id == "changelog":
        copy_tree_lf(FIXTURES_DIR / "pantry-0.1.0", path)
        git(path, "add", "-A")
        git(path, "commit", "-q", "-m", "Release 0.1.0")
        git(path, "tag", "v0.1.0")
        _clear_except_git(path)
        copy_tree_lf(FIXTURES_DIR / "pantry", path)
        git(path, "add", "-A")
        git(path, "commit", "-q", "-m", "Prepare 0.2.0")
    else:
        copy_tree_lf(FIXTURES_DIR / "pantry", path)
        if task.id == "rewrite":
            docs = path / "docs"
            docs.mkdir()
            docs.joinpath("usage.md").write_bytes(
                (FIXTURES_DIR / "pantry-bad-usage.md").read_bytes().replace(b"\r\n", b"\n")
            )
        git(path, "add", "-A")
        git(path, "commit", "-q", "-m", "Initial commit")

    if condition.skill_dir:
        copy_tree_lf(condition.skill_dir, path / ".claude" / "skills" / condition.skill_dir.name)


def changed_files(path: Path) -> list[str]:
    git(path, "add", "-A")
    return [line for line in git(path, "diff", "--cached", "--name-only", "HEAD").splitlines() if line]


def diff(path: Path) -> str:
    git(path, "add", "-A")
    return git(path, "diff", "--cached", "HEAD")


def original_file(path: Path, rel: str) -> str | None:
    try:
        return git(path, "show", f"HEAD:{rel}")
    except RuntimeError:
        return None
