"""Runs reader-written shell commands and Python scripts in throwaway folders.

These limits reduce risk; they are not a security boundary. See bench/README.md.
"""

import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .model import Project
from .workspace import copy_tree_lf, remove_tree

ALLOWED_COMMANDS = {
    "python", "python3", "py", "pip", "pip3", "export", "cd", "mkdir", "echo", "test", "[", "exit",
    "true", "false", "ls", "cat", "unset", "set", "!", "if", "then", "else", "fi", "env",
}

# pip may only install from local paths. These options would let it reach a package index or URL.
REMOTE_PIP = re.compile(r"--index-url|--extra-index-url|(?:^|\s)-i\s|--find-links|(?:^|\s)-f\s|git\+|https?://")

# Reader-written Python may import only these modules, plus the project's own package.
ALLOWED_IMPORTS = {"json", "pathlib", "decimal", "datetime", "fractions", "dataclasses", "typing", "collections"}
# Reading an exception's class name is a normal thing to do; other dunder attributes can escape the sandbox.
SAFE_DUNDERS = {"__name__", "__qualname__", "__class__"}
BLOCKED_NAMES = {"eval", "exec", "compile", "open", "input", "__import__", "globals", "locals", "vars", "breakpoint",
                 "getattr", "setattr", "delattr"}


def disallowed_shell(script: str, extra_commands: set[str] = frozenset()) -> str | None:
    """Return why a shell script can't run, or None if every command is on the allowlist."""
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
        if words and words[0] not in ALLOWED_COMMANDS | extra_commands and not words[0].startswith(("#", ">", "<", "2>")):
            return f"'{words[0]}'"
    return None


def disallowed_python(code: str, package: str) -> str | None:
    """Return why a Python script can't run, or None if it only uses allowed imports and names."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f"a syntax error ({exc.msg})"
    allowed = ALLOWED_IMPORTS | {package}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in allowed:
                    return f"import {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in allowed or node.level:
                return f"from {node.module} import"
        elif isinstance(node, ast.Name) and node.id in BLOCKED_NAMES:
            return f"'{node.id}'"
        elif isinstance(node, ast.Attribute) and node.attr.startswith("__") and node.attr not in SAFE_DUNDERS:
            return f"'.{node.attr}'"
    return None


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


def _venv_bin(venv: Path) -> Path:
    return venv / ("Scripts" if os.name == "nt" else "bin")


def offline_pip_env(wheels: Path) -> dict:
    """Stop pip from using PyPI. Build dependencies come from a local folder instead."""
    return {"PIP_NO_INDEX": "1", "PIP_FIND_LINKS": str(wheels)}


def download_build_wheels(wheels: Path) -> Path:
    """Fetch the only packages the projects need to build, once, before any reader command runs."""
    if (wheels / "ready").exists():
        return wheels
    wheels.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "pip", "download", "-q", "-d", str(wheels), "setuptools>=61", "wheel"],
                   check=True, capture_output=True)
    (wheels / "ready").write_text("ok")
    return wheels


def make_venv(path: Path, wheels: Path, install: Path | None = None) -> Path:
    """Create a virtual environment, optionally with a local project installed. Reused once ready."""
    if (path / "ready").exists():
        return path
    remove_tree(path)
    subprocess.run([sys.executable, "-m", "venv", str(path)], check=True, capture_output=True)
    if install:
        python = _venv_bin(path) / ("python.exe" if os.name == "nt" else "python")
        subprocess.run([str(python), "-m", "pip", "install", "-q", str(install)], check=True,
                       capture_output=True, env={**os.environ, **offline_pip_env(wheels)})
    (path / "ready").write_text("ok")
    return path


class Sandbox:
    """A folder holding a fresh copy of the project, where reader code runs with HOME pointed inside it."""

    def __init__(self, root: Path, project: Project, wheels: Path, venv: Path | None = None):
        remove_tree(root)
        root.mkdir(parents=True)
        copy_tree_lf(project.current, root / project.clone_name)
        (root / "home").mkdir()
        shims = root / ".shims"
        shims.mkdir()
        for name, target in (("python3", "python"), ("pip3", "pip"), ("py", "python")):
            (shims / name).write_text(f'#!/bin/sh\nexec {target} "$@"\n', encoding="utf-8")
        self.root = root
        self.project = project
        self.wheels = wheels
        self.venv = venv

    def env(self) -> dict:
        blocked = {"PYTHONPATH", "VIRTUAL_ENV", *self.project.clear_env}
        env = {k: v for k, v in os.environ.items() if k not in blocked}
        env.update({
            "PATH": os.pathsep.join([str(self.root / ".shims"), str(_venv_bin(self.venv)), env.get("PATH", "")]),
            "VIRTUAL_ENV": str(self.venv),
            "HOME": str(self.root / "home"),
            "USERPROFILE": str(self.root / "home"),
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PYTHONIOENCODING": "utf-8",
            **offline_pip_env(self.wheels),
        })
        return env

    def run_shell(self, script: str, timeout: int = 60) -> subprocess.CompletedProcess:
        return self._run([_bash(), "-c", script], timeout)

    def run_python(self, code: str, filename: str = "job.py", timeout: int = 60) -> subprocess.CompletedProcess:
        (self.root / filename).write_text(code, encoding="utf-8")
        python = _venv_bin(self.venv) / ("python.exe" if os.name == "nt" else "python")
        return self._run([str(python), filename], timeout)

    def _run(self, args: list[str], timeout: int) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(args, cwd=self.root, env=self.env(), capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=timeout)
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(args, 124, "", f"timed out after {timeout}s")

    def write_json(self, rel: str, data) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return path

    def read_json(self, rel: str):
        try:
            return json.loads((self.root / rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None


@dataclass
class JobContext:
    """What a project's score_job function needs to run one reader job."""

    project: Project
    root: Path
    wheels: Path
    installed_venv: Path
    today: date

    def sandbox(self) -> Sandbox:
        return Sandbox(self.root, self.project, self.wheels, self.installed_venv)


def commands_text(value) -> str:
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    return str(value or "")
