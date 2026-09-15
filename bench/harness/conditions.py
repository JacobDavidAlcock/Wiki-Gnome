"""The conditions each task runs under, and fingerprints that identify their prompt or skill version."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from . import BASELINES_DIR, PROMPT_FILE, SKILL_DIR

# Loading the skill by instruction tests its content separately from whether the model chooses to load it.
FORCE_SKILL_PREFIX = f"Use the Skill tool to load the {SKILL_DIR.name} skill first.\n\n"


@dataclass(frozen=True)
class Condition:
    id: str
    description: str
    append_system_prompt: str | None = None
    skill_dir: Path | None = None
    prompt_prefix: str = ""


def fingerprint(condition: Condition) -> str | None:
    """A short hash of what the condition adds, so runs can be matched to prompt and skill versions."""
    if condition.append_system_prompt:
        content = condition.append_system_prompt.encode("utf-8")
    elif condition.skill_dir:
        content = condition.prompt_prefix.encode("utf-8") + (condition.skill_dir / "SKILL.md").read_bytes()
    else:
        return None
    return hashlib.sha256(content).hexdigest()[:12]


def _versioned(version: str, prompt_file: Path, skill_dir: Path) -> list[Condition]:
    suffix = f"-{version}" if version else ""
    label = f", {version}" if version else ""
    return [
        Condition(f"prompt{suffix}", f"Wiki-Gnome prompt.md{label}",
                  append_system_prompt=prompt_file.read_text(encoding="utf-8")),
        Condition(f"skill{suffix}", f"Wiki-Gnome skill{label}", skill_dir=skill_dir),
        Condition(f"skill-forced{suffix}", f"Wiki-Gnome skill{label}, loaded by instruction",
                  skill_dir=skill_dir, prompt_prefix=FORCE_SKILL_PREFIX),
    ]


def load_conditions() -> dict[str, Condition]:
    conditions = [
        Condition("none", "No guidance"),
        Condition("oneline", "One-line prompt",
                  append_system_prompt="When you write documentation, write clear docs like Stripe's."),
        *_versioned("", PROMPT_FILE, SKILL_DIR),
    ]
    for version_dir in sorted(p for p in BASELINES_DIR.glob("*") if p.is_dir()):
        conditions += _versioned(version_dir.name, version_dir / "prompt.md", version_dir / SKILL_DIR.name)
    return {condition.id: condition for condition in conditions}


def baseline_names() -> dict[str, str]:
    """Map each baseline condition's fingerprint to its versioned name, such as prompt-v4."""
    names = {}
    for condition in load_conditions().values():
        if condition.id[-1].isdigit():
            names.setdefault(fingerprint(condition), condition.id)
    return names
