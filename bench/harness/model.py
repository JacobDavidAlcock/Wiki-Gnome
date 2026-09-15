"""Data types shared by the harness and the test projects."""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Callable


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
    reader: str  # "exec": the reader writes code that the harness runs. "quiz": the reader answers questions.
    jobs: tuple[str, ...] = ()
    questions: tuple[Question, ...] = ()
    # "current": the current release only. "changelog": the previous release is committed and tagged first.
    # "rewrite": the project's bad doc is committed at doc_path, for the writer to rewrite.
    setup: str = "current"
    # True when the doc is source code, such as docstrings. The reader then sees signatures and docstrings only.
    code_doc: bool = False


@dataclass(frozen=True)
class InventedPattern:
    pattern: str
    description: str
    # Lines matching this regex are skipped, for example a line that sets a value on purpose.
    skip_lines: str | None = None
    # Tasks where the pattern doesn't apply, such as a changelog that correctly describes an old API.
    skip_tasks: tuple[str, ...] = ()


@dataclass
class Project:
    id: str
    dir: Path
    # How the judge refers to the project, e.g. "a small command-line tool called pantry".
    description: str
    tasks: dict[str, Task]
    invented_patterns: dict[str, InventedPattern]
    # Folder name of the project inside a reader's sandbox, e.g. "pantry" for ./pantry.
    clone_name: str
    # Shell command that succeeds once the project is installed, and text its output must contain.
    install_check: str
    install_check_output: str
    # Reader prompt for exec tasks. Formatted with {doc} plus the values from exec_prompt_values(today).
    exec_prompt: str
    exec_prompt_values: Callable[[date], dict[str, str]]
    # Scores one non-install job: (job id, reader's answer for it, JobContext) -> result dict with "passed".
    score_job: Callable[[str, Any, Any], dict]
    writer_allowed: list[str] = field(default_factory=list)
    writer_disallowed: list[str] = field(default_factory=list)
    previous_tag: str | None = None
    # Environment variables to clear before running reader code, so the host's settings can't leak in.
    clear_env: tuple[str, ...] = ()
    # Shell commands readers may run on top of the sandbox allowlist, such as the project's own CLI.
    extra_commands: frozenset[str] = frozenset()
    # Files a writer might create while trying the project out, kept out of the diff.
    workspace_ignores: tuple[str, ...] = ()

    @property
    def current(self) -> Path:
        return self.dir / "current"

    @property
    def previous(self) -> Path:
        return self.dir / "previous"

    @property
    def facts_file(self) -> Path:
        return self.dir / "facts.md"

    @property
    def bad_doc(self) -> Path:
        return self.dir / "bad-doc.md"
