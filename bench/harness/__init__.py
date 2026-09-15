from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BENCH_DIR.parent
# One folder per test project. Each holds the project's code and a project.py that defines its tasks.
PROJECTS_DIR = BENCH_DIR / "projects"
SKILL_DIR = REPO_DIR / ".claude" / "skills" / "technical-docs-style"
PROMPT_FILE = REPO_DIR / "prompt.md"
# Earlier versions of the prompt and skill, kept so new versions can be measured against them.
BASELINES_DIR = BENCH_DIR / "baselines"
