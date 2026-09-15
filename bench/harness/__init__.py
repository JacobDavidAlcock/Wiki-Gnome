from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BENCH_DIR.parent
FIXTURES_DIR = BENCH_DIR / "fixtures"
SKILL_DIR = REPO_DIR / ".claude" / "skills" / "technical-docs-style"
PROMPT_FILE = REPO_DIR / "prompt.md"
# Earlier versions of the prompt and skill, kept so new versions can be measured against them.
BASELINES_DIR = BENCH_DIR / "baselines"
